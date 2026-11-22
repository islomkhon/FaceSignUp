from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]


def environment_name() -> str:
    return os.environ.get("FACESIGNUP_ENV", "development").strip().lower()


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_origins(value: str | None, environment: str) -> tuple[str, ...]:
    if value:
        return tuple(
            origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()
        )
    if environment == "production":
        raise RuntimeError("FACESIGNUP_ALLOWED_ORIGINS is required in production.")
    return (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8100",
        "http://localhost:8100",
    )


def parse_hosts(value: str | None, environment: str) -> tuple[str, ...]:
    if value:
        return tuple(host.strip() for host in value.split(",") if host.strip())
    if environment == "production":
        raise RuntimeError("FACESIGNUP_ALLOWED_HOSTS is required in production.")
    return ("127.0.0.1", "localhost", "testserver")


def load_embedding_key(environment: str) -> str:
    configured = os.environ.get("FACESIGNUP_EMBEDDING_KEY")
    if configured:
        Fernet(configured.encode("ascii"))
        return configured
    if environment == "production":
        raise RuntimeError("FACESIGNUP_EMBEDDING_KEY is required in production.")

    key_path = ROOT / "data" / "embedding.key"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    if key_path.exists():
        key = key_path.read_text(encoding="ascii").strip()
        Fernet(key.encode("ascii"))
        return key
    key = Fernet.generate_key().decode("ascii")
    key_path.write_text(key, encoding="ascii")
    try:
        key_path.chmod(0o600)
    except OSError:
        pass
    return key


@dataclass(frozen=True)
class Settings:
    environment: str = field(default_factory=environment_name)
    allowed_origins: tuple[str, ...] = field(
        default_factory=lambda: parse_origins(
            os.environ.get("FACESIGNUP_ALLOWED_ORIGINS"),
            environment_name(),
        )
    )
    allowed_hosts: tuple[str, ...] = field(
        default_factory=lambda: parse_hosts(
            os.environ.get("FACESIGNUP_ALLOWED_HOSTS"),
            environment_name(),
        )
    )
    cookie_secure: bool = field(
        default_factory=lambda: env_bool(
            "FACESIGNUP_COOKIE_SECURE",
            environment_name() == "production",
        )
    )
    allow_movement_fallback: bool = field(
        default_factory=lambda: env_bool(
            "FACESIGNUP_ALLOW_MOVEMENT_FALLBACK",
            environment_name() != "production",
        )
    )
    max_frame_bytes: int = field(
        default_factory=lambda: int(
            os.environ.get("FACESIGNUP_MAX_FRAME_BYTES", str(2 * 1024 * 1024))
        )
    )
    max_request_bytes: int = field(
        default_factory=lambda: int(
            os.environ.get("FACESIGNUP_MAX_REQUEST_BYTES", str(512 * 1024))
        )
    )
    embedding_key: str = field(
        default_factory=lambda: load_embedding_key(environment_name())
    )

    @property
    def production(self) -> bool:
        return self.environment == "production"


settings = Settings()
