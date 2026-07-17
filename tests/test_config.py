"""Offline smoke tests for the project foundation."""

from sovereignlab import __version__
from sovereignlab.config import Environment, Settings


def test_package_version_is_explicit() -> None:
    assert __version__ == "0.1.0"


def test_settings_have_safe_offline_defaults(monkeypatch) -> None:
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("ECOS_API_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.environment is Environment.DEVELOPMENT
    assert settings.log_level == "INFO"
    assert settings.mistral_api_key is None
    assert settings.ecos_api_key is None


def test_api_key_is_loaded_as_a_secret(monkeypatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "not-a-real-key")
    monkeypatch.setenv("ECOS_API_KEY", "not-a-real-ecos-key")

    settings = Settings(_env_file=None)

    assert settings.mistral_api_key is not None
    assert settings.mistral_api_key.get_secret_value() == "not-a-real-key"
    assert settings.ecos_api_key is not None
    assert settings.ecos_api_key.get_secret_value() == "not-a-real-ecos-key"
    assert "not-a-real-key" not in repr(settings)
    assert "not-a-real-ecos-key" not in repr(settings)
