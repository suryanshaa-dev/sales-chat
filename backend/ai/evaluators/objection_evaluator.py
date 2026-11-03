from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Literal
from langchain.messages import HumanMessage
from langchain_core.documents import Document
load_dotenv()

class ClassifyObjectionDocument(BaseModel):

    classification: Literal[
        "exact_match",
        "related_match",
        "no_match"
    ] = Field(description="Take the user's query and objection response document, and classify it")


class ObjectionEvaluator(BaseModel):

    @staticmethod
    def evaluate(model:str, document:Document, user_query: str):
        grader=ChatOpenAI(model=model, temperature=0).with_structured_output(ClassifyObjectionDocument)
        messages = [
            HumanMessage(content="User's Query:" \
            f"{user_query}" \
            "" \
            "Document contents:" \
            f"{document.page_content}")
        ]

        result = grader.invoke(messages)
        return result

