from app.core.config import settings


def test_settings_load():
    assert settings.APP_NAME
    assert settings.API_V1_PREFIX.startswith("/")
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    assert settings.MAX_TOOL_RETRIES >= 0
