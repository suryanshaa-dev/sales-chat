from pydantic import BaseModel, Field

 
     

class ObjectionResponseOutput(BaseModel):
     objection_name: str = Field(
        max_length=100,
        description=(
            "The objection category identified from the retrieved "
            "sales script's objection-handling framework. "
            "Maximum 100 characters."
        )
    )

     script: str  = Field(description="You will recieve a document with multiple embedded script you will return all the scripts from the document in logic order in this way:" \
 
     "You: [SCRIPT LINE WORD FOR WORD]" \
     "Prospect: Here you will write prospect response in first person" \
     "You: [Next LINE OF SCRIPT]" \
     "and so on.... ")
 

     psychology: str = Field(
        max_length=1200,
        description=(
            "Explain the psychological principles behind the "
            "retrieved script and why it works. "
            "Maximum 1200 characters."
        )
    )

