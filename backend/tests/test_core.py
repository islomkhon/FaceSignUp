from __future__ import annotations

import hashlib
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

import cv2
import numpy as np

from backend.db import Database
from backend.face_engine import (
    CANDIDATE_THRESHOLD,
    FACE_CONSISTENCY_THRESHOLD,
    FaceEngine,
    brightness_statistics,
    check_face_consistency,
    cosine_similarity,
    rank_face_matches,
)
from backend.security import (
    hash_answer,
    hash_password,
    normalize_answer,
    verify_answer,
    verify_password,
)


def test_password_and_answer_hashing() -> None:
    password_hash = hash_password("correct-horse-42")
    assert password_hash != "correct-horse-42"
    assert verify_password(password_hash, "correct-horse-42")
    assert not verify_password(password_hash, "incorrect")

    answer_hash = hash_answer("  New   York ")
    assert normalize_answer("  New   York ") == "new york"
    assert verify_answer(answer_hash, "new york")
    assert not verify_answer(answer_hash, "Boston")


def test_cosine_similarity() -> None:
    assert cosine_similarity([1, 0, 0], [1, 0, 0]) == 1.0
    assert cosine_similarity([1, 0, 0], [0, 1, 0]) == 0.0
    assert cosine_similarity([0, 0], [0, 0]) == -1.0


def test_rank_face_matches_returns_top_three_distinct_accounts() -> None:
    ranked = rank_face_matches(
        [1.0, 0.0],
        [
            ("one", [1.0, 0.0]),
            ("two", [0.9, 0.1]),
            ("two", [0.8, 0.2]),
            ("three", [0.7, 0.3]),
            ("four", [0.5, 0.5]),
        ],
    )
    assert [user_id for user_id, _score in ranked] == ["one", "two", "three"]
    assert all(score >= CANDIDATE_THRESHOLD for _user_id, score in ranked)


def test_three_stage_face_consistency() -> None:
    passed, scores = check_face_consistency([[1.0, 0.0], [0.99, 0.01], [0.98, 0.02]])
    assert passed
    assert len(scores) == 3
    assert min(scores) >= FACE_CONSISTENCY_THRESHOLD

    passed, _scores = check_face_consistency([[1.0, 0.0], [0.99, 0.01], [0.0, 1.0]])
    assert not passed


def test_lighting_evaluation() -> None:
    samples = {
        "ambient": [(55.0, (60.0, 55.0, 50.0))] * 3,
        "red": [(75.0, (35.0, 45.0, 145.0))] * 3,
        "green": [(78.0, (35.0, 150.0, 40.0))] * 3,
        "blue": [(82.0, (160.0, 45.0, 35.0))] * 3,
        "white": [(115.0, (150.0, 150.0, 150.0))] * 3,
    }
    passed, details = FaceEngine.evaluate_lighting(samples)
    assert passed
    assert details["lumaRange"] >= 4


def test_lighting_accepts_camera_white_balance_shift_with_strong_brightness() -> None:
    samples = {
        "ambient": [(100.0, (50.0, 40.0, 80.0))] * 3,
        "red": [(101.0, (50.0, 40.0, 81.0))] * 3,
        "green": [(110.0, (30.0, 20.0, 120.0))] * 3,
        "blue": [(109.0, (60.0, 60.0, 70.0))] * 3,
        "white": [(99.0, (100.0, 80.0, 20.0))] * 3,
    }
    passed, details = FaceEngine.evaluate_lighting(samples)
    assert passed
    assert details["responsiveColorPhases"] >= 2


def test_brightness_statistics_uses_face_roi() -> None:
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[20:60, 30:70] = (20, 80, 160)
    luminance, channels = brightness_statistics(image, (30, 20, 40, 40))
    assert 0 < luminance < 255
    assert channels == (20.0, 80.0, 160.0)


def test_profile_thumbnail_is_square_jpeg() -> None:
    image = np.full((320, 480, 3), (40, 100, 180), dtype=np.uint8)
    encoded, source = cv2.imencode(".jpg", image)
    assert encoded
    thumbnail = FaceEngine.create_profile_thumbnail(
        source.tobytes(), (170, 70, 120, 150)
    )
    decoded = cv2.imdecode(np.frombuffer(thumbnail, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert thumbnail.startswith(b"\xff\xd8")
    assert decoded is not None
    assert decoded.shape[:2] == (256, 256)


def test_database_registration_and_session() -> None:
    root = Path.cwd() / ".test-data"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as directory:
        database = Database(Path(directory) / "test.db")
        profile_image = b"\xff\xd8private-profile-photo\xff\xd9"
        user_id = database.create_user(
            display_name="Test Person",
            password_hash=hash_password("example-pass-42"),
            embedding=[0.6, 0.8, 0.0],
            model_version="test",
            profile_image=profile_image,
            security_answers=[
                ("What city were you born in?", hash_answer("Shanghai")),
                (
                    "What was the name of your first school?",
                    hash_answer("First School"),
                ),
            ],
        )
        user = database.get_user_by_id(user_id)
        assert user is not None
        assert user["display_name"] == "Test Person"
        assert database.get_user_by_display_name("test person")["id"] == user_id
        assert database.embeddings_for_user(user_id) == [[0.6, 0.8, 0.0]]
        assert database.profile_image_for_user(user_id) == profile_image
        listed_user = next(
            item for item in database.list_users() if item["id"] == user_id
        )
        assert bool(listed_user["has_photo"]) is True
        with closing(sqlite3.connect(database.path)) as connection:
            stored = connection.execute(
                "SELECT embedding FROM face_embeddings WHERE user_id = ?",
                (user_id,),
            ).fetchone()[0]
            stored_photo = connection.execute(
                "SELECT profile_image FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()[0]
        assert stored.startswith("enc:v1:")
        assert "0.6" not in stored
        assert stored_photo.startswith("enc:v1:")
        assert "private-profile-photo" not in stored_photo

        token = database.create_auth_session(user_id)
        with closing(sqlite3.connect(database.path)) as connection:
            stored_session_token = connection.execute(
                "SELECT token FROM auth_sessions WHERE user_id = ?",
                (user_id,),
            ).fetchone()[0]
        assert stored_session_token != token
        assert stored_session_token == hashlib.sha256(token.encode("ascii")).hexdigest()
        assert database.user_for_session(token)["id"] == user_id
        database.delete_auth_session(token)
        assert database.user_for_session(token) is None
