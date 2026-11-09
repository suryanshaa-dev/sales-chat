import asyncio

from backend.ai.agents.sales_agent import SalesAgent
from backend.ai.query_router import QueryRouter
from langsmith import traceable


def get_query_type(query: str):
    query_type = QueryRouter.analyze(query)
    return query_type


@traceable(name="sales_chat")
async def run_sales_agent(
    query: str,
    selected_model: str = "gpt-5.4-nano",
    thread_id: str | None = None,
    conversation_history: list[dict[str, str]] | None = None,
):
    if not thread_id:
        raise ValueError("thread_id is required")

    query_type = get_query_type(query).query_type
    yield {"event": "metadata", "data": {"query_type": query_type}}

    stream = SalesAgent.user_query(
        query=query,
        thread_id=thread_id,
        query_type=query_type,
        selected_model=selected_model,
        conversation_history=conversation_history or [],
    )
    async for item in stream:
        yield item
