from pydantic_settings import BaseSettings, SettingsConfigDict

from askui.telemetry import TelemetrySettings


class Settings(BaseSettings):
    """Main settings class"""

    telemetry: TelemetrySettings = TelemetrySettings()

    model_config = SettingsConfigDict(
        env_prefix="ASKUI__VA__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()
