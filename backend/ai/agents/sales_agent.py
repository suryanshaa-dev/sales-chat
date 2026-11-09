import json

from dotenv import load_dotenv
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from langchain.agents import create_agent, AgentState
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.tools import tool, ToolRuntime
from langchain.agents.middleware import wrap_model_call
from backend.ai.schemas.sales_agent import (
    ObjectionResponseOutput,
    LeadQualificationResponse,
)
from langgraph.types import Command
from backend.ai.evaluators.objection_evaluator import ObjectionEvaluator
from backend.ai.evaluators.sales_knowledge_evaluator import SalesKnowledgeEvaluator

load_dotenv()


class SalesAgentState(AgentState):
    query_type: str
    selected_model: str
    found_documents: bool
    retrieval_attempted: bool


def serialize_sources(source_results):
    sources = []
    for result in source_results:
        if len(result) == 3:
            document, score, relevance = result
        else:
            document, score = result
            relevance = None
        sources.append(
            {
                "source": document.metadata.get("source"),
                "page": document.metadata.get("page"),
                "relevance_score": score,
                "relevance": relevance,
            }
        )
    return sources


class SalesAgent:
    _sales_agent = None

    _query_type = None

    _available_models = {"gpt-5.4-nano", "gpt-5.4"}

    @staticmethod
    @tool
    def sales_knowledge(query: str, runtime: ToolRuntime[None, SalesAgentState]):
        """
        Search sales knowledge and return documents relevant to the user's query.
        """

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorStore = Chroma(
            embedding_function=embeddings,
            persist_directory="./sales_knowledge_db",
            collection_name="sales_knowledge",
        )

        search_documents = vectorStore.similarity_search_with_relevance_scores(
            query=query, k=5
        )

        

        evaluations = SalesKnowledgeEvaluator.evaluate(
            model=runtime.state.get("selected_model"),
            documents=[document for document, _score in search_documents],
            user_query=query,
        )

        relevant_indexes = {
            evaluation["index"]
            for evaluation in evaluations
            if evaluation["classification"] != "no_match"
        }

        return [
            (document, score)
            for index, (document, score) in enumerate(search_documents)
            if index in relevant_indexes
        ]

    @staticmethod
    @tool
    def get_objection_documents(
        query: str, runtime: ToolRuntime[None, SalesAgentState]
    ):
        """Find the most relevant objection document to answer user's query with their word-for-word scripts."""
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory="./sales_objections_db",
            collection_name="sales_objections",
        )

        results = vector_store.similarity_search_with_relevance_scores(query=query, k=1)
        docs = [doc for doc, score in results]
        content = "No objection document was found."
        classified_results = []

        if len(docs) > 0:

            grader = ObjectionEvaluator.evaluate(
                model=runtime.state.get("selected_model"),
                document=docs[0],
                user_query=query,
            )
            if grader.classification in {"exact_match", "related_match"}:
                classified_results = [(docs[0], results[0][1], grader.classification)]
                content = (
                    f"A relevant objection document was found. Use its content "
                    f"to answer the user.\n"
                    f"Source: {docs[0].metadata.get('source', 'Unknown')}\n"
                    f"Content: {docs[0].page_content}\n"
                    f"Score: {results[0][1]}\n"
                    f"Relevance: {grader.classification}"
                )
            else:
                content = (
                    "The retrieved document was evaluated as no_match. Do not "
                    "use it as a source; tell the user no matching objection "
                    "document was found."
                )

        return Command(
            update={
                "found_documents": bool(classified_results),
                "retrieval_attempted": True,
                "messages": [
                    ToolMessage(
                        content=content,
                        artifact=classified_results,
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
            }
        )

        return content, docs

    @classmethod
    def get_sales_agent(cls):
        """Create the agent once, after the class tool has been defined."""

        if cls._sales_agent is None:
            cls._sales_agent = create_agent(
                model="gpt-5.4-nano",
                state_schema=SalesAgentState,
                tools=[cls.get_objection_documents, cls.sales_knowledge],
                middleware=[SalesAgent.filter_tools],
                system_prompt=(
                    "You are a helpful sales agent. For general queries use my sales knowledge. For objection queries, use "
                    "only a document that retrieval marked exact_match or "
                    "related_match. If retrieval says no_match or no document "
                    "was found, do not invent a script."
                ),
                response_format=None,
            )
        return cls._sales_agent

    @staticmethod
    async def user_query(
        query: str, thread_id: str, query_type: str, selected_model: str,
        conversation_history: list[dict[str, str]] | None = None,
    ):
        if selected_model not in SalesAgent._available_models:
            selected_model = "gpt-5.4-nano"

        agent = SalesAgent.get_sales_agent()
        agent_input = {
            "messages": [
                *[
                    HumanMessage(content=message["content"])
                    if message["role"] == "user"
                    else AIMessage(content=message["content"])
                    for message in (conversation_history or [])
                    if message.get("role") in {"user", "assistant"}
                ],
                HumanMessage(content=query),
            ],
            "query_type": query_type,
            "selected_model": selected_model,
        }

        if query_type == "objection":
            # These flags describe this turn's retrieval, so overwrite any values
            # restored from the thread's checkpoint before starting the turn.
            agent_input["retrieval_attempted"] = False
            agent_input["found_documents"] = False
            # Structured fields are only complete after the agent finishes.
            result = await agent.ainvoke(agent_input)
            result_messages = result.get("messages", [])
            source_results = []
            for message in reversed(result_messages):
                if isinstance(message, HumanMessage):
                    break
                if isinstance(message, ToolMessage):
                    source_results.extend(getattr(message, "artifact", None) or [])
            if source_results:
                sources = serialize_sources(source_results)
                yield {"event": "sources", "data": {"documents": sources}}

            structured_response = result.get("structured_response")
            if hasattr(structured_response, "model_dump"):
                structured_response = structured_response.model_dump()
            if result.get("found_documents") and isinstance(structured_response, dict):
                retrieved_docs = [
                    doc for doc, _score, _classification in source_results
                ]
                heading = ""
                if retrieved_docs:
                    try:
                        document_data = json.loads(retrieved_docs[0].page_content)
                        heading = document_data.get("heading", "")
                    except (json.JSONDecodeError, AttributeError, TypeError):
                        heading = ""
                structured_response["objection_name"] = heading
            elif not result.get("found_documents"):
                final_text = next(
                    (
                        message.content
                        for message in reversed(result_messages)
                        if isinstance(message, AIMessage)
                        and isinstance(message.content, str)
                        and message.content
                    ),
                    "No matching objection document was found.",
                )
                # Preserve the UI payload shape without asking the model to
                # produce or validate an ObjectionResponseOutput.
                structured_response = {
                    "objection_name": "",
                    "script": final_text,
                    "psychology": [],
                }
            yield {"event": "complete", "data": {"response": structured_response}}
            return

        elif query_type == "lead_qualification":

            result = await agent.ainvoke(agent_input)
            result_messages = result.get("messages", [])
            source_results = []
            for message in reversed(result_messages):
                if isinstance(message, HumanMessage):
                    break
                if isinstance(message, ToolMessage):
                    source_results.extend(getattr(message, "artifact", None) or [])
            if source_results:
                yield {
                    "event": "sources",
                    "data": {
                        "documents": serialize_sources(source_results)
                    },
                }
            structured_response = result.get("structured_response")
            if hasattr(structured_response, "model_dump"):
                structured_response = structured_response.model_dump()
            if structured_response is None:
                structured_response = next(
                    (message.content for message in reversed(result_messages)
                     if isinstance(message, AIMessage) and message.content),
                    "",
                )
            yield {"event": "complete", "data": {"response": structured_response}}
            return
        else:
            async for message, _metadata in agent.astream(
                agent_input,
                stream_mode="messages",
            ):
                if isinstance(message, ToolMessage):
                    results = getattr(message, "artifact", None)

                    if results:
                        sources = serialize_sources(results)
                        yield {"event": "sources", "data": {"documents": sources}}

                elif isinstance(message, AIMessage):
                    if isinstance(message.content, str) and message.content:
                        yield {"event": "delta", "data": {"content": message.content}}

    @staticmethod
    @wrap_model_call
    async def filter_tools(request, handler):

        query_type = request.state.get("query_type", "general")
        selected_model_name = request.state.get("selected_model", "gpt-5.4-nano")
        if selected_model_name not in SalesAgent._available_models:
            selected_model_name = "gpt-5.4-nano"
         
        if query_type == "lead_qualification":
            request = request.override(response_format=LeadQualificationResponse)
        elif query_type == "objection":

            retrieval_attempted = request.state.get("retrieval_attempted", False)
            if not retrieval_attempted:
                # The first model call must invoke retrieval. Structured output
                # is applied on the follow-up call after the tool updates state.
                request = request.override(response_format=None)
                request = request.override(
                    tool_choice={
                        "type": "function",
                        "function": {
                            "name": "get_objection_documents",
                        },
                    },
                )
            else:
                # Retrieval is a one-shot step for this turn. Prevent the model
                # from re-entering the tool loop after seeing the evaluation.
                request = request.override(tools=[])
                if request.state.get("found_documents", False):
                    request = request.override(response_format=ObjectionResponseOutput)
                else:
                    request = request.override(response_format=None)

        request = request.override(model=ChatOpenAI(model=selected_model_name))

        return await handler(request)
