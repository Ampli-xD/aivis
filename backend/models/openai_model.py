import os
from typing import Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

from .base import AIModel


class OpenAIModel(AIModel):
    """
    Generic OpenAI model adapter.
    Supports any model on the Responses API with web_search
    (gpt-4o-mini, gpt-4o, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, o1, o3, etc.)

    Returns the complete raw API response — zero processing, zero extraction.
    """

    def __init__(self, model_id: str):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model_id

    async def generate_response(self, prompt: str, region_meta: dict = None) -> Dict[str, Any]:
        """
        Call the OpenAI Responses API and return the complete raw response dict.
        Attaches region location context to the web_search tool when provided.
        """
        try:
            tools = [{"type": "web_search"}]

            if region_meta:
                tools[0]["user_location"] = {
                    "type": "approximate",
                    "country": region_meta.get("country_code", ""),
                    "city": region_meta.get("city", ""),
                    "region": region_meta.get("region", ""),
                }

            response = await self.client.responses.create(
                model=self.model,
                input=prompt,
                tools=tools,
                tool_choice="auto",
            )

            return response.model_dump()

        except Exception as e:
            print(f"[OpenAIModel:{self.model}] Error: {e}")
            return {"error": str(e), "model": self.model}
