from __future__ import annotations

import asyncio
import json
import logging
import random
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import settings
from backend.db import db, iso_now
from backend.face_engine import (
    FACE_CONSISTENCY_THRESHOLD,
    MATCH_THRESHOLD,
    MODEL_VERSION,
    FaceProcessingError,
    brightness_statistics,
    check_face_consistency,
    cosine_similarity,
    face_engine,
    rank_face_matches,
)
from backend.security import (
    hash_answer,
    hash_password,
    opaque_token,
    strong_password_errors,
    verify_answer,
    verify_password,
)

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
SESSION_TTL_SECONDS = 180
FACE_ATTEMPT_WINDOW = 90
ENROLLMENT_TTL_SECONDS = 15 * 60
BIOMETRIC_CONSENT_VERSION = "biometric-v1"
TERMS_VERSION = "terms-v6"
SESSION_COOKIE_NAME = "__Host-fs_session" if settings.production else "fs_session"
RATE_RETENTION_SECONDS = 300
RATE_STORE_MAX_KEYS = 5000
MAX_WEBSOCKET_TEXT_BYTES = 4096
LIGHT_SCHEDULE = (
    ("ambient", 1500),
    ("red", 1000),
    ("green", 1000),
    ("blue", 1000),
    ("white", 1200),
)
LIGHT_PHASES = tuple(phase for phase, _duration in LIGHT_SCHEDULE)
LIGHT_TOTAL_MS = sum(duration for _phase, duration in LIGHT_SCHEDULE)
ACTION_LABELS = {
    "blink_both": "Blink both eyes normally",
    "open_mouth": "Open your mouth briefly",
    "turn_head": "Turn your head slowly to one side",
}
logger = logging.getLogger("uvicorn.error")


class PasswordLoginRequest(BaseModel):
    candidate_token: str = Field(min_length=20, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class AdminPasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=10, max_length=256)


class AdminRoleUpdateRequest(BaseModel):
    role: Literal["user", "admin"]


class NameLoginRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=256)


class SecurityAnswerInput(BaseModel):
    question: str = Field(min_length=5, max_length=160)
    answer: str = Field(min_length=2, max_length=160)


class RegistrationRequest(BaseModel):
    enrollment_ticket: str = Field(min_length=20, max_length=128)
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=10, max_length=256)
    security_answers: list[SecurityAnswerInput] = Field(min_length=1, max_length=1)
    terms_accepted: bool = False
    biometric_consent: bool = False


class RecoveryQuestionsRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)


class RecoveryResetRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    answers: list[SecurityAnswerInput] = Field(min_length=1, max_length=1)
    new_password: str = Field(min_length=10, max_length=256)


@dataclass
class ScanSession:
    id: str
    challenge_action: str
    created_at: float
    client: str
    step: int = 1
    action_passed: bool = False
    lighting_ready: bool = False
    lighting_started_at: float | None = None
    current_phase: str | None = None
    lighting_samples: dict[str, list[tuple[float, tuple[float, float, float]]]] = field(
        default_factory=lambda: {phase: [] for phase in LIGHT_PHASES}
    )
    lighting_detection_failures: dict[str, int] = field(
        default_factory=lambda: {phase: 0 for phase in LIGHT_PHASES}
    )
    latest_frame: bytes | None = None
    last_quality_sent: float = 0.0
    last_frame_processed: float = 0.0
    last_face_bbox: tuple[int, int, int, int] | None = None
    last_face_detection_at: float = 0.0
    last_face_quality: dict[str, Any] | None = None
    reference_embedding: list[float] | None = None
    lighting_frame_payload: bytes | None = None
    lighting_embedding: list[float] | None = None


scan_sessions: dict[str, ScanSession] = {}
candidate_tokens: dict[str, dict[str, Any]] = {}
enrollment_tickets: dict[str, dict[str, Any]] = {}
scan_store_lock = threading.RLock()
rate_events: dict[str, list[float]] = {}
face_task_lock = asyncio.Semaphore(1)


def client_key(request: Request | WebSocket) -> str:
    if request.client:
        return request.client.host
    return "unknown"


