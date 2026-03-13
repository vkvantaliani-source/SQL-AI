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

    def query_similar(self, query_embedding: list[float], query_text: str, limit: int = 5) -> list[RagExample]:
        rows: list[tuple[str, str, str, float]] = []

        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                # 1) Hybrid search (vector + text score) when embedding is available.
                if query_embedding:
                    hybrid_sql = """
                    SELECT report_name,
                           description,
                           sql_text,
                           GREATEST(
                               1 - (embedding <=> %(embedding)s::vector),
                               CASE
                                   WHEN lower(description) = lower(%(query)s) THEN 1.0
                                   WHEN description ILIKE %(like_query)s THEN 0.9
                                   WHEN report_name ILIKE %(like_query)s THEN 0.85
                                   ELSE 0.0
                               END
                           ) AS similarity
                    FROM rag_examples
                    ORDER BY similarity DESC, report_name ASC
                    LIMIT %(limit)s;
                    """
                    cur.execute(
                        hybrid_sql,
                        {
                            "embedding": query_embedding,
                            "query": query_text,
                            "like_query": f"%{query_text}%",
                            "limit": limit,
                        },
                    )
                    rows = cur.fetchall()

                # 2) Text fallback if embedding unavailable or hybrid returned nothing.
                if not rows:
                    text_sql = """
                    SELECT report_name,
                           description,
                           sql_text,
                           CASE
                               WHEN lower(description) = lower(%(query)s) THEN 1.0
                               WHEN description ILIKE %(like_query)s THEN 0.9
                               WHEN report_name ILIKE %(like_query)s THEN 0.85
                               ELSE 0.0
                           END AS similarity
                    FROM rag_examples
                    WHERE lower(description) = lower(%(query)s)
                       OR description ILIKE %(like_query)s
                       OR report_name ILIKE %(like_query)s
                    ORDER BY similarity DESC, report_name ASC
                    LIMIT %(limit)s;
                    """
                    cur.execute(
                        text_sql,
                        {
                            "query": query_text,
                            "like_query": f"%{query_text}%",
                            "limit": limit,
                        },
                    )
                    rows = cur.fetchall()

                # 3) Final safety fallback: always return top rows if table is non-empty.
                if not rows:
                    default_sql = """
                    SELECT report_name,
                           description,
                           sql_text,
                           0.5 AS similarity
                    FROM rag_examples
                    ORDER BY created_at DESC, id DESC
                    LIMIT %(limit)s;
                    """
                    cur.execute(default_sql, {"limit": limit})
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
