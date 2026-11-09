import json
from typing import Literal

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain.messages import HumanMessage
from pydantic import BaseModel, Field

load_dotenv()


class ClassifySalesKnowledgeDocument(BaseModel):

    index: int = Field(
        description="The zero-based index of the document being evaluated."
    )

    classification: Literal[
        "exact_match",
        "related_match",
        "no_match",
    ] = Field(
        description="""
Classify the document based on the user's sales-related query.

- exact_match: The document directly answers the user's query or provides
  a sales script, framework, technique, or explanation that directly
  addresses the user's specific question.

- related_match: The document does not directly answer the query but
  addresses a similar underlying sales concept, objection, problem,
  technique, or intent that can be partially applied.

- no_match: The document does not address the user's query or any
  meaningfully related sales concept.

Focus on semantic relevance and underlying intent, not merely keyword
similarity.

Do not classify a document as exact_match simply because it contains
the same keywords as the query.

Return exactly one classification for each document.
"""
    )


class SalesKnowledgeEvaluation(BaseModel):

    evaluations: list[ClassifySalesKnowledgeDocument] = Field(
        description="""
A classification for every document provided.

Each document must appear exactly once, identified by its original
zero-based index.

Do not omit documents or add classifications for documents that
were not provided.
"""
    )


class SalesKnowledgeEvaluator:

    @staticmethod
    def evaluate(
        model: str,
        documents: list[Document],
        user_query: str,
    ):

        if not documents:
            return []

        grader = ChatOpenAI(
            model=model,
            temperature=0,
        ).with_structured_output(
            SalesKnowledgeEvaluation,
            method="function_calling",
        )

        documents_payload = [
            {
                "index": index,
                "content": document.page_content,
            }
            for index, document in enumerate(documents)
        ]

        messages = [
            HumanMessage(
                content=f"""
Evaluate the relevance of each document against the user's query.

User's Query:
{user_query}

Documents:
{json.dumps(documents_payload, ensure_ascii=False)}

Return one classification for every document.
Preserve the original document indexes.
"""
            )
        ]

        result = grader.invoke(messages)

        # Associate each classification with its original document.
        return [
            {
                "index": evaluation.index,
                "document": documents[evaluation.index],
                "classification": evaluation.classification,
            }
            for evaluation in result.evaluations
        ]
