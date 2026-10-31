import asyncio

from backend.ai.agents.sales_agent import SalesAgent
from langchain_core.utils.uuid import uuid7

_thread_id = str(uuid7())


def run_sales_agent(query: str):
    """Return the agent's async stream for FastAPI to forward directly."""
    return SalesAgent.user_query(query=query, thread_id=_thread_id)


 
