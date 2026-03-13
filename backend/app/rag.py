from __future__ import annotations

import os
from dataclasses import dataclass

import psycopg


@dataclass
class RagExample:
    report_name: str
    description: str
    sql: str
    similarity: float


class RagStore:
    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sql_agent")
        self.min_similarity = float(os.getenv("MIN_SIMILARITY", "0.55"))

    def query_similar(self, query_embedding: list[float], limit: int = 5) -> list[RagExample]:
        if not query_embedding:
            return []

        sql = """
        SELECT report_name,
               description,
               sql_text,
               1 - (embedding <=> %(embedding)s::vector) AS similarity
        FROM rag_examples
        WHERE 1 - (embedding <=> %(embedding)s::vector) >= %(min_similarity)s
        ORDER BY embedding <=> %(embedding)s::vector
        LIMIT %(limit)s;
        """

        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    {
                        "embedding": query_embedding,
                        "min_similarity": self.min_similarity,
                        "limit": limit,
                    },
                )
                rows = cur.fetchall()

        return [
            RagExample(
                report_name=row[0],
                description=row[1],
                sql=row[2],
                similarity=float(row[3]),
            )
            for row in rows
        ]
