from __future__ import annotations

import base64
import hashlib
import json
import os
import sqlite3
import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from backend.config import settings
from backend.security import EmbeddingCipher, hash_password

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "facesignup.db"


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_now() -> str:
    return utc_now().isoformat()


class Database:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or os.environ.get("FACESIGNUP_DB", DEFAULT_DB_PATH))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.cipher = EmbeddingCipher(settings.embedding_key)
        self.initialize()
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._lock, self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    internal_key TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    display_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    must_change_password INTEGER NOT NULL DEFAULT 0,
                    profile_image TEXT,
                    consent_version TEXT,
                    consented_at TEXT,
                    terms_version TEXT,
                    terms_accepted_at TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS face_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    embedding TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS security_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    question TEXT NOT NULL,
                    answer_hash TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS auth_sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_face_embeddings_user
                    ON face_embeddings(user_id);

                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_display_name_unique
                    ON users(display_name COLLATE NOCASE);
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(users)").fetchall()
            }
            if "email" in columns and "internal_key" not in columns:
                connection.execute(
                    "ALTER TABLE users RENAME COLUMN email TO internal_key"
                )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(users)").fetchall()
            }
            if "consent_version" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN consent_version TEXT")
            if "consented_at" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN consented_at TEXT")
            if "terms_version" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN terms_version TEXT")
            if "terms_accepted_at" not in columns:
                connection.execute(
                    "ALTER TABLE users ADD COLUMN terms_accepted_at TEXT"
                )
            if "role" not in columns:
                connection.execute(
                    "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'"
                )
            if "must_change_password" not in columns:
                connection.execute(
                    "ALTER TABLE users ADD COLUMN must_change_password "
                    "INTEGER NOT NULL DEFAULT 0"
                )
            if "profile_image" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN profile_image TEXT")

            for user in connection.execute(
                "SELECT id, internal_key FROM users"
            ).fetchall():
                generated_key = f"{user['id']}@local.invalid"
                if user["internal_key"] != generated_key:
                    connection.execute(
                        "UPDATE users SET internal_key = ? WHERE id = ?",
                        (generated_key, user["id"]),
                    )

            legacy_embeddings = connection.execute(
                "SELECT id, embedding FROM face_embeddings"
            ).fetchall()
            for row in legacy_embeddings:
                if not row["embedding"].startswith(self.cipher.prefix):
                    connection.execute(
                        "UPDATE face_embeddings SET embedding = ? WHERE id = ?",
                        (self.cipher.encrypt(row["embedding"]), row["id"]),
                    )

            admin = connection.execute(
                "SELECT id FROM users WHERE display_name = 'admin' COLLATE NOCASE"
            ).fetchone()
            if admin is None:
                admin_id = str(uuid.uuid4())
                connection.execute(
                    """
                    INSERT INTO users(
                        id, internal_key, display_name, password_hash,
                        role, must_change_password, created_at
                    )
                    VALUES (?, ?, 'admin', ?, 'admin', 1, ?)
                    """,
                    (
                        admin_id,
                        f"{admin_id}@local.invalid",
                        hash_password("admin123"),
                        iso_now(),
                    ),
                )

    def get_user_by_display_name(self, display_name: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM users WHERE display_name = ? COLLATE NOCASE",
                (display_name,),
            ).fetchone()

    def get_user_by_id(self, user_id: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()

    def create_user(
        self,
        *,
        display_name: str,
        password_hash: str,
        embedding: list[float],
        security_answers: list[tuple[str, str]],
        model_version: str,
        role: str = "user",
        must_change_password: bool = False,
        profile_image: bytes | None = None,
        consent_version: str = "biometric-v1",
        consented_at: str | None = None,
        terms_version: str = "terms-v6",
        terms_accepted_at: str | None = None,
    ) -> str:
        user_id = str(uuid.uuid4())
        internal_account_id = f"{user_id}@local.invalid"
        with self._lock, self.connect() as connection:
            connection.execute(
                """
                INSERT INTO users(
                    id, internal_key, display_name, password_hash,
                    role, must_change_password,
                    profile_image,
                    consent_version, consented_at, terms_version,
                    terms_accepted_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    internal_account_id,
                    display_name,
                    password_hash,
                    role,
                    int(must_change_password),
                    (
                        self.cipher.encrypt(
                            base64.b64encode(profile_image).decode("ascii")
                        )
                        if profile_image
                        else None
                    ),
                    consent_version,
                    consented_at or iso_now(),
                    terms_version,
                    terms_accepted_at or iso_now(),
                    iso_now(),
                ),
            )
            connection.execute(
                """
                INSERT INTO face_embeddings(user_id, embedding, model_version, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    self.cipher.encrypt(json.dumps(embedding)),
                    model_version,
                    iso_now(),
                ),
            )
            connection.executemany(
                """
                INSERT INTO security_answers(user_id, question, answer_hash)
                VALUES (?, ?, ?)
                """,
                [
                    (user_id, question, answer_hash)
                    for question, answer_hash in security_answers
                ],
            )
        return user_id

    def embeddings_for_user(self, user_id: str) -> list[list[float]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT embedding FROM face_embeddings WHERE user_id = ?", (user_id,)
            ).fetchall()
        return [json.loads(self.cipher.decrypt(row["embedding"])) for row in rows]

    def all_face_records(self) -> list[tuple[str, list[float]]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT user_id, embedding FROM face_embeddings"
            ).fetchall()
        return [
            (row["user_id"], json.loads(self.cipher.decrypt(row["embedding"])))
            for row in rows
        ]

    def security_answers_for_user(self, user_id: str) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT question, answer_hash
                FROM security_answers
                WHERE user_id = ?
                ORDER BY id
                """,
                (user_id,),
            ).fetchall()

    def update_password(
        self,
        user_id: str,
        password_hash: str,
        *,
        must_change_password: bool | None = None,
    ) -> None:
        with self._lock, self.connect() as connection:
            if must_change_password is None:
                connection.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (password_hash, user_id),
                )
            else:
                connection.execute(
                    "UPDATE users SET password_hash = ?, must_change_password = ? "
                    "WHERE id = ?",
                    (password_hash, int(must_change_password), user_id),
                )
            connection.execute(
                "DELETE FROM auth_sessions WHERE user_id = ?", (user_id,)
            )

    def delete_user(self, user_id: str) -> None:
        with self._lock, self.connect() as connection:
            connection.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def list_users(self) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT
                    u.id,
                    u.display_name,
                    u.role,
                    u.must_change_password,
                    u.created_at,
                    EXISTS(
                        SELECT 1 FROM face_embeddings f WHERE f.user_id = u.id
                    ) AS has_face,
                    u.profile_image IS NOT NULL AS has_photo
                FROM users u
                ORDER BY lower(u.display_name)
                """
            ).fetchall()

    def update_role(self, user_id: str, role: str) -> None:
        with self._lock, self.connect() as connection:
            connection.execute(
                "UPDATE users SET role = ? WHERE id = ?",
                (role, user_id),
            )

    def count_admins(self) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM users WHERE role = 'admin'"
            ).fetchone()
        return int(row["count"])

    def profile_image_for_user(self, user_id: str) -> bytes | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT profile_image FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        if not row or not row["profile_image"]:
            return None
        encoded = self.cipher.decrypt(row["profile_image"])
        return base64.b64decode(encoded)

    def create_auth_session(self, user_id: str, lifetime_hours: int = 12) -> str:
        token = uuid.uuid4().hex + uuid.uuid4().hex
        token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
        expires_at = (utc_now() + timedelta(hours=lifetime_hours)).isoformat()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO auth_sessions(token, user_id, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (token_hash, user_id, expires_at, iso_now()),
            )
        return token

    def user_for_session(self, token: str) -> sqlite3.Row | None:
        token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT u.*
                FROM auth_sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token = ? AND s.expires_at > ?
                """,
                (token_hash, iso_now()),
            ).fetchone()
        return row

    def delete_auth_session(self, token: str) -> None:
        token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM auth_sessions WHERE token = ?", (token_hash,)
            )

    def delete_expired_auth_sessions(self) -> None:
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM auth_sessions WHERE expires_at <= ?",
                (iso_now(),),
            )


db = Database()
