import base64
import logging

from anthropic import Omit, omit
from pydantic import UUID4, Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

logger = logging.getLogger(__name__)


class AskUiInferenceApiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        validate_by_name=True,
        env_prefix="ASKUI__",
        env_nested_delimiter="__",
        arbitrary_types_allowed=True,
    )

    inference_endpoint: HttpUrl = Field(
        default_factory=lambda: HttpUrl("https://inference.askui.com"),  # noqa: F821
        validation_alias="ASKUI_INFERENCE_ENDPOINT",
    )
    authorization: SecretStr | Omit = Field(
        default=omit,
        description=(
            "The authorization header to use for the AskUI Inference API. "
            "If not provided, the token will be used to generate the header."
        ),
    )
    token: SecretStr | Omit = Field(
        default=omit,
        validation_alias="ASKUI_TOKEN",
    )
    workspace_id: UUID4 = Field(
        default=...,
        validation_alias="ASKUI_WORKSPACE_ID",
    )

    @model_validator(mode="after")
    def check_authorization(self) -> "Self":
        if self.authorization == omit and self.token == omit:
            error_message = (
                'Either authorization ("ASKUI__AUTHORIZATION" environment variable) '
                'or token ("ASKUI_TOKEN" environment variable) must be provided'
            )
            raise ValueError(error_message)
        return self

    @property
    def authorization_header(self) -> str:
        if self.authorization:
            return self.authorization.get_secret_value()
        assert not isinstance(self.token, Omit), "Token is not set"
        token_str = self.token.get_secret_value()
        token_base64 = base64.b64encode(token_str.encode()).decode()
        return f"Basic {token_base64}"

    @property
    def base_url(self) -> str:
        # NOTE(OS): Pydantic parses urls with trailing slashes
        # meaning "https://inference.askui.com" turns into -> "https://inference.askui.com/"
        # https://github.com/pydantic/pydantic/issues/7186
        return f"{self.inference_endpoint}api/v1/workspaces/{self.workspace_id}"
