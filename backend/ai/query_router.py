from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Literal

llm = init_chat_model(model="gpt-5.4-nano")


load_dotenv()


class QueryType(BaseModel):
    query_type: Literal["objection", "lead_qualification", "general"] = Field(
        description="""
            Classify the user's query into exactly one of the following categories:

            objection:
            The user is asking for help handling a prospect's objection, including
            concerns, doubts, hesitations, or reasons for not purchasing.
            

            lead_qualification:
            The user is asking about assessing a prospect's suitability,
            readiness, needs, budget, goals, or eligibility for the offer.
             

            general:
            The user's query does not fall into either of the above categories.
            This includes general questions, sales advice, product information,
            and unrelated requests.

            Choose the category based on the primary intent of the user's query.
            Return exactly one of the allowed values.
            """
    )


class QueryRouter:

    @staticmethod
    def analyze(query: str):

        messages = [
            SystemMessage(
                "Classify the user's message as 'objection' when they want help "
                "responding to or handling a prospect's sales objection. Classify "
                "all other messages as 'general'."
            ),
            HumanMessage(content=query),
        ]

        response = llm.with_structured_output(QueryType).invoke(messages)
        return response
