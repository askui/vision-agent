from fastapi import Depends

from chat.api.settings import Settings


def get_settings() -> Settings:
    """Get ChatApiSettings instance."""
    return Settings()


SettingsDep = Depends(get_settings)
