from __future__ import annotations

import os
from textwrap import dedent

from openai import OpenAI

from .rag import RagExample


class SqlGenerator:
    def __init__(self) -> None:
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def create_embedding(self, text: str) -> list[float]:
        embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        response = self.client.embeddings.create(model=embedding_model, input=text)
        return response.data[0].embedding

    def generate_sql(self, question: str, examples: list[RagExample]) -> str:
        examples_block = "\n\n".join(
            [
                f"Example {i + 1}\n"
                f"Report: {ex.report_name}\n"
                f"Description: {ex.description}\n"
                f"SQL:\n{ex.sql}"
                for i, ex in enumerate(examples)
            ]
        ) or "No similar examples found."

        system_prompt = dedent(
            """
            You are a senior analytics engineer that writes PostgreSQL SQL queries.
            Use the retrieved examples as style and business logic references.
            Return only SQL, no markdown fences, no explanation.
            """
        ).strip()

        user_prompt = dedent(
            f"""
            User question:
            {question}

            Retrieved examples:
            {examples_block}
            """
        ).strip()

        completion = self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return completion.choices[0].message.content.strip()
