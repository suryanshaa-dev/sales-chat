from pydantic import BaseModel, Field


class ObjectionResponseOutput(BaseModel):
    objection_name: str = Field(
        max_length=100,
        description=(
            "The objection category identified from the retrieved return None if not found "
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
