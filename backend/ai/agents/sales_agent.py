from dotenv import load_dotenv
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.tools import tool
from langchain.agents.middleware import wrap_model_call
from backend.ai.schemas.sales_agent import ObjectionResponseOutput

load_dotenv()

class SalesAgentState(AgentState):
    query_type: str
    selected_model: str


class SalesAgent:
    checkpointer = InMemorySaver()
    _sales_agent = None

    _query_type = None

    _available_models = {"gpt-5.4-nano", "gpt-5.4"}

    @staticmethod
    @tool(response_format="content_and_artifact")
    def get_objection_documents(query: str):
        """Find relevant objection documents and their word-for-word scripts."""
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory="./sales_objections_db",
            collection_name="sales_objections",
        )

        results=  vector_store.similarity_search_with_relevance_scores(query=query, k=1)
        docs = [doc for doc, score in results]
        content = {}

        if(len(docs)>0):
            content =  "\n\n".join(
        f"Source: {doc.metadata.get('source', 'Unknown')}\n"
        f"Content: {doc.page_content}"
        for doc in docs
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
    "You are helpfule sales agent"
),
                checkpointer=cls.checkpointer,
                response_format=None,
            )
        return cls._sales_agent

    @staticmethod
    async def user_query(query: str, thread_id: str, query_type: str, selected_model: str):
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
            # Structured fields are only complete after the agent finishes.
            result = await agent.ainvoke(agent_input, config=config)
            result_messages = result.get("messages", [])
            source_docs = []
            for message in reversed(result_messages):
                if isinstance(message, HumanMessage):
                    break
                if isinstance(message, ToolMessage):
                    source_docs.extend(getattr(message, "artifact", None) or [])
            if source_docs:
                sources = [
                    {
                        "source": doc.metadata.get("source"),
                        "page": doc.metadata.get("page"),
                    }
                    for doc in source_docs
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
                docs = getattr(message,"artifact",None)

                if docs:
                    sources= [{
                        "source": doc.metadata.get("source"),
                        "page": doc.metadata.get("page")
                    }
                    for doc in docs]
                    yield{"event":"sources","data":{"documents":sources}}

            elif isinstance(message, AIMessage):
                if isinstance(message.content, str) and message.content:
                    yield {"event": "delta", "data": {"content": message.content}}

    @staticmethod
    @wrap_model_call
    async def filter_tools(request, handler):
        query_type = request.state.get("query_type","general")
        selected_model_name = request.state.get("selected_model", "gpt-5.4-nano")
        if selected_model_name not in SalesAgent._available_models:
            selected_model_name = "gpt-5.4-nano"
 
 
        if query_type=="general":
          
            request = request.override(tools=[])
        elif query_type=="objection":
            request = request.override(response_format=ObjectionResponseOutput)
        
        request= request.override(model=ChatOpenAI(model=selected_model_name))    

        return await handler(request)


 

 
