import tempfile
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import backend.app as app_module
from backend.app import (
    ACTION_LABELS,
    LIGHT_TOTAL_MS,
    RegistrationRequest,
    SecurityAnswerInput,
    app,
    lighting_phase_at,
    movement_fallback_allowed,
    validate_registration,
)
from backend.db import Database
from backend.security import hash_answer, hash_password, verify_password

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["model"].startswith("sface-")
    ready = client.get("/api/ready")
    assert ready.status_code == 200
    assert ready.json()["ready"] is True


@pytest.mark.skipif(
    not (Path.cwd() / "dist" / "index.html").exists(),
    reason="Production frontend has not been built yet.",
)
def test_face_scanner_production_route() -> None:
    response = client.get("/faceScanner")
    assert response.status_code == 200
    assert "FaceSignUp" in response.text
    assert response.headers["cache-control"] == "no-store, max-age=0"
    admin = client.get("/admin")
    assert admin.status_code == 200
    assert "FaceSignUp" in admin.text
    assert admin.headers["cache-control"] == "no-store, max-age=0"


def test_current_user_requires_session() -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_registration_rejects_expired_or_unknown_ticket() -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "enrollment_ticket": "x" * 32,
            "display_name": "New User",
            "password": "secure-pass-42",
            "terms_accepted": True,
            "biometric_consent": True,
            "security_answers": [
                {"question": "What city were you born in?", "answer": "Shanghai"},
            ],
        },
    )
    assert response.status_code == 401


def test_registration_validation_returns_readable_field_error() -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "enrollment_ticket": "x" * 32,
            "display_name": "N",
            "password": "secure-pass-42",
            "terms_accepted": True,
            "biometric_consent": True,
            "security_answers": [
                {"question": "What city were you born in?", "answer": "Shanghai"},
            ],
        },
    )
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)
    assert "Name" in response.json()["detail"]


def test_websocket_session_challenge() -> None:
    response = client.post("/api/face/sessions")
    assert response.status_code == 200
    session = response.json()
    with client.websocket_connect(
        f"/ws/face?session_id={session['sessionId']}"
    ) as websocket:
        event = websocket.receive_json()
    assert event["type"] == "session_ready"
    assert event["step"] == 1
    assert event["action"] == session["challenge"]["action"]


def test_websocket_session_is_bound_to_requesting_client() -> None:
    response = client.post("/api/face/sessions")
    assert response.status_code == 200
    session_id = response.json()["sessionId"]
    with app_module.scan_store_lock:
        app_module.scan_sessions[session_id].client = "different-client"
    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect(f"/ws/face?session_id={session_id}") as websocket,
    ):
        websocket.receive_json()


def test_movement_challenges_are_accessible_without_single_eye_actions() -> None:
    assert set(ACTION_LABELS) == {"blink_both", "open_mouth", "turn_head"}


def test_custom_security_questions_are_allowed() -> None:
    request = RegistrationRequest(
        enrollment_ticket="x" * 32,
        display_name="Custom User",
        password="secure-pass-42",
        terms_accepted=True,
        biometric_consent=True,
        security_answers=[
            SecurityAnswerInput(
                question="Which street did I live on when I was ten?",
                answer="Evergreen",
            ),
        ],
    )
    validate_registration(request)


def test_registration_requires_biometric_consent() -> None:
    request = RegistrationRequest(
        enrollment_ticket="x" * 32,
        display_name="Consent User",
        password="secure-pass-42",
        terms_accepted=True,
        biometric_consent=False,
        security_answers=[
            SecurityAnswerInput(
                question="Which street did I live on when I was ten?",
                answer="Evergreen",
            ),
        ],
    )
    with pytest.raises(HTTPException, match="consent"):
        validate_registration(request)


def test_registration_requires_terms_acceptance() -> None:
    request = RegistrationRequest(
        enrollment_ticket="x" * 32,
        display_name="Terms User",
        password="secure-pass-42",
        terms_accepted=False,
        biometric_consent=True,
        security_answers=[
            SecurityAnswerInput(
                question="Which street did I live on when I was ten?",
                answer="Evergreen",
            ),
        ],
    )
    with pytest.raises(HTTPException, match="Terms"):
        validate_registration(request)


