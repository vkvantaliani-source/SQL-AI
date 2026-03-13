CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS rag_examples (
    id BIGSERIAL PRIMARY KEY,
    report_name TEXT NOT NULL,
    description TEXT NOT NULL,
    sql_text TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS rag_examples_embedding_idx
    ON rag_examples
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE UNIQUE INDEX IF NOT EXISTS rag_examples_report_name_uidx
    ON rag_examples (report_name);
