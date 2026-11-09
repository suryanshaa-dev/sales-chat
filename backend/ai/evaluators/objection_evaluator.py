from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Literal
from langchain.messages import HumanMessage
from langchain_core.documents import Document

load_dotenv()


class ClassifyObjectionDocument(BaseModel):

    classification: Literal["exact_match", "related_match", "no_match"] = Field(
        description="""
Classify the document based on the user's query:

- exact_match: The document's script directly handles the user's objection.
- related_match: The script does not directly handle the objection but addresses a similar underlying concern or intent and can be partially applied.
- no_match: The script does not address the objection or any meaningfully related concern.

Focus on the underlying intent, not just wording or keyword similarity. Different objections may share the same underlying concern.

Return only the classification.
"""
    )


class ObjectionEvaluator(BaseModel):

    @staticmethod
    def evaluate(model: str, document: Document, user_query: str):
        grader = ChatOpenAI(model=model, temperature=0).with_structured_output(
            ClassifyObjectionDocument,
            method="function_calling",
        )
        messages = [
            HumanMessage(
                content="User's Query:"
                f"{user_query}"
                ""
                "Document contents:"
                f"{document.page_content}"
            )
        ]

        result = grader.invoke(messages)
        return result
