from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .llm import SqlGenerator
from .models import ChatRequest, ChatResponse
from .rag import RagStore

app = FastAPI(title="SQL Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sql_generator = SqlGenerator()
rag_store = RagStore()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        question_embedding = sql_generator.create_embedding(request.question)
        similar_examples = rag_store.query_similar(question_embedding, limit=5)
        generated_sql = sql_generator.generate_sql(request.question, similar_examples)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        sql=generated_sql,
        context_examples=[
            {
                "report_name": ex.report_name,
                "description": ex.description,
                "sql": ex.sql,
                "similarity": f"{ex.similarity:.4f}",
            }
            for ex in similar_examples
        ],
    )
