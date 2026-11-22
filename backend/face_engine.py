from __future__ import annotations

import ctypes
import math
import sys
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DETECTION_MODEL = ROOT / "backend" / "models" / "face_detection_yunet_2023mar.onnx"
RECOGNITION_MODEL = ROOT / "backend" / "models" / "face_recognition_sface_2021dec.onnx"
MODEL_VERSION = "sface-2021dec/yunet-2023mar"
MATCH_THRESHOLD = 0.40
CANDIDATE_THRESHOLD = 0.30
FACE_CONSISTENCY_THRESHOLD = 0.35


class FaceProcessingError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class DetectionResult:
    face: np.ndarray
    bbox: tuple[int, int, int, int]
    quality: dict[str, float | int | str]


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    a = np.asarray(list(left), dtype=np.float32)
    b = np.asarray(list(right), dtype=np.float32)
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denominator == 0:
        return -1.0
    return float(np.dot(a, b) / denominator)


def rank_face_matches(
    embedding: list[float],
    records: Iterable[tuple[str, list[float]]],
    *,
    threshold: float = CANDIDATE_THRESHOLD,
    limit: int = 3,
) -> list[tuple[str, float]]:
    best_by_user: dict[str, float] = {}
    for user_id, stored_embedding in records:
        score = cosine_similarity(embedding, stored_embedding)
        if score > best_by_user.get(user_id, -1.0):
            best_by_user[user_id] = score
    ranked = sorted(best_by_user.items(), key=lambda item: item[1], reverse=True)
    return [(user_id, score) for user_id, score in ranked[:limit] if score >= threshold]


def check_face_consistency(
    embeddings: Iterable[list[float]],
    *,
    threshold: float = FACE_CONSISTENCY_THRESHOLD,
) -> tuple[bool, list[float]]:
    samples = list(embeddings)
    if len(samples) < 3:
        return False, []
    scores: list[float] = []
    for index, left in enumerate(samples):
        for right in samples[index + 1 :]:
            scores.append(cosine_similarity(left, right))
    return bool(scores) and min(scores) >= threshold, scores


def brightness_statistics(
    image: np.ndarray, bbox: tuple[int, int, int, int]
) -> tuple[float, tuple[float, float, float]]:
    height, width = image.shape[:2]
    x, y, w, h = bbox
    x1 = max(0, min(width - 1, int(x)))
    y1 = max(0, min(height - 1, int(y)))
    x2 = max(x1 + 1, min(width, int(x + w)))
    y2 = max(y1 + 1, min(height, int(y + h)))
    roi = image[y1:y2, x1:x2]
    means = tuple(float(value) for value in roi.mean(axis=(0, 1)))
    blue, green, red = means
    luminance = 0.114 * blue + 0.587 * green + 0.299 * red
    return luminance, (blue, green, red)


