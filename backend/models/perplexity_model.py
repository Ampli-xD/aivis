import os
from typing import Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

from .base import AIModel


class PerplexityModel(AIModel):
    """
    Perplexity model adapter.
    Perplexity uses an OpenAI-compatible API but with its own base URL and sonar models.
    Web search is built into every sonar model — no tool setup needed.

    Supported external_ids (from models table):
      sonar, sonar-pro, sonar-reasoning, sonar-reasoning-pro, sonar-deep-research

    Returns the complete raw API response — zero processing, zero extraction.
    """

    PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

    def __init__(self, model_id: str):
        self.api_key = os.environ.get("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable is not set")
        # Perplexity is OpenAI-compatible — reuse the OpenAI async client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.PERPLEXITY_BASE_URL,
        )
        self.model = model_id

    async def generate_response(self, prompt: str, region_meta: dict = None) -> Dict[str, Any]:
        """
        Call the Perplexity Chat Completions API and return the complete raw response dict.
        Region metadata is attached as a system message hint when provided.
        No extraction performed.
        """
        try:
            messages = []

            # Provide region context via system message (Perplexity has no location tool param)
            if region_meta:
                location_hint = (
                    f"The user is located in {region_meta.get('city', '')}, "
                    f"{region_meta.get('region', '')}, {region_meta.get('country_code', '')}. "
                    "Prioritize locally relevant sources when applicable."
                )
                messages.append({"role": "system", "content": location_hint})

            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )

            return response.model_dump()

        except Exception as e:
            print(f"[PerplexityModel:{self.model}] Error: {e}")
            return {"error": str(e), "model": self.model}
