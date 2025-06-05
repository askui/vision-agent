from pydantic import BaseModel, Field


class OpenRouterSettings(BaseModel):
    model: str = Field(..., description="OpenRouter model name")
