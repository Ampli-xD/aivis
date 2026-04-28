from abc import ABC, abstractmethod
from typing import Dict, Any

class AIModel(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, region_meta: dict = None) -> Dict[str, Any]:
        """
        Call the model API and return the complete raw response as a dict.
        No extraction, no transformation — caller receives exactly what the API returned.
        """
        pass