def test_server_controls_light_phase_schedule() -> None:
    assert lighting_phase_at(0) == "ambient"
    assert lighting_phase_at(1500) == "red"
    assert lighting_phase_at(2500) == "green"
    assert lighting_phase_at(3500) == "blue"
    assert lighting_phase_at(4500) == "white"
    assert lighting_phase_at(LIGHT_TOTAL_MS) is None


def test_movement_fallback_requires_complete_capture_and_no_light_signal() -> None:
    details = {
        "counts": {"ambient": 6, "red": 8, "green": 8, "blue": 8, "white": 9},
        "brightnessChanged": False,
        "correctColorOrder": 1,
    }
    assert movement_fallback_allowed(True, details)
    assert not movement_fallback_allowed(False, details)
    assert movement_fallback_allowed(True, {**details, "brightnessChanged": True})
    assert not movement_fallback_allowed(True, {**details, "correctColorOrder": 2})
    assert not movement_fallback_allowed(
        True, {**details, "counts": {**details["counts"], "red": 2}}
    )


def test_recovery_uses_name_without_email() -> None:
    response = client.post(
        "/api/auth/recovery/questions",
        json={"display_name": "Unknown Person"},
    )
    assert response.status_code == 200
    assert response.json()["questions"] == [
        "What is the answer to your security question?"
    ]


def test_face_login_requires_account_password(monkeypatch) -> None:
    root = Path.cwd() / ".test-data"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as directory:
        database = Database(Path(directory) / "answer-login-test.db")
        user_id = database.create_user(
            display_name="Password User",
            password_hash=hash_password("secure-pass-42"),
            embedding=[1.0, 0.0, 0.0],
            model_version="test",
            security_answers=[
                ("What was the name of my childhood pet?", hash_answer("Milo"))
            ],
        )
        monkeypatch.setattr(app_module, "db", database)
        candidate_token = "answer-candidate-" + "x" * 32
        with app_module.scan_store_lock:
            app_module.candidate_tokens[candidate_token] = {
                "user_id": user_id,
                "embedding": [1.0, 0.0, 0.0],
                "expires_at": app_module.time.time() + 60,
                "attempts": 0,
                "client": "testclient",
            }

        local_client = TestClient(app)
        wrong = local_client.post(
            "/api/auth/password",
            json={"candidate_token": candidate_token, "password": "Wrong"},
        )
        assert wrong.status_code == 401

        correct = local_client.post(
            "/api/auth/password",
            json={
                "candidate_token": candidate_token,
                "password": "secure-pass-42",
            },
        )
        assert correct.status_code == 200
        assert correct.json()["user"]["displayName"] == "Password User"
        with app_module.scan_store_lock:
            assert candidate_token not in app_module.candidate_tokens


def test_face_login_tokens_expire_and_are_bound_to_client(monkeypatch) -> None:
    root = Path.cwd() / ".test-data"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as directory:
        database = Database(Path(directory) / "candidate-security-test.db")
        user_id = database.create_user(
            display_name="Candidate User",
            password_hash=hash_password("secure-pass-42"),
            embedding=[1.0, 0.0, 0.0],
            model_version="test",
            security_answers=[("What is my recovery word?", hash_answer("Orbit"))],
        )
        monkeypatch.setattr(app_module, "db", database)
        local_client = TestClient(app)

        expired_token = "expired-candidate-" + "x" * 32
        foreign_token = "foreign-candidate-" + "x" * 32
        with app_module.scan_store_lock:
            app_module.candidate_tokens[expired_token] = {
                "user_id": user_id,
                "embedding": [1.0, 0.0, 0.0],
                "expires_at": app_module.time.time() - 1,
                "attempts": 0,
                "client": "testclient",
            }
            app_module.candidate_tokens[foreign_token] = {
                "user_id": user_id,
                "embedding": [1.0, 0.0, 0.0],
                "expires_at": app_module.time.time() + 60,
                "attempts": 0,
                "client": "different-client",
            }

        for token in (expired_token, foreign_token):
            response = local_client.post(
                "/api/auth/password",
                json={"candidate_token": token, "password": "secure-pass-42"},
            )
            assert response.status_code == 401
        with app_module.scan_store_lock:
            assert expired_token not in app_module.candidate_tokens
            assert foreign_token not in app_module.candidate_tokens


