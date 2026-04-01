import base64
import logging

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

from askui import __version__

logger = logging.getLogger(__name__)


class OtelSettings(BaseSettings):
    """Settings for otel configuration"""

    model_config = SettingsConfigDict(
        env_prefix="ASKUI__OTEL_",
        case_sensitive=False,
        extra="ignore",
        validate_by_name=True,
    )

    enabled: bool = Field(default=False)
    user: str | None = Field(
        default=None,
        description="User for OTLP authentication. Required when enabled=True.",
    )
    secret: SecretStr | None = Field(
        default=None,
        description="Secret for OTLP authentication. Required when enabled=True.",
    )
    service_name: str = Field(default="askui-python-sdk")
    service_version: str = Field(default=__version__)
    endpoint: str | None = Field(
        default=None,
        description="OTLP endpoint URL.",
    )
    workspace_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ASKUI_WORKSPACE_ID", "askui_workspace_id"),
        description="AskUI workspace ID. Read from ASKUI_WORKSPACE_ID env var.",
    )

    @model_validator(mode="after")
    def validate_secret_when_enabled(self) -> Self:
        """Ensure secret is provided when OpenTelemetry is enabled."""
        if self.enabled and self.user is None:
            error_msg = "User is required when OpenTelemetry is enabled"
            raise ValueError(error_msg)
        if self.enabled and self.secret is None:
            error_msg = "Secret is required when OpenTelemetry is enabled"
            raise ValueError(error_msg)
        return self


def setup_opentelemetry_tracing(settings: OtelSettings) -> None:
    """
    Set up OpenTelemetry tracing for the FastAPI application.

    Args:
        settings (OtelSettings): OpenTelemetry configuration settings containing
            endpoint, user, secret, service name, and version.

    Returns:
        None

    """
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.httpx import (
            HTTPXClientInstrumentor,
        )
    except ImportError:
        logger.exception("Failed to set up OpenTelemetry Tracing.")
        return

    if not settings.enabled:
        return

    resource_attributes: dict[str, str] = {
        "service.name": settings.service_name,
        "service.version": settings.service_version,
    }
    if settings.workspace_id:
        resource_attributes["askui.workspace.id"] = settings.workspace_id
    resource = Resource.create(resource_attributes)
    provider = TracerProvider(resource=resource)

    base: str = settings.user + ":" + settings.secret.get_secret_value()  # type: ignore
    encoded = base64.b64encode(base.encode("utf-8")).decode("utf-8")

    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.endpoint,
        headers={"authorization": f"Basic {encoded}"},
    )

    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    trace.set_tracer_provider(provider)

    HTTPXClientInstrumentor().instrument()
