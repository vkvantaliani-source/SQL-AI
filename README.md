# SQL Agent (Text-to-SQL + pgvector RAG + Web Chatbot)

This starter project implements your idea:
- user asks a plain-language analytics question in a web chatbot,
- backend embeds the question,
- pgvector retrieves similar report/ad-hoc examples,
- Gemini generates a PostgreSQL SQL query using retrieved examples.

## Architecture

1. **Frontend chatbot** (`frontend/`)
   - Simple web page sends question to API.
2. **FastAPI backend** (`backend/app/`)
   - Creates embedding for user question.
   - Retrieves closest examples from `rag_examples` (pgvector cosine distance).
   - Prompts LLM with retrieved examples and returns generated SQL.
3. **RAG store in PostgreSQL + pgvector** (`db/init.sql`)
   - Stores `report_name`, `description`, `sql_text`, `embedding`.

## Run locally

```bash
docker compose up --build
```

- Web UI: http://localhost:8080
- API docs: http://localhost:8000/docs

Set your Google API key before starting:

```bash
export GOOGLE_API_KEY="your-key"
```

Default models used by the app:
- LLM: `gemini-3-flash-preview` (`GEMINI_MODEL`)
- Embeddings: `models/gemini-embedding-001` (`EMBEDDING_MODEL`)
- Retrieval threshold: `0.55` (`MIN_SIMILARITY`)

## RAG data format

Important retrieval contract:
- Stored `embedding` is generated from the saved **description** text.
- Incoming user **question** is embedded at query time.
- Vector search compares question embedding vs stored description embeddings.


Insert historical report/ad-hoc examples into `rag_examples`:

```sql
INSERT INTO rag_examples (report_name, description, sql_text, embedding)
VALUES (
  'Weekly Active Users',
  'Count unique users active each week by country',
  'SELECT date_trunc(''week'', event_time) AS week, country, COUNT(DISTINCT user_id) AS wau ...',
  '[0.01, -0.02, ...]'::vector
);
```

You can build an ingestion script later to:
1) generate embedding from **description only**,
2) upsert into `rag_examples`.


## Seed simple reports into RAG

After starting Postgres and setting `GOOGLE_API_KEY`, run (this is required because `db/init.sql` now creates schema only, without zero-vector seed rows):

```bash
cd backend
pip install -r requirements.txt
python -m app.seed_rag
```

This command is safe to re-run: it upserts by `report_name` and refreshes description embeddings.

This inserts 3 starter examples (WAU, revenue, top products) into `rag_examples`, each with an embedding built from the saved business description text.

If needed, point to another DB:

```bash
python -m app.seed_rag --dsn postgresql://postgres:postgres@localhost:5432/sql_agent
```


### Retrieval behavior

The backend follows pure vector retrieval on saved description embeddings: it embeds the incoming user question, compares against `rag_examples.embedding`, and returns only rows above `MIN_SIMILARITY` (default `0.55`). Retrieved description + SQL pairs are passed to the LLM prompt as context.

## Next enhancements

- Add schema-aware prompting (table + column metadata).
- Add SQL validation and guardrails (read-only enforcement).
- Add query execution preview with safe sandbox role.
- Add conversation memory and feedback loop (thumbs up/down -> retraining queue).