def test_forgotten_password_recovery_uses_one_question(monkeypatch) -> None:
    root = Path.cwd() / ".test-data"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as directory:
        database = Database(Path(directory) / "recovery-answer-test.db")
        user_id = database.create_user(
            display_name="Recovery User",
            password_hash=hash_password("old-secure-pass-42"),
            embedding=[1.0, 0.0, 0.0],
            model_version="test",
            security_answers=[
                ("What was the name of my childhood pet?", hash_answer("Milo"))
            ],
        )
        monkeypatch.setattr(app_module, "db", database)
        local_client = TestClient(app)

        questions = local_client.post(
            "/api/auth/recovery/questions",
            json={"display_name": "Recovery User"},
        )
        assert questions.status_code == 200
        assert questions.json()["questions"] == [
            "What was the name of my childhood pet?"
        ]

        reset = local_client.post(
            "/api/auth/recovery/reset",
            json={
                "display_name": "Recovery User",
                "answers": [
                    {
                        "question": "What was the name of my childhood pet?",
                        "answer": "Milo",
                    }
                ],
                "new_password": "new-secure-pass-42",
            },
        )
        assert reset.status_code == 200
        updated = database.get_user_by_id(user_id)
        assert updated is not None
        assert verify_password(updated["password_hash"], "new-secure-pass-42")


def test_registration_keeps_ticket_after_duplicate_name(monkeypatch) -> None:
    root = Path.cwd() / ".test-data"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as directory:
        database = Database(Path(directory) / "retry-test.db")
        database.create_user(
            display_name="Taken Name",
            password_hash=hash_password("secure-pass-42"),
            embedding=[1.0, 0.0, 0.0],
            model_version="test",
            security_answers=[
                ("What city were you born in?", hash_answer("Shanghai")),
                (
                    "What was the name of your first school?",
                    hash_answer("First School"),
                ),
            ],
        )
        monkeypatch.setattr(app_module, "db", database)
        ticket_value = "retry-ticket-" + "x" * 32
        with app_module.scan_store_lock:
            app_module.enrollment_tickets[ticket_value] = {
                "embedding": [0.0, 1.0, 0.0],
                "profile_image": b"\xff\xd8retry-photo\xff\xd9",
                "expires_at": app_module.time.time() + 120,
                "client": "testclient",
            }

        payload = {
            "enrollment_ticket": ticket_value,
            "display_name": "Taken Name",
            "password": "secure-pass-42",
            "terms_accepted": True,
            "biometric_consent": True,
            "security_answers": [
                {"question": "Which street did I grow up on?", "answer": "Evergreen"},
            ],
        }
        local_client = TestClient(app)
        duplicate = local_client.post("/api/auth/register", json=payload)
        assert duplicate.status_code == 409
        with app_module.scan_store_lock:
            assert ticket_value in app_module.enrollment_tickets
            assert "claimed" not in app_module.enrollment_tickets[ticket_value]

        payload["display_name"] = "Available Name"
        retry = local_client.post("/api/auth/register", json=payload)
        assert retry.status_code == 200
        with app_module.scan_store_lock:
            assert ticket_value not in app_module.enrollment_tickets
        assert database.get_user_by_display_name("Available Name") is not None


def test_enrollment_ticket_is_bound_to_requesting_client(monkeypatch) -> None:
    root = Path.cwd() / ".test-data"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as directory:
        database = Database(Path(directory) / "foreign-ticket-test.db")
        monkeypatch.setattr(app_module, "db", database)
        ticket_value = "foreign-ticket-" + "x" * 32
        with app_module.scan_store_lock:
            app_module.enrollment_tickets[ticket_value] = {
                "embedding": [1.0, 0.0, 0.0],
                "profile_image": None,
                "expires_at": app_module.time.time() + 120,
                "client": "different-client",
            }
        response = TestClient(app).post(
            "/api/auth/register",
            json={
                "enrollment_ticket": ticket_value,
                "display_name": "Foreign Ticket",
                "password": "secure-pass-42",
                "terms_accepted": True,
                "biometric_consent": True,
                "security_answers": [
                    {
                        "question": "Which street did I grow up on?",
                        "answer": "Evergreen",
                    }
                ],
            },
        )
        assert response.status_code == 401
        assert database.get_user_by_display_name("Foreign Ticket") is None


