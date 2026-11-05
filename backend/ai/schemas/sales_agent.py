from pydantic import BaseModel, Field
from typing import Literal


class ObjectionResponseOutput(BaseModel):
    objection_name: str = Field(
        max_length=100,
        description=(
            "Copy the heading value exactly from the retrieved objection document. "
            "If no objection document was retrieved, return an empty string. "
            "Maximum 100 characters."
        ),
    )

    script: str = Field(
        description="You will recieve a document with multiple embedded script you will return all the scripts from the document in logic order in this way:"
        "You: [SCRIPT LINE WORD FOR WORD]"
        "Prospect: Here you will write prospect response in first person"
        "You: [Next LINE OF SCRIPT]"
        "and so on.... "
    )

    psychology: list[str] = Field(
        min_length=1,
        max_length=6,
        description=(
            "Explain why the retrieved script works as a list of 3 to 6 "
            "concise, specific psychological principles. Each list item must "
            "express one idea in plain language."
        ),
    )


QualificationLevel = Literal[
    "Low",
    "Moderate",
    "High",
    "Unconfirmed",
]


class LeadQualificationResponse(BaseModel):

    qualification_score: int = Field(
        ge=0,
        le=100,
        description=(
            "Output the overall lead qualification score based on "
            "need, budget, authority, and timeline."
        ),
    )

    need: QualificationLevel = Field(description="Classify the need of the prospect.")

    need_reasoning: str = Field(
        max_length=100,
        description=(
            "Provide reasoning in 100 characters or fewer "
            "for the need classification. If Unconfirmed, output 'N/A'."
        ),
    )

    budget: QualificationLevel = Field(
        description="Classify the budget of the prospect."
    )

    budget_reasoning: str = Field(
        max_length=100,
        description=(
            "Provide reasoning in 100 characters or fewer "
            "for the budget classification. If Unconfirmed, output 'N/A'."
        ),
    )

    authority: QualificationLevel = Field(
        description="Classify the authority of the prospect to make the purchase."
    )

    authority_reasoning: str = Field(
        max_length=100,
        description=(
            "Provide reasoning in 100 characters or fewer "
            "for the authority classification. If Unconfirmed, output 'N/A'."
        ),
    )

    timeline: QualificationLevel = Field(
        description=(
            "Classify the timeline of the prospect, "
            "indicating how soon they are likely to make the purchase."
        ),
    )

    timeline_reasoning: str = Field(
        max_length=100,
        description=(
            "Provide reasoning in 100 characters or fewer "
            "for the timeline classification. If Unconfirmed, output 'N/A'."
        ),
    )
