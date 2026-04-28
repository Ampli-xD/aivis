from .openai_model import OpenAIModel
from .claude_model import ClaudeModel
from .perplexity_model import PerplexityModel
from .google_model import GoogleAIModel


def get_model(external_id: str):
    """
    Factory: returns an instantiated AI model for the given external_id.
    The external_id comes directly from the models table in the database.

    Routing:
      gpt-*, o1, o3, ...   → OpenAIModel      (OpenAI Responses API + web_search)
      claude-*             → ClaudeModel       (Anthropic Messages API + web_search)
      sonar*               → PerplexityModel   (Perplexity — search built-in)
      gemini-*             → GoogleAIModel     (Gemini + Google Search grounding)
    """
    if external_id.startswith("gpt-") or external_id.startswith("o"):
        return OpenAIModel(model_id=external_id)

    if external_id.startswith("claude-"):
        return ClaudeModel(model_id=external_id)

    if external_id.startswith("sonar"):
        return PerplexityModel(model_id=external_id)

    if external_id.startswith("gemini-"):
        return GoogleAIModel(model_id=external_id)

    raise ValueError(f"No model implementation found for external_id: '{external_id}'")
