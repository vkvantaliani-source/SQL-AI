from __future__ import annotations

import os
from textwrap import dedent

import google.generativeai as genai

from .rag import RagExample


class SqlGenerator:
    def __init__(self) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set")

        genai.configure(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
        self.model = genai.GenerativeModel(self.model_name)

    def create_embedding(self, text: str) -> list[float]:
        result = genai.embed_content(
            model=self.embedding_model,
            content=text,
            task_type="retrieval_query",
            output_dimensionality=1536,
        )
        return result["embedding"]

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

        prompt = dedent(
            f"""
            You are a senior analytics engineer that writes PostgreSQL SQL queries.
            Use the retrieved examples as style and business logic references.
            Return only SQL, no markdown fences, no explanation.

            User question:
            {question}

            Retrieved examples:
            {examples_block}
            """
        ).strip()

        print("=== FULL PROMPT START ===")
        print(prompt)
        print("=== FULL PROMPT END ===")

        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
            ),
        )

        generated_sql = (response.text or "").strip()
        print("=== GENERATED SQL START ===")
        print(generated_sql)
        print("=== GENERATED SQL END ===")
        return generated_sql
