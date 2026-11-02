from dotenv import load_dotenv
from langchain.messages import HumanMessage, AIMessage
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.tools import tool
from langchain.agents.middleware import wrap_model_call
from backend.ai.schemas.sales_agent import ObjectionResponseOutput

load_dotenv()

class SalesAgentState(AgentState):
    query_type: str


class SalesAgent:
    checkpointer = InMemorySaver()
    _sales_agent = None

    _query_type = None

    @staticmethod
    @tool
    def get_objection_documents(query: str):
        """Find relevant objection documents and their word-for-word scripts."""
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory="./sales_objections_db",
            collection_name="sales_objections",
        )
        return vector_store.similarity_search_with_relevance_scores(query=query)[0]

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
    async def user_query(query: str, thread_id: str, query_type: str):
        config = {"configurable": {"thread_id": thread_id}}
        agent = SalesAgent.get_sales_agent()
        agent_input = {
            "messages": [HumanMessage(content=query)],
            "query_type": query_type,
        }

        if query_type == "objection":
            # Structured fields are only complete after the agent finishes.
            result = await agent.ainvoke(agent_input, config=config)
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
            if isinstance(message, AIMessage):
                if isinstance(message.content, str) and message.content:
                    yield {"event": "delta", "data": {"content": message.content}}

    @staticmethod
    @wrap_model_call
    async def filter_tools(request, handler):
        query_type = request.state.get("query_type","general")
        if query_type=="general":
            print("removed tools")
            request = request.override(tools=[])
        elif query_type=="objection":
            request = request.override(response_format=ObjectionResponseOutput)


        return await handler(request)


 

 
