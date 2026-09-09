from __future__ import annotations

from openai import AsyncOpenAI
from pydantic import BaseModel

from .base import LLMProvider, T


class OpenAILLMProvider(LLMProvider):
    """OpenAI Responses structured-output adapter. No loose JSON parsing is used."""

    def __init__(self, api_key: str | None, model: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI LLM provider.")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate_structured(self, *, system: str, user: str, schema: type[T]) -> T:
        response = await self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": system}]},
                {"role": "user", "content": [{"type": "input_text", "text": user}]},
            ],
            text_format=schema,
        )
        parsed = response.output_parsed
        if not isinstance(parsed, schema):
            raise RuntimeError("OpenAI did not return a parsed structured result.")
        return parsed
