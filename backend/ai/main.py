import asyncio

from backend.ai.agents.sales_agent import SalesAgent
from langchain_core.utils.uuid import uuid7
from backend.ai.query_router import QueryRouter

_thread_id = str(uuid7())


def get_query_type(query: str):
    query_type = QueryRouter.analyze(query)
    return query_type


def run_sales_agent(query: str):
    query_type = get_query_type(query).query_type

    return SalesAgent.user_query(
        query=query, thread_id=_thread_id, query_type=query_type
    )

 