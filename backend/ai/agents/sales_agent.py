from dotenv import load_dotenv
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.tools import tool, ToolRuntime
from langchain.agents.middleware import wrap_model_call
from backend.ai.schemas.sales_agent import ObjectionResponseOutput
from langgraph.types import Command
from backend.ai.evaluators.objection_evaluator import ObjectionEvaluator
load_dotenv()


class SalesAgentState(AgentState):
    query_type: str
    selected_model: str
    found_documents: bool
    retrieval_attempted: bool


class SalesAgent:
    checkpointer = InMemorySaver()
    _sales_agent = None

    _query_type = None

    _available_models = {"gpt-5.4-nano", "gpt-5.4"}

    @staticmethod
    @tool
    def get_objection_documents(
        query: str, runtime: ToolRuntime[None, SalesAgentState]
    ):
        """Find relevant objection documents and their word-for-word scripts."""
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory="./sales_objections_db",
            collection_name="sales_objections",
        )

        results = vector_store.similarity_search_with_relevance_scores(query=query, k=1)
        docs = [doc for doc, score in results]
        content = {}

        if len(docs) > 0:

            grader = ObjectionEvaluator.evaluate(
                model=runtime.state.get("selected_model"),
                document=docs[0],
                user_query=query,
            )
            classified_results = [
                (doc, score, grader.classification if index == 0 else None)
                for index, (doc, score) in enumerate(results)
            ]

            content = "\n\n".join(
                f"Source: {doc.metadata.get('source', 'Unknown')}\n"
                f"Content: {doc.page_content}\n"
                f"Score: {score}\n"
                f"Relevance: {classification}"
                for doc, score, classification in classified_results
            )
        else:
            classified_results = []

        return Command(
            update={
                "found_documents": len(docs) > 0,
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
                tools=[cls.get_objection_documents],
                middleware=[SalesAgent.filter_tools],
                system_prompt=(
                    "You are helpfule sales agent."
                ),
                checkpointer=cls.checkpointer,
                response_format=None,
            )
        return cls._sales_agent

    @staticmethod
    async def user_query(
        query: str, thread_id: str, query_type: str, selected_model: str
    ):
        if selected_model not in SalesAgent._available_models:
            selected_model = "gpt-5.4-nano"

        config = {"configurable": {"thread_id": thread_id}}
        agent = SalesAgent.get_sales_agent()
        agent_input = {
            "messages": [HumanMessage(content=query)],
            "query_type": query_type,
            "selected_model": selected_model,
        }

        if query_type == "objection":
            # These flags describe this turn's retrieval, so overwrite any values
            # restored from the thread's checkpoint before starting the turn.
            agent_input["retrieval_attempted"] = False
            agent_input["found_documents"] = False
            # Structured fields are only complete after the agent finishes.
            result = await agent.ainvoke(agent_input, config=config)
            result_messages = result.get("messages", [])
            source_results = []
            for message in reversed(result_messages):
                if isinstance(message, HumanMessage):
                    break
                if isinstance(message, ToolMessage):
                    source_results.extend(getattr(message, "artifact", None) or [])
            if source_results:
                sources = [
                    {
                        "source": doc.metadata.get("source"),
                        "page": doc.metadata.get("page"),
                        "relevance_score": score,
                        "relevance": classification,
                    }
                    for doc, score, classification in source_results
                ]
                yield {"event": "sources", "data": {"documents": sources}}

            structured_response = result.get("structured_response")
            if hasattr(structured_response, "model_dump"):
                structured_response = structured_response.model_dump()
            yield {"event": "complete", "data": {"response": structured_response}}
            return

        async for message, _metadata in agent.astream(
            agent_input,
            config=config,
            stream_mode="messages",
        ):
            if isinstance(message, ToolMessage):
                results = getattr(message, "artifact", None)

                print("tools message below:")
                print(results)

                if results:
                    sources = [
                        {
                            "source": doc.metadata.get("source"),
                            "page": doc.metadata.get("page"),
                            "relevance_score": score,
                            "relevance": classification,
                          
                        }
                        for doc, score, classification in results
                    ]
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

        if query_type == "general":

            request = request.override(tools=[])
        elif query_type == "objection":
          
            retrieval_attempted = request.state.get("retrieval_attempted", False)
            if not retrieval_attempted:

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
                request = request.override(response_format=ObjectionResponseOutput)

        request = request.override(model=ChatOpenAI(model=selected_model_name))

        return await handler(request)
