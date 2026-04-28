import os
from typing import Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

from .base import AIModel


class GoogleAIModel(AIModel):
    """
    Google Gemini model adapter with Google Search grounding.

    "Google AI Overviews" are powered by Gemini + Google Search retrieval.
    The closest API-accessible equivalent is Gemini with Google Search grounding enabled,
    which uses the same underlying retrieval pipeline as AI Overviews in Google Search.

    Supported external_ids (from models table):
      gemini-2.0-flash, gemini-2.0-flash-lite, gemini-2.5-pro-preview-03-25, etc.

    Returns the complete raw API response as a dict — zero processing, zero extraction.
    """

    def __init__(self, model_id: str):
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        self.client = genai.Client(api_key=self.api_key)
        self.model = model_id

    async def generate_response(self, prompt: str, region_meta: dict = None) -> Dict[str, Any]:
        """
        Call the Gemini API with Google Search grounding and return the complete
        raw response dict. Region metadata is prepended as context when provided.
        No extraction performed.
        """
        try:
            # Optionally prepend region context to the prompt
            full_prompt = prompt
            if region_meta:
                location_hint = (
                    f"[Location context: {region_meta.get('city', '')}, "
                    f"{region_meta.get('region', '')}, {region_meta.get('country_code', '')}] "
                )
                full_prompt = location_hint + prompt

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                ),
            )

            return response.model_dump()

        except Exception as e:
            print(f"[GoogleAIModel:{self.model}] Error: {e}")
            return {"error": str(e), "model": self.model}