def enforce_rate(key: str, limit: int, window_seconds: int) -> None:
    now = time.time()
    with scan_store_lock:
        if len(rate_events) > RATE_STORE_MAX_KEYS:
            stale_keys = [
                stored_key
                for stored_key, timestamps in rate_events.items()
                if not timestamps or now - timestamps[-1] >= RATE_RETENTION_SECONDS
            ]
            for stored_key in stale_keys:
                rate_events.pop(stored_key, None)
            if len(rate_events) >= RATE_STORE_MAX_KEYS:
                oldest_key = min(
                    rate_events,
                    key=lambda stored_key: rate_events[stored_key][-1],
                )
                rate_events.pop(oldest_key, None)
        events = [
            event for event in rate_events.get(key, []) if now - event < window_seconds
        ]
        if len(events) >= limit:
            raise HTTPException(
                status_code=429, detail="Too many attempts. Wait and try again."
            )
        events.append(now)
        rate_events[key] = events


def validate_registration(request: RegistrationRequest) -> None:
    if not request.terms_accepted:
        raise HTTPException(
            status_code=400,
            detail="Please agree to the Terms of Service.",
        )
    if not request.biometric_consent:
        raise HTTPException(
            status_code=400,
            detail="Explicit consent is required before storing a face template.",
        )
    errors = list(strong_password_errors(request.password))
    if errors:
        raise HTTPException(status_code=400, detail=errors[0])
    if len(request.display_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Enter your name.")
    if any(len(item.question.strip()) < 5 for item in request.security_answers):
        raise HTTPException(
            status_code=400, detail="Write a security question with more detail."
        )
    if any(len(item.answer.strip()) < 4 for item in request.security_answers):
        raise HTTPException(
            status_code=400, detail="Security answer must have at least 4 characters."
        )


def set_auth_cookie(response: Response, token: str, request: Request) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=12 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure or request.url.scheme == "https",
        samesite="strict",
        path="/",
    )


def require_admin_session(
    request: Request,
    *,
    allow_password_change: bool = False,
) -> sqlite3.Row:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    user = db.user_for_session(token) if token else None
    if not user:
        raise HTTPException(status_code=401, detail="Sign in as an administrator.")
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Administrator access is required.")
    if user["must_change_password"] and not allow_password_change:
        raise HTTPException(
            status_code=403,
            detail="Change the default administrator password before continuing.",
        )
    return user


def public_user(user: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": user["id"],
        "displayName": user["display_name"],
        "role": user["role"],
        "mustChangePassword": bool(user["must_change_password"]),
    }


def prune_ephemeral_state() -> None:
    now = time.time()
    with scan_store_lock:
        for session_id, session in list(scan_sessions.items()):
            if now - session.created_at > SESSION_TTL_SECONDS:
                scan_sessions.pop(session_id, None)
        for store in (candidate_tokens, enrollment_tickets):
            for token, value in list(store.items()):
                if value["expires_at"] < now:
                    store.pop(token, None)
    db.delete_expired_auth_sessions()


def lighting_phase_at(elapsed_ms: float) -> str | None:
    cursor = 0.0
    for phase, duration in LIGHT_SCHEDULE:
        cursor += duration
        if elapsed_ms < cursor:
            return phase
    return None


def movement_fallback_allowed(action_passed: bool, details: dict[str, Any]) -> bool:
    return (
        action_passed
        and all(count >= 3 for count in details["counts"].values())
        and details["correctColorOrder"] < 2
    )


async def finalize_lighting_embedding(session: ScanSession) -> None:
    if session.lighting_embedding is not None or session.lighting_frame_payload is None:
        return
    try:
        session.lighting_embedding, _detection = await run_face_task(
            face_engine.extract_embedding,
            session.lighting_frame_payload,
        )
        logger.info("lighting-stage face embedding captured")
    except FaceProcessingError as error:
        logger.info(
            "lighting-stage embedding failed code=%s message=%s",
            error.code,
            error.message,
        )


# Scan progression is server-authoritative; browser events are evidence, not decisions.
app = FastAPI(
    title="FaceSignUp MVP",
    version="0.1.0",
    docs_url=None if settings.production else "/docs",
    redoc_url=None if settings.production else "/redoc",
    openapi_url=None if settings.production else "/openapi.json",
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))


@app.exception_handler(RequestValidationError)
async def request_validation_error(request: Request, error: RequestValidationError):
    field_labels = {
        "enrollment_ticket": "Face scan",
        "display_name": "Name",
        "terms_accepted": "Terms of Service",
        "biometric_consent": "Face-template consent",
        "password": "Password",
        "security_answers": "Recovery question",
        "question": "Recovery question",
        "answer": "Recovery answer",
    }
    messages: list[str] = []
    for item in error.errors():
        location = [part for part in item.get("loc", ()) if part != "body"]
        field = str(location[-1]) if location else "Request"
        label = field_labels.get(field, field.replace("_", " ").title())
        message = str(item.get("msg", "Invalid value"))
        if "at least" in message:
            message = message.replace("String should have", "Must have")
        readable = f"{label}: {message}."
        if readable not in messages:
            messages.append(readable)
        logger.info(
            "request validation failed path=%s field=%s",
            request.url.path,
            ".".join(str(part) for part in location),
        )
    return JSONResponse(
        status_code=422,
        content={"detail": " ".join(messages) or "Please check the form values."},
    )


