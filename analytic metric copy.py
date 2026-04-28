import os
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

from .base import AIModel

class GPT4oMini(AIModel):
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"
        
        # Pricing per 1M tokens (update as needed)
        self.input_price_per_1m = 0.15 # $0.15 per 1M input tokens
        self.cached_input_price_per_1m = 0.075 # $0.075 per 1M cached input tokens
        self.output_price_per_1m = 0.60 # $0.60 per 1M output tokens

    async def generate_response(self, prompt: str, region_meta: dict = None) -> Dict[str, Any]:
        """Generate response and return normalized format"""
        try:
            tools = [{"type": "web_search"}]
            
            if region_meta:
                tools[0]["user_location"] = {
                    "type": "approximate",
                    "country": region_meta.get("country_code", ""),
                    "city": region_meta.get("city", ""),
                    "region": region_meta.get("region", "")
                }

            response = await self.client.responses.create(
                model=self.model,
                input=prompt,
                tools=tools,
                tool_choice="auto"
            )
            
            raw_response = response.model_dump()
            normalized = self._extract_openai_response(raw_response)
            return normalized
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                "text": "",
                "citations": [],
                "usage": {},
                "cost": 0.0,
                "raw": {"error": str(e)}
            }

    def _extract_openai_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract normalized data from OpenAI Responses API format"""
        
        # Extract text
        text = ""
        if response_data.get("output"):
            for output_item in response_data["output"]:
                if output_item.get("type") == "message":
                    for content in output_item.get("content", []):
                        if content.get("type") == "output_text":
                            text = content.get("text", "")
                            break
        
        # Extract citations
        citations = []
        if response_data.get("output"):
            for output_item in response_data["output"]:
                for content in output_item.get("content", []):
                    annotations = content.get("annotations", [])
                    for ann in annotations:
                        if ann.get("type") == "citation":
                            citations.append({
                                "url": ann.get("url"),
                                "title": ann.get("title", "")
                            })
        
        # Fallback: extract URLs from text
        if not citations and text:
            urls = re.findall(r'https?://[^\s\)]+', text)
            citations = [{"url": url, "title": ""} for url in urls]
        
        # Extract usage and calculate cost
        usage = response_data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cached_tokens = usage.get("input_tokens_details", {}).get("cached_tokens", 0)
        
        cost = self._calculate_cost(input_tokens, output_tokens, cached_tokens)
        
        # Extract timing
        created_at = response_data.get("created_at")
        completed_at = response_data.get("completed_at")
        response_time = None
        if created_at and completed_at:
            response_time = completed_at - created_at
        
        return {
            "text": text,
            "citations": citations,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": usage.get("total_tokens", 0),
                "cached_tokens": cached_tokens
            },
            "cost": cost,
            "model_version": response_data.get("model", self.model),
            "response_time_seconds": response_time,
            "raw": response_data
        }

    def _calculate_cost(self, input_tokens: int, output_tokens: int, cached_tokens: int) -> float:
        """Calculate cost in USD"""
        billable_input = input_tokens - cached_tokens
        
        input_cost = (billable_input / 1_000_000) * self.input_price_per_1m
        cached_cost = (cached_tokens / 1_000_000) * self.cached_input_price_per_1m
        output_cost = (output_tokens / 1_000_000) * self.output_price_per_1m
        
        return round(input_cost + cached_cost + output_cost, 6)

    def extract_text(self, response_data: Dict[str, Any]) -> str:
        """Extract text from normalized response"""
        return response_data.get('text', '')

    async def calculate_metrics(
        self, 
        response_data: Dict[str, Any], 
        brand_name: str,
        brand_domain: str,
    ) -> Dict[str, Any]:
        """
        Extract AEO metrics.
        - Brand mention = ANY source discussing your brand
        - Competitors = ANY other brands mentioned
        """
        text = response_data.get('text', '')
        citations = response_data.get('citations', [])
        citation_urls = [c.get('url', '') for c in citations]
        
        analysis_prompt = f"""Analyze for brand visibility and competitive landscape.

Target Brand: {brand_name}
Primary Domain: {brand_domain}

Response:
{text}

Citations:
{json.dumps(citations, indent=2)}

Return ONLY valid JSON:
{{
  "brand_mentioned": boolean True if brand is mentioned as a source only else false,
  "narrative_mention": boolean True if brand is mentioned in narrative/citation else false,
  "brand_position": integer or null if brand not mentioned,
  "mention_count": integer or 0 if brand not mentioned,
  "mention_sources": [
    {{"source": "techcrunch.com", "url": "...", "is_primary_domain": boolean}}
  ],
  "competitors_mentioned": [
    {{"name": "CompetitorX", "narrative": boolean, "position": integer}}
  ],
  "sentiment_score": float or null if brand not mentioned,
  "all_sources": [
    {{"source": "string", "url": "string"}}
  ]
}}

Rules:
- brand_mentioned: true if {brand_name} discussed OR cited (any source)
- mention_sources: ALL sources mentioning {brand_name} (blogs, social, news, {brand_domain})
- is_primary_domain: true only if from {brand_domain}
- competitors_mentioned: ALL other brands in same industry
- narrative_mention: substantive discussion vs just listed
- brand_position: mention order (1st, 2nd, etc.)
- all_sources: every unique source cited
"""

        try:
            judge_response = await self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[{"role": "user", "content": analysis_prompt}],
                response_format={"type": "json_object"}
            )
            
            content = judge_response.choices[0].message.content.strip()
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            
            metrics = json.loads(content)
            metrics.update({
                "processing_version": "v1.0",
                "processed_at": datetime.utcnow().isoformat(),
                "requires_reprocessing": False,
                "citation_urls": citation_urls
            })
            
            return metrics
            
        except Exception as e:
            print(f"Metrics error: {e}")
            return self._default_metrics(error=str(e))
    
    def _default_metrics(self, error: str = None) -> Dict[str, Any]:
        """Return safe default metrics on failure"""
        return {
            "brand_mentioned": False,
            "narrative_mention": False,
            "brand_position": None,
            "mention_count": 0,
            "mention_sources": [],
            "competitors_mentioned": [],
            "sentiment_score": 0.0,
            "context_snippets": [],
            "recommendation_type": "none",
            "all_sources": [],
            "citation_urls": [],
            "processing_version": "v1.0",
            "processed_at": datetime.utcnow().isoformat(),
            "requires_reprocessing": True,
            "error": error
        }