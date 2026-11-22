from __future__ import annotations

import secrets
from collections.abc import Iterable

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.fernet import Fernet, InvalidToken

hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def normalize_answer(answer: str) -> str:
    return " ".join(answer.strip().casefold().split())


def hash_answer(answer: str) -> str:
    return hasher.hash(normalize_answer(answer))


def verify_answer(answer_hash: str, answer: str) -> bool:
    return verify_password(answer_hash, normalize_answer(answer))


def opaque_token() -> str:
    return secrets.token_urlsafe(32)


def strong_password_errors(password: str) -> Iterable[str]:
    if len(password) < 10:
        yield "Password must be at least 10 characters."
    if len(password) > 256:
        yield "Password is too long."
    if not any(character.isalpha() for character in password):
        yield "Password must include a letter."
    if not any(character.isdigit() for character in password):
        yield "Password must include a number."


class EmbeddingCipher:
    prefix = "enc:v1:"

    def __init__(self, key: str) -> None:
        self.fernet = Fernet(key.encode("ascii"))

    def encrypt(self, value: str) -> str:
        token = self.fernet.encrypt(value.encode("utf-8")).decode("ascii")
        return f"{self.prefix}{token}"

    def decrypt(self, value: str) -> str:
        if not value.startswith(self.prefix):
            raise InvalidToken("Embedding is not encrypted.")
        token = value[len(self.prefix) :]
        return self.fernet.decrypt(token.encode("ascii")).decode("utf-8")