class FaceEngine:
    def __init__(self) -> None:
        if not DETECTION_MODEL.exists() or not RECOGNITION_MODEL.exists():
            raise RuntimeError("Face model files are missing from backend/models.")
        cv2.setNumThreads(1)
        cv2.ocl.setUseOpenCL(False)
        self.detector = cv2.FaceDetectorYN.create(
            str(DETECTION_MODEL),
            "",
            (320, 320),
            score_threshold=0.82,
            nms_threshold=0.3,
            top_k=5000,
        )
        self.recognizer = cv2.FaceRecognizerSF.create(str(RECOGNITION_MODEL), "")
        self.lock = threading.RLock()

    @staticmethod
    def trim_memory() -> None:
        if not sys.platform.startswith("linux"):
            return
        try:
            libc = ctypes.CDLL(None)
            libc.malloc_trim(0)
        except (AttributeError, OSError):
            pass

    @staticmethod
    def decode_jpeg(payload: bytes) -> np.ndarray:
        image = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise FaceProcessingError(
                "invalid_frame", "The camera frame could not be decoded."
            )
        return image

    def detect(self, image: np.ndarray) -> DetectionResult:
        height, width = image.shape[:2]
        with self.lock:
            self.detector.setInputSize((width, height))
            faces = self.detector.detect(image)[1]
        if faces is None or len(faces) == 0:
            raise FaceProcessingError("no_face", "No face was detected.")

        face = max(faces, key=lambda item: float(item[2] * item[3]))
        x, y, w, h = (float(value) for value in face[:4])
        area_ratio = (w * h) / float(width * height)
        center_x = (x + w / 2) / width
        center_y = (y + h / 2) / height
        luminance, _ = brightness_statistics(image, (int(x), int(y), int(w), int(h)))
        quality: dict[str, float | int | str] = {
            "faces": len(faces),
            "areaRatio": round(area_ratio, 3),
            "centerX": round(center_x, 3),
            "centerY": round(center_y, 3),
            "brightness": round(luminance, 1),
        }
        if len(faces) != 1:
            quality["hint"] = "Keep only one face in the frame."
        elif area_ratio < 0.10:
            quality["hint"] = "Move closer to the camera."
        elif luminance < 35:
            quality["hint"] = "Add some light to your face."
        elif luminance > 220:
            quality["hint"] = "Reduce direct light or glare."
        else:
            quality["hint"] = "Face detected. Follow the action on screen."
        return DetectionResult(
            face=face, bbox=(int(x), int(y), int(w), int(h)), quality=quality
        )

    def extract_embedding(self, payload: bytes) -> tuple[list[float], DetectionResult]:
        image = self.decode_jpeg(payload)
        detection = self.detect(image)
        return self.embedding_from_detection(image, detection), detection

    def embedding_from_detection(
        self,
        image: np.ndarray,
        detection: DetectionResult,
    ) -> list[float]:
        if detection.quality["faces"] != 1:
            raise FaceProcessingError("multiple_faces", "Exactly one face is required.")
        if float(detection.quality["areaRatio"]) < 0.08:
            raise FaceProcessingError("face_too_small", "Move closer to the camera.")

        with self.lock:
            aligned = self.recognizer.alignCrop(image, detection.face)
            feature = self.recognizer.feature(aligned)
        vector = np.asarray(feature, dtype=np.float32).reshape(-1)
        norm = float(np.linalg.norm(vector))
        if not math.isfinite(norm) or norm == 0:
            raise FaceProcessingError(
                "embedding_failed", "Face features could not be calculated."
            )
        vector /= norm
        return vector.tolist()

    def inspect_frame(self, payload: bytes) -> DetectionResult:
        return self.detect(self.decode_jpeg(payload))

    @staticmethod
    def create_profile_thumbnail(
        payload: bytes,
        bbox: tuple[int, int, int, int],
        size: int = 256,
    ) -> bytes:
        image = FaceEngine.decode_jpeg(payload)
        height, width = image.shape[:2]
        x, y, face_width, face_height = bbox
        center_x = x + face_width / 2
        center_y = y + face_height / 2
        crop_size = int(max(face_width, face_height) * 1.55)
        left = max(0, min(width - crop_size, int(center_x - crop_size / 2)))
        top = max(0, min(height - crop_size, int(center_y - crop_size / 2)))
        right = min(width, left + crop_size)
        bottom = min(height, top + crop_size)
        crop = image[top:bottom, left:right]
        if crop.size == 0:
            raise FaceProcessingError(
                "thumbnail_failed", "Profile image could not be created."
            )
        thumbnail = cv2.resize(crop, (size, size), interpolation=cv2.INTER_AREA)
        encoded, buffer = cv2.imencode(
            ".jpg",
            thumbnail,
            [cv2.IMWRITE_JPEG_QUALITY, 84],
        )
        if not encoded:
            raise FaceProcessingError(
                "thumbnail_failed", "Profile image could not be encoded."
            )
        return buffer.tobytes()

    @staticmethod
    def evaluate_lighting(
        samples: dict[str, list[tuple[float, tuple[float, float, float]]]],
    ) -> tuple[bool, dict[str, object]]:
        expected = ("ambient", "red", "green", "blue", "white")
        counts = {phase: len(samples.get(phase, [])) for phase in expected}
        if any(counts[phase] < 3 for phase in expected):
            return False, {"reason": "Missing lighting samples.", "counts": counts}

        phase_luma = {
            phase: float(np.mean([sample[0] for sample in samples[phase]]))
            for phase in expected
        }
        illuminated = [phase_luma[phase] for phase in ("red", "green", "blue", "white")]
        luma_range = max(illuminated) - min(illuminated)
        ambient_delta = max(abs(value - phase_luma["ambient"]) for value in illuminated)
        phase_channels = {
            phase: tuple(
                float(np.mean([sample[1][channel] for sample in samples[phase]]))
                for channel in range(3)
            )
            for phase in expected
        }
        color_dominance = {
            phase: {
                "red": channels[2] - (channels[0] + channels[1]) / 2,
                "green": channels[1] - (channels[0] + channels[2]) / 2,
                "blue": channels[0] - (channels[1] + channels[2]) / 2,
            }
            for phase, channels in phase_channels.items()
        }
        correct_color_order = sum(
            color_dominance[color][color]
            > max(
                color_dominance[color][other]
                for other in ("red", "green", "blue")
                if other != color
            )
            and color_dominance[color][color] >= 0.5
            for color in ("red", "green", "blue")
        )
        white_delta = phase_luma["white"] - phase_luma["ambient"]
        phase_luma_delta = {
            phase: phase_luma[phase] - phase_luma["ambient"]
            for phase in ("red", "green", "blue")
        }
        responsive_color_phases = sum(
            abs(delta) >= 5.0 for delta in phase_luma_delta.values()
        )
        brightness_changed = luma_range >= 4.0 or abs(white_delta) >= 6.0
        passed = brightness_changed and (
            correct_color_order >= 2 or responsive_color_phases >= 2
        )
        return passed, {
            "counts": counts,
            "phaseLuma": {
                phase: round(value, 2) for phase, value in phase_luma.items()
            },
            "lumaRange": round(luma_range, 2),
            "ambientDelta": round(ambient_delta, 2),
            "whiteDelta": round(white_delta, 2),
            "phaseLumaDelta": {
                phase: round(value, 2) for phase, value in phase_luma_delta.items()
            },
            "responsiveColorPhases": responsive_color_phases,
            "colorDominance": {
                phase: {color: round(value, 2) for color, value in scores.items()}
                for phase, scores in color_dominance.items()
            },
            "correctColorOrder": correct_color_order,
            "brightnessChanged": brightness_changed,
        }


face_engine = FaceEngine()
