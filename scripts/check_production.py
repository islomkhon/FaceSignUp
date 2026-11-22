from __future__ import annotations

import hashlib
import os
import sqlite3
import sys
from pathlib import Path

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.config import settings

EXPECTED_MODEL_HASHES = {
    "backend/models/face_detection_yunet_2023mar.onnx": (
        "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"
    ),
    "backend/models/face_recognition_sface_2021dec.onnx": (
        "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"
    ),
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    failures: list[str] = []
    warnings: list[str] = []

    if not settings.production:
        failures.append("FACESIGNUP_ENV must be production.")
    if settings.allow_movement_fallback:
        failures.append("Movement-only liveness fallback must be disabled.")
    if not settings.cookie_secure:
        failures.append("Secure cookies must be enabled.")
    if not settings.allowed_origins or any(
        not origin.startswith("https://") for origin in settings.allowed_origins
    ):
        failures.append("Every allowed origin must use HTTPS.")
    if not settings.allowed_hosts:
        failures.append("At least one production host must be configured.")
    try:
        Fernet(settings.embedding_key.encode("ascii"))
    except (ValueError, TypeError):
        failures.append("The embedding encryption key is invalid.")

    face_landmarker = ROOT / "dist" / "models" / "face_landmarker.task"
    if not face_landmarker.exists():
        face_landmarker = ROOT / "public" / "models" / "face_landmarker.task"
    required_files = [
        ROOT / "dist" / "index.html",
        face_landmarker,
        ROOT / "backend" / "models" / "face_detection_yunet_2023mar.onnx",
        ROOT / "backend" / "models" / "face_recognition_sface_2021dec.onnx",
    ]
    for path in required_files:
        if not path.exists():
            failures.append(f"Missing required file: {path}")
    for relative_path, expected_hash in EXPECTED_MODEL_HASHES.items():
        model_path = ROOT / relative_path
        if model_path.exists() and file_sha256(model_path) != expected_hash:
            failures.append(f"Model integrity check failed: {relative_path}")

    database_path = Path(
        os.environ.get("FACESIGNUP_DB", ROOT / "data" / "facesignup.db")
    )
    if database_path.exists():
        with sqlite3.connect(database_path) as connection:
            plaintext = connection.execute(
                "SELECT COUNT(*) FROM face_embeddings WHERE embedding NOT LIKE 'enc:v1:%'"
            ).fetchone()[0]
            unconsented = connection.execute(
                "SELECT COUNT(*) FROM users u "
                "WHERE EXISTS(SELECT 1 FROM face_embeddings f WHERE f.user_id = u.id) "
                "AND (u.consent_version IS NULL OR u.terms_version IS NULL)"
            ).fetchone()[0]
            default_admins = connection.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'admin' "
                "AND must_change_password = 1"
            ).fetchone()[0]
            users = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if plaintext:
            failures.append(f"{plaintext} face embeddings are not encrypted.")
        if unconsented:
            failures.append(
                f"{unconsented} existing accounts lack the Terms or biometric consent record."
            )
        if default_admins:
            failures.append(
                f"{default_admins} administrator account(s) still use a default password."
            )
        if users:
            warnings.append(
                f"The database contains {users} accounts; confirm they are production users."
            )
    else:
        warnings.append(
            "Database does not exist yet and will be created on first start."
        )

    warnings.extend(
        [
            "Custom liveness is not certified presentation-attack detection.",
            "Test the deployment on representative cameras, browsers, and users.",
            "Review biometric privacy and child-consent requirements for the jurisdiction.",
        ]
    )

    for warning in warnings:
        print(f"WARNING: {warning}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(1)
    print("Production configuration checks passed.")


if __name__ == "__main__":
    main()