@app.middleware("http")
async def security_headers(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if (
        settings.production
        and request.url.path.startswith("/api/")
        and request.method in {"POST", "PUT", "PATCH"}
    ):
        if not content_length:
            return JSONResponse(
                status_code=411,
                content={"detail": "A request body length is required."},
            )
        content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
        if content_type != "application/json":
            return JSONResponse(
                status_code=415,
                content={"detail": "JSON content is required."},
            )
    if content_length:
        try:
            too_large = int(content_length) > settings.max_request_bytes
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request size."},
            )
        if too_large:
            return JSONResponse(
                status_code=413,
                content={"detail": "The request is too large."},
            )
    if request.method not in {"GET", "HEAD", "OPTIONS"} and request.url.path.startswith(
        "/api/"
    ):
        origin = request.headers.get("origin")
        if settings.production and not origin:
            return JSONResponse(
                status_code=403,
                content={"detail": "A trusted request origin is required."},
            )
        if origin and origin.rstrip("/") not in settings.allowed_origins:
            return JSONResponse(
                status_code=403,
                content={"detail": "This request origin is not allowed."},
            )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=()"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    if response.headers.get("content-type", "").startswith("text/html"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    if settings.production:
        websocket_origins = " ".join(
            origin.replace("https://", "wss://").replace("http://", "ws://")
            for origin in settings.allowed_origins
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'wasm-unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "media-src 'self' blob:; "
            f"connect-src 'self' {websocket_origins}; "
            "worker-src 'self' blob:; "
            "font-src 'self' data:; "
            "object-src 'none'; "
            "base-uri 'none'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "upgrade-insecure-requests"
        )
    if settings.cookie_secure:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    if request.url.path.startswith("/assets/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif request.url.path.startswith(("/models/", "/mediapipe/", "/favicon")):
        response.headers["Cache-Control"] = "public, max-age=604800"
    elif request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "model": MODEL_VERSION,
        "matchThreshold": MATCH_THRESHOLD,
        "mode": "MVP",
        "environment": settings.environment,
        "movementFallbackEnabled": settings.allow_movement_fallback,
    }


@app.get("/api/ready")
def readiness():
    try:
        with db.connect() as connection:
            connection.execute("SELECT 1").fetchone()
    except sqlite3.Error as error:
        raise HTTPException(status_code=503, detail="Database is not ready.") from error
    return {"ready": True, "model": MODEL_VERSION}


@app.post("/api/face/sessions")
def create_face_session(request: Request) -> dict[str, Any]:
    enforce_rate(f"session:{client_key(request)}", limit=20, window_seconds=60)
    prune_ephemeral_state()
    action = random.SystemRandom().choice(tuple(ACTION_LABELS))
    session_id = opaque_token()
    session = ScanSession(
        id=session_id,
        challenge_action=action,
        created_at=time.time(),
        client=client_key(request),
    )
    with scan_store_lock:
        scan_sessions[session_id] = session
    logger.info("scan session created action=%s", action)
    return {
        "sessionId": session_id,
        "expiresIn": SESSION_TTL_SECONDS,
        "challenge": {
            "step": 1,
            "action": action,
            "instruction": ACTION_LABELS[action],
        },
    }


async def send_event(websocket: WebSocket, event_type: str, **payload: Any) -> None:
    await websocket.send_json({"type": event_type, **payload})


async def run_face_task(function: Any, *args: Any) -> Any:
    async with face_task_lock:
        return await asyncio.to_thread(function, *args)


