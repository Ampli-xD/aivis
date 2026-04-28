import os
from typing import Dict, Any
import anthropic
from dotenv import load_dotenv

load_dotenv()

from .base import AIModel


class ClaudeModel(AIModel):
    """
    Anthropic Claude model adapter.
    Supports any Claude model with the built-in web_search tool
    (claude-3-5-sonnet-20241022, claude-3-7-sonnet-20250219, claude-3-5-haiku-20241022, etc.)

    Returns the complete raw API response — zero processing, zero extraction.
    """

    def __init__(self, model_id: str):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        self.model = model_id

    async def generate_response(self, prompt: str, region_meta: dict = None) -> Dict[str, Any]:
        """
        Call the Anthropic Messages API with the web_search tool and return
        the complete raw response dict. No extraction performed.
        """
        try:
            web_search_tool = {"type": "web_search_20250305", "name": "web_search"}

            if region_meta:
                location = {"type": "approximate"}
                if region_meta.get("country_code"):
                    location["country"] = region_meta["country_code"]
                if region_meta.get("city"):
                    location["city"] = region_meta["city"]
                if region_meta.get("region"):
                    location["region"] = region_meta["region"]
                if region_meta.get("timezone"):
                    location["timezone"] = region_meta["timezone"]
                web_search_tool["user_location"] = location

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=8096,
                messages=[{"role": "user", "content": prompt}],
                tools=[web_search_tool],
            )

            return response.model_dump()

        except Exception as e:
            print(f"[ClaudeModel:{self.model}] Error: {e}")
            return {"error": str(e), "model": self.model}