def test_name_login_and_account_deletion(monkeypatch) -> None:
    root = Path.cwd() / ".test-data"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as directory:
        database = Database(Path(directory) / "api-test.db")
        user_id = database.create_user(
            display_name="Accessible User",
            password_hash=hash_password("secure-pass-42"),
            embedding=[1.0, 0.0, 0.0],
            model_version="test",
            security_answers=[
                ("What city were you born in?", hash_answer("Shanghai")),
                (
                    "What was the name of your first school?",
                    hash_answer("First School"),
                ),
            ],
        )
        monkeypatch.setattr(app_module, "db", database)
        local_client = TestClient(app)
        login = local_client.post(
            "/api/auth/name-login",
            json={
                "display_name": "accessible user",
                "password": "secure-pass-42",
            },
        )
        assert login.status_code == 200
        assert "email" not in login.json()["user"]

        deleted = local_client.post(
            "/api/auth/account/delete",
            json={"password": "secure-pass-42"},
        )
        assert deleted.status_code == 200
        assert database.get_user_by_id(user_id) is None


def test_default_admin_must_change_password_before_management(monkeypatch) -> None:
    root = Path.cwd() / ".test-data"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as directory:
        database = Database(Path(directory) / "admin-test.db")
        photo = b"\xff\xd8test-profile-photo\xff\xd9"
        photo_user_id = database.create_user(
            display_name="Photo Person",
            password_hash=hash_password("secure-photo-42"),
            embedding=[0.0, 1.0, 0.0],
            model_version="test",
            profile_image=photo,
            security_answers=[
                ("What city were you born in?", hash_answer("Shanghai")),
                (
                    "What was the name of your first school?",
                    hash_answer("First School"),
                ),
            ],
        )
        monkeypatch.setattr(app_module, "db", database)
        local_client = TestClient(app)

        login = local_client.post(
            "/api/auth/name-login",
            json={"display_name": "admin", "password": "admin123"},
        )
        assert login.status_code == 200
        assert login.json()["user"]["role"] == "admin"
        assert login.json()["user"]["mustChangePassword"] is True
        assert local_client.get("/api/admin/users").status_code == 403

        password_change = local_client.post(
            "/api/admin/password",
            json={
                "current_password": "admin123",
                "new_password": "secure-admin-42",
            },
        )
        assert password_change.status_code == 200
        assert password_change.json()["user"]["mustChangePassword"] is False

        users = local_client.get("/api/admin/users")
        assert users.status_code == 200
        photo_user = next(
            item for item in users.json()["users"] if item["id"] == photo_user_id
        )
        assert photo_user["hasPhoto"] is True
        admin_user = next(
            item for item in users.json()["users"] if item["name"] == "admin"
        )
        assert admin_user["hasPhoto"] is False

        anonymous_client = TestClient(app)
        assert (
            anonymous_client.get(f"/api/admin/users/{photo_user_id}/photo").status_code
            == 401
        )

        photo_response = local_client.get(f"/api/admin/users/{photo_user_id}/photo")
        assert photo_response.status_code == 200
        assert photo_response.headers["content-type"] == "image/jpeg"
        assert photo_response.headers["cache-control"] == "no-store"
        assert photo_response.content == photo

        normal_client = TestClient(app)
        normal_login = normal_client.post(
            "/api/auth/name-login",
            json={
                "display_name": "Photo Person",
                "password": "secure-photo-42",
            },
        )
        assert normal_login.status_code == 200
        assert (
            normal_client.get(f"/api/admin/users/{photo_user_id}/photo").status_code
            == 403
        )