@app.websocket("/ws/face")
async def face_websocket(websocket: WebSocket, session_id: str) -> None:
    origin = websocket.headers.get("origin", "").rstrip("/")
    if (settings.production and not origin) or (
        origin and origin not in settings.allowed_origins
    ):
        await websocket.close(code=4403)
        return
    await websocket.accept()
    with scan_store_lock:
        session = scan_sessions.get(session_id)
    if not session or time.time() - session.created_at > SESSION_TTL_SECONDS:
        logger.info("scan connection rejected reason=expired_or_missing")
        await send_event(websocket, "session_expired")
        await websocket.close(code=4404)
        return
    if session.client != client_key(websocket):
        logger.warning("scan connection rejected reason=client_mismatch")
        await websocket.close(code=4403)
        return

    logger.info("scan connected action=%s", session.challenge_action)
    await send_event(
        websocket,
        "session_ready",
        sessionId=session.id,
        step=1,
        action=session.challenge_action,
        instruction=ACTION_LABELS[session.challenge_action],
        expiresIn=max(1, int(SESSION_TTL_SECONDS - (time.time() - session.created_at))),
    )
    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
            if time.time() - session.created_at > SESSION_TTL_SECONDS:
                await send_event(websocket, "session_expired")
                await websocket.close(code=4408)
                break
            payload = message.get("bytes")
            text = message.get("text")
            if payload:
                if len(payload) > settings.max_frame_bytes:
                    await send_event(
                        websocket, "error", message="Camera frame is too large."
                    )
                    await websocket.close(code=4409)
                    break
                now = time.time()
                if now - session.last_frame_processed < 0.07:
                    continue
                session.last_frame_processed = now
                session.latest_frame = payload
                if session.step == 3:
                    continue
                try:
                    image = await run_face_task(face_engine.decode_jpeg, payload)
                    detection = None
                    if (
                        session.step == 2
                        and session.lighting_ready
                        and session.lighting_started_at is None
                    ):
                        session.lighting_started_at = now
                        session.current_phase = "ambient"
                        logger.info("lighting schedule started on first frame")
                    if (
                        session.step != 2
                        or session.last_face_bbox is None
                        or now - session.last_face_detection_at >= 0.5
                    ):
                        detection = await run_face_task(face_engine.detect, image)
                        session.last_face_bbox = detection.bbox
                        session.last_face_detection_at = now
                        session.last_face_quality = detection.quality

                    if session.step == 2 and session.lighting_started_at is not None:
                        elapsed_ms = (time.time() - session.lighting_started_at) * 1000
                        next_phase = lighting_phase_at(elapsed_ms)
                        if next_phase != session.current_phase:
                            logger.info(
                                "lighting phase=%s samples=%s failures=%s",
                                next_phase,
                                len(session.lighting_samples.get(next_phase, [])),
                                session.lighting_detection_failures.get(next_phase, 0),
                            )
                        session.current_phase = next_phase

                    if (
                        session.step == 1
                        and session.reference_embedding is None
                        and detection is not None
                        and detection.quality["faces"] == 1
                        and float(detection.quality["areaRatio"]) >= 0.10
                    ):
                        session.reference_embedding = await run_face_task(
                            face_engine.embedding_from_detection, image, detection
                        )
                        logger.info("movement-stage face embedding captured")

                    if (
                        session.step == 2
                        and session.current_phase
                        and session.last_face_bbox is not None
                    ):
                        luminance, channels = brightness_statistics(
                            image, session.last_face_bbox
                        )
                        session.lighting_samples[session.current_phase].append(
                            (luminance, channels)
                        )
                        if len(session.lighting_samples[session.current_phase]) > 60:
                            session.lighting_samples[session.current_phase] = (
                                session.lighting_samples[session.current_phase][-60:]
                            )
                        if (
                            session.lighting_frame_payload is None
                            and session.current_phase in {"green", "blue", "white"}
                            and len(session.lighting_samples[session.current_phase])
                            >= 3
                            and detection is not None
                            and detection.quality["faces"] == 1
                        ):
                            session.lighting_frame_payload = payload
                            logger.info(
                                "lighting-stage embedding scheduled phase=%s",
                                session.current_phase,
                            )

                    quality_update = (
                        detection.quality if detection else session.last_face_quality
                    )
                    if quality_update and now - session.last_quality_sent > 0.45:
                        session.last_quality_sent = time.time()
                        await send_event(
                            websocket,
                            "frame_quality",
                            step=session.step,
                            phase=session.current_phase,
                            quality=quality_update,
                        )
                except FaceProcessingError as error:
                    if session.step == 2 and session.current_phase:
                        session.lighting_detection_failures[session.current_phase] += 1
                    if time.time() - session.last_quality_sent > 0.55:
                        session.last_quality_sent = time.time()
                        await send_event(
                            websocket,
                            "frame_quality",
                            step=session.step,
                            phase=session.current_phase,
                            quality={"faces": 0, "hint": error.message},
                        )
                continue
            if not text:
                continue
            if len(text.encode("utf-8")) > MAX_WEBSOCKET_TEXT_BYTES:
                await send_event(
                    websocket, "error", message="Scan command is too large."
                )
                await websocket.close(code=4409)
                break

            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                await send_event(websocket, "error", message="Invalid scan command.")
                continue

            event_type = event.get("type")
            if event_type == "action_detected":
                if session.step != 1:
                    await send_event(
                        websocket, "error", message="The action step is closed."
                    )
                    continue
                action = str(event.get("action", ""))
                confidence = float(event.get("confidence", 0))
                if action != session.challenge_action or confidence < 0.50:
                    logger.info(
                        "action rejected expected=%s received=%s confidence=%.3f",
                        session.challenge_action,
                        action,
                        confidence,
                    )
                    await send_event(
                        websocket, "action_retry", message="Try the shown action again."
                    )
                    continue
                if session.reference_embedding is None:
                    await send_event(
                        websocket,
                        "action_retry",
                        message="Hold still for one moment so the camera can find your face.",
                    )
                    continue
                logger.info(
                    "action accepted action=%s confidence=%.3f",
                    action,
                    confidence,
                )
                session.action_passed = True
                session.step = 2
                session.lighting_ready = False
                session.lighting_started_at = None
                session.current_phase = None
                await send_event(
                    websocket,
                    "action_passed",
                    step=2,
                    lighting={
                        "totalMs": LIGHT_TOTAL_MS,
                        "phases": [
                            {"name": phase, "durationMs": duration}
                            for phase, duration in LIGHT_SCHEDULE
                        ],
                    },
                )
            elif event_type == "lighting_ready":
                if session.step != 2 or session.lighting_ready:
                    continue
                session.lighting_ready = True
                session.lighting_started_at = time.time()
                session.current_phase = "ambient"
                logger.info("lighting schedule started after spoken instruction")
                await send_event(
                    websocket,
                    "lighting_started",
                    lighting={
                        "totalMs": LIGHT_TOTAL_MS,
                        "phases": [
                            {"name": phase, "durationMs": duration}
                            for phase, duration in LIGHT_SCHEDULE
                        ],
                    },
                )
            elif event_type == "lighting_complete":
                if session.step != 2:
                    continue
                lighting_elapsed_ms = (
                    (time.time() - session.lighting_started_at) * 1000
                    if session.lighting_started_at is not None
                    else 0
                )
                if lighting_elapsed_ms < LIGHT_TOTAL_MS - 150:
                    logger.info(
                        "lighting finished early elapsed_ms=%.0f required_ms=%s",
                        lighting_elapsed_ms,
                        LIGHT_TOTAL_MS,
                    )
                    await send_event(
                        websocket,
                        "scan_failed",
                        reason="The lighting challenge ended before all reflections were captured.",
                    )
                    session.step = 0
                    continue
                session.current_phase = None
                passed, details = face_engine.evaluate_lighting(
                    session.lighting_samples
                )
                details["detectionFailures"] = session.lighting_detection_failures
                logger.info("lighting-check passed=%s details=%s", passed, details)
                if not passed:
                    if settings.allow_movement_fallback and movement_fallback_allowed(
                        session.action_passed, details
                    ):
                        details["fallbackUsed"] = "movement_liveness"
                        logger.warning(
                            "lighting fallback used=movement_liveness "
                            "reason=no_measurable_screen_light"
                        )
                        await finalize_lighting_embedding(session)
                        session.step = 3
                        await send_event(
                            websocket,
                            "step_started",
                            step=3,
                            instruction=(
                                "The screen light could not be measured. "
                                "Continuing with movement verification."
                            ),
                            lighting=details,
                        )
                        continue
                    if any(count < 3 for count in details["counts"].values()):
                        failure_reason = (
                            "The camera missed part of the light check. "
                            "Keep your face in the frame and try again."
                        )
                    elif not details["brightnessChanged"]:
                        failure_reason = (
                            "The screen light did not reach your face. "
                            "Turn up the screen brightness, keep the screen facing you, and try again."
                        )
                    else:
                        failure_reason = (
                            "The camera did not detect the screen colors clearly. "
                            "Reduce other bright lights and try again."
                        )
                    await send_event(
                        websocket,
                        "scan_failed",
                        reason=failure_reason,
                    )
                    session.step = 0
                    continue
                await finalize_lighting_embedding(session)
                session.step = 3
                await send_event(
                    websocket,
                    "step_started",
                    step=3,
                    instruction="Hold still while the secure face template is calculated.",
                    lighting=details,
                )
            elif event_type == "capture_final":
                if session.step != 3 or not session.latest_frame:
                    await send_event(
                        websocket,
                        "scan_failed",
                        reason="No usable face frame is available.",
                    )
                    continue
                try:
                    embedding, detection = await run_face_task(
                        face_engine.extract_embedding, session.latest_frame
                    )
                except FaceProcessingError as error:
                    logger.info(
                        "embedding failed code=%s message=%s",
                        error.code,
                        error.message,
                    )
                    await send_event(websocket, "scan_failed", reason=error.message)
                    continue

                consistency_samples = [
                    session.reference_embedding,
                    session.lighting_embedding,
                    embedding,
                ]
                if any(sample is None for sample in consistency_samples):
                    await send_event(
                        websocket,
                        "scan_failed",
                        reason="We could not verify that the same face stayed in view. Please scan again.",
                    )
                    continue
                consistent, consistency_scores = check_face_consistency(
                    consistency_samples
                )
                logger.info(
                    "face consistency passed=%s threshold=%.2f scores=%s",
                    consistent,
                    FACE_CONSISTENCY_THRESHOLD,
                    [round(score, 4) for score in consistency_scores],
                )
                if not consistent:
                    await send_event(
                        websocket,
                        "scan_failed",
                        reason=(
                            "The face changed during the scan. "
                            "Keep the same person in view and try again."
                        ),
                    )
                    continue

                profile_image: bytes | None = None
                try:
                    profile_image = await run_face_task(
                        face_engine.create_profile_thumbnail,
                        session.latest_frame,
                        detection.bbox,
                    )
                except FaceProcessingError as error:
                    logger.info(
                        "profile thumbnail failed code=%s message=%s",
                        error.code,
                        error.message,
                    )

                ranked = rank_face_matches(embedding, db.all_face_records(), limit=3)
                logger.info(
                    "face ranking candidates=%s scores=%s",
                    len(ranked),
                    [round(score, 4) for _user_id, score in ranked],
                )

                now = time.time()
                candidate_accounts: list[dict[str, str]] = []
                if ranked and ranked[0][1] >= MATCH_THRESHOLD:
                    for user_id, _score in ranked:
                        user = db.get_user_by_id(user_id)
                        if not user:
                            continue
                        token = opaque_token()
                        with scan_store_lock:
                            candidate_tokens[token] = {
                                "user_id": user_id,
                                "embedding": embedding,
                                "expires_at": now + FACE_ATTEMPT_WINDOW,
                                "attempts": 0,
                                "client": session.client,
                            }
                        candidate_accounts.append(
                            {"token": token, "name": user["display_name"]}
                        )

                if candidate_accounts:
                    logger.info(
                        "face match result candidates=%s", len(candidate_accounts)
                    )
                    await send_event(
                        websocket,
                        "face_match",
                        step=4,
                        candidates=candidate_accounts,
                        expiresIn=FACE_ATTEMPT_WINDOW,
                        quality=detection.quality,
                    )
                else:
                    logger.info("face match result no_match")
                    ticket = opaque_token()
                    with scan_store_lock:
                        enrollment_tickets[ticket] = {
                            "embedding": embedding,
                            "profile_image": profile_image,
                            "expires_at": now + ENROLLMENT_TTL_SECONDS,
                            "client": session.client,
                        }
                    await send_event(
                        websocket,
                        "face_no_match",
                        step=4,
                        enrollmentTicket=ticket,
                        quality=detection.quality,
                    )
                session.step = 4
            elif event_type == "cancel":
                session.step = 0
                await send_event(websocket, "cancelled")
    except WebSocketDisconnect:
        pass
    finally:
        logger.info("scan connection closed")
        with scan_store_lock:
            scan_sessions.pop(session_id, None)
        face_engine.trim_memory()


