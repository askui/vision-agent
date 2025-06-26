from pydantic import Field
from pydantic_settings import BaseSettings


class Holo1Settings(BaseSettings):
    """Settings for Holo-1 model configuration.

    Environment variables:
        HOLO1_MODEL_NAME: Hugging Face model identifier (default: Hcompany/Holo1-7B)
        HOLO1_DEVICE: Device to run inference on (default: auto-detect)
        HOLO1_MAX_NEW_TOKENS: Maximum tokens to generate (default: 128)
        HOLO1_TEMPERATURE: Sampling temperature (default: 0.1)
    """

    model_name: str = Field(
        default="Hcompany/Holo1-7B",
        description="Hugging Face model identifier",
    )
    device: str | None = Field(
        default=None,
        description="Device to run inference on (cuda/cpu, auto-detect if None)",
    )
    max_new_tokens: int = Field(
        default=128,
        description="Maximum number of tokens to generate",
    )
    temperature: float = Field(
        default=0.1,
        description="Sampling temperature for generation",
    )

    model_config = {"env_prefix": "HOLO1_"}
