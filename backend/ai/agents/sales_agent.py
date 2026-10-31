
from dotenv import load_dotenv
from langchain.messages import HumanMessage, AIMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()


class SalesAgent:

    checkpointer = InMemorySaver()

    sales_agent = create_agent(
        model="gpt-5.4-nano",
        tools=[],
        system_prompt=(
            "You are a helpful sales assistant trained "
            "on Alex Hormozi's closer framework."
        ),
        checkpointer=checkpointer,
    )

    @staticmethod
    async def user_query(query: str, thread_id: str):

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
       
        async for message, metadata in SalesAgent.sales_agent.astream(
            {"messages": [HumanMessage(content=query)]},
            config=config,
            stream_mode="messages",
        ):
           if isinstance(message, AIMessage):
                 
                yield(message.content)