@app.post("/api/auth/password")
def password_login(payload: PasswordLoginRequest, request: Request, response: Response):
    enforce_rate(f"password:{client_key(request)}", limit=8, window_seconds=60)
    now = time.time()
    with scan_store_lock:
        candidate = candidate_tokens.get(payload.candidate_token)
        if candidate and (
            candidate["expires_at"] < now or candidate["client"] != client_key(request)
        ):
            candidate_tokens.pop(payload.candidate_token, None)
            candidate = None
        if not candidate:
            raise HTTPException(
                status_code=401, detail="Face verification has expired. Scan again."
            )
        if candidate["attempts"] >= 5:
            candidate_tokens.pop(payload.candidate_token, None)
            raise HTTPException(
                status_code=429, detail="Too many password attempts. Scan again."
            )
        candidate["attempts"] += 1

    user = db.get_user_by_id(candidate["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="Sign-in could not be completed.")
    stored_embeddings = db.embeddings_for_user(user["id"])
    face_score = max(
        (cosine_similarity(candidate["embedding"], item) for item in stored_embeddings),
        default=-1.0,
    )
    password_ok = verify_password(user["password_hash"], payload.password)
    if face_score < MATCH_THRESHOLD or not password_ok:
        raise HTTPException(
            status_code=401, detail="Face or password verification failed."
        )

    with scan_store_lock:
        candidate_tokens.pop(payload.candidate_token, None)
    session_token = db.create_auth_session(user["id"])
    set_auth_cookie(response, session_token, request)
    return {"ok": True, "user": public_user(user)}


@app.post("/api/auth/name-login")
def name_login(payload: NameLoginRequest, request: Request, response: Response):
    enforce_rate(f"name-login:{client_key(request)}", limit=8, window_seconds=60)
    user = db.get_user_by_display_name(payload.display_name.strip())
    if not user or not verify_password(user["password_hash"], payload.password):
        raise HTTPException(status_code=401, detail="Name or password is not correct.")
    session_token = db.create_auth_session(user["id"])
    set_auth_cookie(response, session_token, request)
    return {"ok": True, "user": public_user(user)}


@app.get("/api/admin/users")
def admin_list_users(request: Request):
    require_admin_session(request)
    users = db.list_users()
    return {
        "users": [
            {
                "id": user["id"],
                "name": user["display_name"],
                "role": user["role"],
                "mustChangePassword": bool(user["must_change_password"]),
                "hasFace": bool(user["has_face"]),
                "hasPhoto": bool(user["has_photo"]),
                "createdAt": user["created_at"],
            }
            for user in users
        ]
    }


@app.get("/api/admin/users/{user_id}/photo")
def admin_user_photo(user_id: str, request: Request):
    require_admin_session(request)
    image = db.profile_image_for_user(user_id)
    if not image:
        raise HTTPException(status_code=404, detail="Profile photo not found.")
    return Response(
        content=image,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "private, no-store",
            "Cross-Origin-Resource-Policy": "same-origin",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.patch("/api/admin/users/{user_id}/role")
def admin_update_role(
    user_id: str,
    payload: AdminRoleUpdateRequest,
    request: Request,
):
    current_user = require_admin_session(request)
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if current_user["id"] == user_id and payload.role != current_user["role"]:
        raise HTTPException(
            status_code=400,
            detail="An administrator cannot change their own role.",
        )
    if user["role"] == "admin" and payload.role == "user" and db.count_admins() <= 1:
        raise HTTPException(
            status_code=400,
            detail="At least one administrator must remain.",
        )
    db.update_role(user_id, payload.role)
    return {"ok": True}


@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(user_id: str, request: Request):
    current_user = require_admin_session(request)
    if current_user["id"] == user_id:
        raise HTTPException(
            status_code=400,
            detail="Use account deletion for the signed-in administrator.",
        )
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user["role"] == "admin" and db.count_admins() <= 1:
        raise HTTPException(
            status_code=400,
            detail="At least one administrator must remain.",
        )
    db.delete_user(user_id)
    return {"ok": True}


@app.post("/api/admin/password")
def admin_change_password(
    payload: AdminPasswordChangeRequest,
    request: Request,
    response: Response,
):
    user = require_admin_session(request, allow_password_change=True)
    if not verify_password(user["password_hash"], payload.current_password):
        raise HTTPException(status_code=401, detail="Current password is not correct.")
    if payload.new_password == "admin123":
        raise HTTPException(
            status_code=400,
            detail="Choose a password different from the default password.",
        )
    errors = list(strong_password_errors(payload.new_password))
    if errors:
        raise HTTPException(status_code=400, detail=errors[0])
    db.update_password(
        user["id"],
        hash_password(payload.new_password),
        must_change_password=False,
    )
    refreshed = db.get_user_by_id(user["id"])
    session_token = db.create_auth_session(user["id"])
    set_auth_cookie(response, session_token, request)
    return {"ok": True, "user": public_user(refreshed)}


@app.post("/api/auth/register")
def register(payload: RegistrationRequest, request: Request, response: Response):
    enforce_rate(f"register:{client_key(request)}", limit=6, window_seconds=300)
    validate_registration(payload)
    display_name = payload.display_name.strip()
    expires_at = 0.0
    with scan_store_lock:
        ticket = enrollment_tickets.get(payload.enrollment_ticket)
        if ticket:
            expires_at = float(ticket["expires_at"])
        if (
            not ticket
            or expires_at < time.time()
            or ticket.get("claimed")
            or ticket.get("client") != client_key(request)
        ):
            logger.info("registration rejected reason=enrollment_ticket_unavailable")
            raise HTTPException(
                status_code=401, detail="The face enrollment expired. Scan again."
            )
        # Reserve the one-time enrollment while account creation is in progress.
        # Failed validation or duplicate-name attempts release it for correction.
        ticket["claimed"] = True

    registered = False
    try:
        if db.get_user_by_display_name(display_name):
            raise HTTPException(
                status_code=409,
                detail="That name is already used. Add a nickname or number.",
            )
        try:
            user_id = db.create_user(
                display_name=display_name,
                password_hash=hash_password(payload.password),
                embedding=ticket["embedding"],
                profile_image=ticket.get("profile_image"),
                model_version=MODEL_VERSION,
                consent_version=BIOMETRIC_CONSENT_VERSION,
                consented_at=iso_now(),
                terms_version=TERMS_VERSION,
                terms_accepted_at=iso_now(),
                security_answers=[
                    (item.question, hash_answer(item.answer))
                    for item in payload.security_answers
                ],
            )
        except sqlite3.IntegrityError as error:
            raise HTTPException(
                status_code=409,
                detail="That name is already used. Add a nickname or number.",
            ) from error
        registered = True
    finally:
        with scan_store_lock:
            if registered:
                enrollment_tickets.pop(payload.enrollment_ticket, None)
            elif enrollment_tickets.get(payload.enrollment_ticket) is ticket:
                ticket.pop("claimed", None)

    user = db.get_user_by_id(user_id)
    session_token = db.create_auth_session(user_id)
    set_auth_cookie(response, session_token, request)
    return {"ok": True, "user": public_user(user)}


@app.post("/api/auth/recovery/questions")
def recovery_questions(payload: RecoveryQuestionsRequest, request: Request):
    enforce_rate(f"recovery:{client_key(request)}", limit=8, window_seconds=300)
    user = db.get_user_by_display_name(payload.display_name.strip())
    if not user:
        return {"questions": ["What is the answer to your security question?"]}
    rows = db.security_answers_for_user(user["id"])
    return {"questions": [row["question"] for row in rows[:1]]}


@app.post("/api/auth/recovery/reset")
def recovery_reset(payload: RecoveryResetRequest, request: Request):
    enforce_rate(f"recovery-reset:{client_key(request)}", limit=6, window_seconds=300)
    errors = list(strong_password_errors(payload.new_password))
    if errors:
        raise HTTPException(status_code=400, detail=errors[0])
    user = db.get_user_by_display_name(payload.display_name.strip())
    if not user:
        raise HTTPException(
            status_code=401, detail="Recovery details could not be verified."
        )
    stored = db.security_answers_for_user(user["id"])
    if not stored or len(payload.answers) != 1:
        raise HTTPException(
            status_code=401, detail="Recovery details could not be verified."
        )
    supplied = payload.answers[0]
    expected = stored[0]
    if supplied.question != expected["question"] or not verify_answer(
        expected["answer_hash"], supplied.answer
    ):
        raise HTTPException(
            status_code=401, detail="Recovery details could not be verified."
        )
    db.update_password(user["id"], hash_password(payload.new_password))
    return {"ok": True, "message": "Password updated. Return to face sign-in."}


@app.get("/api/auth/me")
def current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not signed in.")
    user = db.user_for_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired.")
    return {"user": public_user(user)}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        db.delete_auth_session(token)
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/",
        secure=settings.cookie_secure,
        samesite="strict",
    )
    return {"ok": True}


@app.post("/api/auth/account/delete")
def delete_account(
    payload: DeleteAccountRequest,
    request: Request,
    response: Response,
):
    enforce_rate(f"delete-account:{client_key(request)}", limit=5, window_seconds=300)
    token = request.cookies.get(SESSION_COOKIE_NAME)
    user = db.user_for_session(token) if token else None
    if not token or not user:
        raise HTTPException(
            status_code=401, detail="Sign in again before deleting the account."
        )
    if not verify_password(user["password_hash"], payload.password):
        raise HTTPException(status_code=401, detail="Password verification failed.")
    db.delete_user(user["id"])
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/",
        secure=settings.cookie_secure,
        samesite="strict",
    )
    return {"ok": True}


if DIST_DIR.exists():

    @app.get("/admin")
    @app.get("/admin/")
    def admin_page():
        return FileResponse(DIST_DIR / "index.html")

    @app.get("/faceScanner")
    @app.get("/faceScanner/")
    def face_scanner_page():
        return FileResponse(DIST_DIR / "index.html")

    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="frontend")
else:

    @app.get("/")
    def development_root():
        return FileResponse(ROOT / "index.html")
