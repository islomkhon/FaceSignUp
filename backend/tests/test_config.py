import pytest
from cryptography.fernet import Fernet

from backend.config import Settings


def test_production_settings_require_trusted_network_and_secure_defaults(
    monkeypatch,
) -> None:
    key = Fernet.generate_key().decode("ascii")
    monkeypatch.setenv("FACESIGNUP_ENV", "production")
    monkeypatch.setenv("FACESIGNUP_ALLOWED_ORIGINS", "https://faces.example.com")
    monkeypatch.setenv("FACESIGNUP_ALLOWED_HOSTS", "faces.example.com")
    monkeypatch.setenv("FACESIGNUP_EMBEDDING_KEY", key)
    monkeypatch.delenv("FACESIGNUP_COOKIE_SECURE", raising=False)
    monkeypatch.delenv("FACESIGNUP_ALLOW_MOVEMENT_FALLBACK", raising=False)
    settings = Settings()
    assert settings.production
    assert settings.cookie_secure
    assert not settings.allow_movement_fallback
    assert settings.allowed_origins == ("https://faces.example.com",)


def test_production_requires_allowed_origins(monkeypatch) -> None:
    monkeypatch.setenv("FACESIGNUP_ENV", "production")
    monkeypatch.setenv(
        "FACESIGNUP_EMBEDDING_KEY", Fernet.generate_key().decode("ascii")
    )
    monkeypatch.delenv("FACESIGNUP_ALLOWED_ORIGINS", raising=False)
    with pytest.raises(RuntimeError, match="ALLOWED_ORIGINS"):
        Settings()


def test_production_requires_embedding_key(monkeypatch) -> None:
    monkeypatch.setenv("FACESIGNUP_ENV", "production")
    monkeypatch.setenv("FACESIGNUP_ALLOWED_ORIGINS", "https://faces.example.com")
    monkeypatch.setenv("FACESIGNUP_ALLOWED_HOSTS", "faces.example.com")
    monkeypatch.delenv("FACESIGNUP_EMBEDDING_KEY", raising=False)
    with pytest.raises(RuntimeError, match="EMBEDDING_KEY"):
        Settings()
