from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=5, description="Natural language analytics question")


class ChatResponse(BaseModel):
    sql: str
    context_examples: list[dict[str, str]]
