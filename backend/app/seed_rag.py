from __future__ import annotations

import argparse
import os
from typing import Iterable

import google.generativeai as genai
import psycopg

DEFAULT_ROWS: list[dict[str, str]] = [
    {
        "report_name": "Weekly Active Users by Country",
        "description": "Count distinct active users per week and country for the last 90 days",
        "sql_text": (
            "SELECT date_trunc('week', event_time) AS week_start, country, "
            "COUNT(DISTINCT user_id) AS weekly_active_users "
            "FROM user_events "
            "WHERE event_time >= now() - interval '90 days' "
            "GROUP BY 1, 2 "
            "ORDER BY 1 DESC, 3 DESC;"
        ),
    },
    {
        "report_name": "Monthly Revenue by Plan",
        "description": "Summarize paid invoice revenue by month and subscription plan",
        "sql_text": (
            "SELECT date_trunc('month', paid_at) AS month_start, plan_name, "
            "SUM(amount_usd) AS revenue_usd "
            "FROM invoices "
            "WHERE status = 'paid' "
            "GROUP BY 1, 2 "
            "ORDER BY 1 DESC, 3 DESC;"
        ),
    },
    {
        "report_name": "Top 20 Products by Units Sold",
        "description": "Find the top 20 products by units sold in the last 30 days",
        "sql_text": (
            "SELECT p.product_name, SUM(oi.quantity) AS units_sold "
            "FROM order_items oi "
            "JOIN products p ON p.id = oi.product_id "
            "JOIN orders o ON o.id = oi.order_id "
            "WHERE o.created_at >= now() - interval '30 days' "
            "GROUP BY 1 "
            "ORDER BY 2 DESC "
            "LIMIT 20;"
        ),
    },
]


def embed_text(model: str, text: str) -> list[float]:
    response = genai.embed_content(
        model=model,
        content=text,
        task_type="retrieval_document",
    )
    return response["embedding"]


def seed_rows(rows: Iterable[dict[str, str]], dsn: str, embedding_model: str) -> int:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")

    genai.configure(api_key=api_key)
    inserted = 0

    insert_sql = """
    INSERT INTO rag_examples (report_name, description, sql_text, embedding)
    VALUES (%s, %s, %s, %s::vector)
    """

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for row in rows:
                combined_text = (
                    f"Report: {row['report_name']}\n"
                    f"Description: {row['description']}\n"
                    f"SQL:\n{row['sql_text']}"
                )
                embedding = embed_text(embedding_model, combined_text)
                cur.execute(
                    insert_sql,
                    (
                        row["report_name"],
                        row["description"],
                        row["sql_text"],
                        embedding,
                    ),
                )
                inserted += 1
        conn.commit()

    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed simple sample reports into rag_examples")
    parser.add_argument(
        "--dsn",
        default=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sql_agent"),
        help="PostgreSQL DSN",
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("EMBEDDING_MODEL", "models/text-embedding-004"),
        help="Embedding model name",
    )
    args = parser.parse_args()

    count = seed_rows(DEFAULT_ROWS, dsn=args.dsn, embedding_model=args.embedding_model)
    print(f"Inserted {count} rows into rag_examples")


if __name__ == "__main__":
    main()
