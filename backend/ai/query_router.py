from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Literal

llm = init_chat_model(model="gpt-5.4-nano")


load_dotenv()

QueryTypeValue = Literal["general", "objection"]


class QueryType(BaseModel):
    query_type: QueryTypeValue = Field(
        description=(
            "Classify whether the user's query asks for help responding to, "
            "overcoming, or handling a sales prospect's objection. Use 'general' "
            "for other sales-related queries."
        )
    )


class QueryRouter:

    @staticmethod
    def analyze(query: str):

        messages = [
            SystemMessage(
                "Classify the user's message as 'objection' when they want help "
                "responding to or handling a prospect's sales objection. Classify "
                "all other sales-related messages as 'general'."
            ),
            HumanMessage(content=query),
        ]

        response = llm.with_structured_output(QueryType).invoke(messages)
        return response
