from pydantic import BaseModel, Field

class RagResponse(BaseModel):
	answer: str = Field(..., description="Answer to the user input")
	reasoning: str = Field(..., description="Referencing the context, explain your answer")

if __name__ == "__main__":
	json_structure = RagResponse.model_json_schema()
	print(json_structure)