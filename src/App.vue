<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  watch
} from "vue";
import { localeOptions, messages, resolveLocale } from "./locales";
import { termsByLocale, termsVersion } from "./terms";

const APP_BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

function appPath(path) {
  return `${APP_BASE}${path}`;
}

function redirectAdmin(user) {
  if (user?.role !== "admin") return false;
  window.location.assign(appPath("/admin"));
  return true;
}

const screen = ref("welcome");
const authParams = new URLSearchParams(window.location.search);
const autoStartScan = authParams.get("autostart") === "1";
const returnTo = (() => {
  const value = authParams.get("returnTo");
  if (!value) return "";
  try {
    const target = new URL(value);
    if (!["http:", "https:"].includes(target.protocol)) return "";
    if (target.hostname !== window.location.hostname) return "";
    return target.href;
  } catch {
    return "";
  }
})();
const modelStatusKey = ref("sensor.idle");
const cameraConnected = ref(false);
const step = ref(1);
const action = ref("");
const instructionKey = ref("scanner.starting");
const quality = ref(null);
const error = ref("");
const busy = ref(false);
const wsConnected = ref(false);
function initialVoiceSetting() {
  try {
    return localStorage.getItem("facesignup-voice") !== "off";
  } catch {
    return true;
  }
}

const voiceEnabled = ref(initialVoiceSetting());
const currentPhase = ref(null);
const candidates = ref([]);
const selectedCandidate = ref(null);
const candidateToken = ref("");
const enrollmentTicket = ref("");
const signedInUser = ref(null);
const authMethod = ref("");
const loginPassword = ref("");
const nameLogin = reactive({ displayName: "", password: "" });
const statusKey = ref("scanner.keepFace");
const recoveryStage = ref("identity");
const recoveryName = ref("");
const recoveryQuestions = ref([]);
const recoveryAnswer = ref("");
const recoveryPassword = ref("");
const showDeleteAccount = ref(false);
const deletePassword = ref("");
const showTerms = ref(false);

const registration = reactive({
  displayName: "",
  password: "",
  confirmPassword: "",
  agreementAccepted: false,
  firstQuestion: "",
  firstAnswer: ""
});

const videoRef = ref(null);
const landmarkCanvasRef = ref(null);
const landmarkDetected = ref(false);
const workCanvas = document.createElement("canvas");

function detectLocale() {
  let saved = null;
  try {
    saved = localStorage.getItem("facesignup-language");
  } catch {
    // Storage may be blocked in privacy-restricted browser contexts.
  }
  return resolveLocale(navigator.languages || [navigator.language], saved);
}

const locale = ref(detectLocale());
const selectedSpeechLocale = computed(
  () => localeOptions.find((option) => option.value === locale.value)?.speech || "en-US"
);
const localizedTerms = computed(() => termsByLocale[locale.value] || termsByLocale.en);
const instruction = computed(() => t(instructionKey.value));
const modelStatus = computed(() => t(modelStatusKey.value));
const cameraStatus = computed(() => (cameraConnected.value ? t("camera.live") : ""));

function t(key, values = {}) {
  const dictionary = messages[locale.value] || messages.en;
  let text = dictionary[key] || messages.en[key] || key;
  for (const [name, value] of Object.entries(values)) {
    text = text.replaceAll(`{${name}}`, String(value));
  }
  return text;
}

const serverMessageKeys = {
  "The camera missed part of the light check. Keep your face in the frame and try again.":
    "server.lightingMissing",
  "The screen light did not reach your face. Turn up the screen brightness, keep the screen facing you, and try again.":
    "server.lightingNoSignal",
  "The camera did not detect the screen colors clearly. Reduce other bright lights and try again.":
    "server.lightingColor",
  "The lighting challenge ended before all reflections were captured.":
    "server.earlyLight",
  "The face changed during the scan. Keep the same person in view and try again.":
    "server.faceChanged",
  "We could not verify that the same face stayed in view. Please scan again.":
    "server.faceMissing",
  "No usable face frame is available.": "server.noFrame",
  "The scan expired.": "server.expired",
  "Face or security answer verification failed.": "error.answerFailed",
  "Face or password verification failed.": "error.loginFailed",
  "Please agree to the Terms of Service.": "error.terms",
  "Explicit consent is required before storing a face template.": "error.consent",
  "Name or password is not correct.": "error.loginFailed",
  "That name is already used. Add a nickname or number.": "error.nameTaken",
  "Recovery details could not be verified.": "error.recoveryFailed",
  "Too many attempts. Wait and try again.": "error.tooMany",
  "Too many security-answer attempts. Scan again.": "error.tooMany",
  "Too many password attempts. Scan again.": "error.tooMany",
  "Face verification has expired. Scan again.": "error.enrollmentExpired",
  "The face enrollment expired. Scan again.": "error.enrollmentExpired",
  "Password verification failed.": "error.deleteFailed",
  "Sign in again before deleting the account.": "error.loginFailed"
};

function localizeServerMessage(message) {
  const normalized = String(message || "").trim();
  const key = serverMessageKeys[normalized];
  if (key) return t(key);
  if (locale.value === "en") return normalized || t("error.generic");
  return t("error.generic");
}

function localizeCaughtError(caughtError) {
  if (
    ["NotAllowedError", "NotFoundError", "NotReadableError", "SecurityError"].includes(
      caughtError?.name
    )
  ) {
    return t("error.camera");
  }
  return localizeServerMessage(caughtError?.message);
}

const cameraView = computed(() => screen.value === "scanner" || screen.value === "verifying");
const stepText = computed(() => {
  if (step.value === 1) return t("step.movement");
  if (step.value === 2) return t("step.light");
  if (step.value === 3) return t("step.face");
  return t("step.verify");
});
const lightTint = computed(() => {
  const colors = {
    red: "rgb(255, 17, 30)",
    green: "rgb(0, 255, 88)",
    blue: "rgb(0, 72, 255)",
    white: "rgb(255, 255, 250)"
  };
  return colors[currentPhase.value] || "transparent";
});
const qualityText = computed(() => {
  if (statusKey.value !== "scanner.keepFace" && quality.value) {
    return t(statusKey.value);
  }
  if (!quality.value) return t("scanner.keepFace");
  if (quality.value.faces !== 1) return t("quality.oneFace");
  if (Number(quality.value.areaRatio) < 0.1) return t("quality.moveCloser");
  if (Number(quality.value.brightness) < 35) return t("quality.addLight");
  if (Number(quality.value.brightness) > 220) return t("quality.reduceLight");
  return t("quality.faceDetected");
});
const cameraNotice = computed(() => {
  if (!quality.value && statusKey.value === "scanner.keepFace") return "";
  if (statusKey.value !== "scanner.keepFace") return t(statusKey.value);
  if (quality.value.faces === 0) return t("scanner.holdMoment");
  if (quality.value.faces > 1) return t("quality.oneFace");
  if (Number(quality.value.areaRatio) < 0.1) return t("quality.moveCloser");
  if (Number(quality.value.brightness) < 35) return t("quality.addLight");
  if (Number(quality.value.brightness) > 220) return t("quality.reduceLight");
  return "";
});

let faceLandmarker = null;
let faceSensorPromise = null;
let mediaStream = null;
let socket = null;
let frameLoop = 0;
let lastVideoTime = -1;
let lastFrameSent = 0;
let lastActionSent = 0;
let actionBaselineYaw = null;
let lightingRun = 0;
let scanGeneration = 0;
let pauseFrameUpload = false;
let lightingPromptPending = false;
let pendingLighting = null;
let voiceUnlocked = false;
let lastSpokenText = "";
let lastSpokenAt = 0;
let faceLandmarkConnections = null;
let smoothedFaceLandmarks = null;

const spokenScreenKeys = {
  welcome: "welcome.subtitle",
  "name-login": "nameLogin.spoken",
  register: "register.spoken",
  recovery: "recovery.spoken",
  success: "success.spoken"
};
const successMessage = computed(() => {
  if (authMethod.value === "face-password") return t("success.facePassword");
  if (authMethod.value === "name-password") return t("success.namePassword");
  if (authMethod.value === "registered") return t("success.registered");
  return t("success.session");
});

function speakText(text, force = false) {
  const normalized = String(text || "").trim();
  if (
    !voiceEnabled.value ||
    !voiceUnlocked ||
    !normalized ||
    !("speechSynthesis" in window) ||
    typeof SpeechSynthesisUtterance === "undefined"
  ) {
    return Promise.resolve(false);
  }
  const now = Date.now();
  if (!force && normalized === lastSpokenText && now - lastSpokenAt < 2500) {
    return Promise.resolve(false);
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(normalized);
  utterance.lang = selectedSpeechLocale.value;
  const voices = window.speechSynthesis.getVoices();
  const exactVoice = voices.find(
    (voice) => voice.lang.toLowerCase() === selectedSpeechLocale.value.toLowerCase()
  );
  const baseLanguage = selectedSpeechLocale.value.split("-")[0].toLowerCase();
  utterance.voice =
    exactVoice ||
    voices.find((voice) => voice.lang.toLowerCase().startsWith(`${baseLanguage}-`)) ||
    null;
  utterance.rate = 0.88;
  utterance.pitch = 1;
  utterance.volume = 1;
  lastSpokenText = normalized;
  lastSpokenAt = now;
  return new Promise((resolve) => {
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      window.clearTimeout(timeout);
      resolve(true);
    };
    const timeout = window.setTimeout(
      finish,
      Math.min(12000, Math.max(1800, normalized.length * 90))
    );
    utterance.onend = finish;
    utterance.onerror = finish;
    try {
      window.speechSynthesis.speak(utterance);
    } catch {
      finish();
    }
  });
}

function toggleVoice() {
  voiceEnabled.value = !voiceEnabled.value;
  voiceUnlocked = true;
  localStorage.setItem("facesignup-voice", voiceEnabled.value ? "on" : "off");
  if (voiceEnabled.value) {
    speakText(t("voice.enabled"), true);
  } else if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

function changeLanguage() {
  try {
    localStorage.setItem("facesignup-language", locale.value);
  } catch {
    // Ignore storage restrictions.
  }
  voiceUnlocked = true;
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  speakText(t("language.changed"), true);
}

async function loadFaceSensor() {
  if (faceLandmarker) return faceLandmarker;
  if (faceSensorPromise) return faceSensorPromise;
  faceSensorPromise = (async () => {
    try {
      modelStatusKey.value = "sensor.loading";
      const { FaceLandmarker, FilesetResolver } = await import("@mediapipe/tasks-vision");
      faceLandmarkConnections = FaceLandmarker.FACE_LANDMARKS_CONTOURS;
      const fileset = await FilesetResolver.forVisionTasks(appPath("/mediapipe/wasm"));
      const options = {
        baseOptions: {
          modelAssetPath: appPath("/models/face_landmarker.task"),
          delegate: "GPU"
        },
        runningMode: "VIDEO",
        numFaces: 1,
        outputFaceBlendshapes: true,
        outputFacialTransformationMatrixes: true
      };
      try {
        faceLandmarker = await FaceLandmarker.createFromOptions(fileset, options);
      } catch {
        faceLandmarker = await FaceLandmarker.createFromOptions(fileset, {
          ...options,
          baseOptions: { ...options.baseOptions, delegate: "CPU" }
        });
      }
      modelStatusKey.value = "sensor.ready";
      return faceLandmarker;
    } catch (sensorError) {
      console.error(sensorError);
      modelStatusKey.value = "sensor.unavailable";
      error.value = t("error.sensor");
      return null;
    } finally {
      faceSensorPromise = null;
    }
  })();
  return faceSensorPromise;
}

async function api(path, options = {}) {
  const requestPath = path.startsWith("/") ? appPath(path) : path;
  const response = await fetch(requestPath, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message =
      typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
          ? data.detail
              .map((item) => `${item.loc?.slice(-1)[0] || "Form"}: ${item.msg}`)
              .join(" ")
          : `Request failed with status ${response.status}.`;
    throw new Error(message);
  }
  return data;
}

async function checkExistingSession() {
  try {
    const data = await api("/api/auth/me");
    signedInUser.value = data.user;
    authMethod.value = "session";
    if (redirectAdmin(data.user)) return;
    screen.value = "success";
  } catch {
    screen.value = "welcome";
    if (autoStartScan) {
      window.setTimeout(() => {
        if (screen.value === "welcome" && !busy.value) startScan();
      }, 120);
    }
  }
}

async function openCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("This browser does not provide camera access.");
  }
  mediaStream = await navigator.mediaDevices.getUserMedia({
    audio: false,
    video: {
      facingMode: "user",
      width: { ideal: 1280 },
      height: { ideal: 720 },
      frameRate: { ideal: 24, max: 30 }
    }
  });
  if (!videoRef.value) throw new Error("Scanner video is unavailable.");
  videoRef.value.srcObject = mediaStream;
  await videoRef.value.play();
  cameraConnected.value = true;
}

function connectSocket(sessionId) {
  return new Promise((resolve, reject) => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    socket = new WebSocket(
      `${protocol}://${window.location.host}${appPath("/ws/face")}?session_id=${encodeURIComponent(sessionId)}`
    );
    socket.binaryType = "arraybuffer";
    const timeout = window.setTimeout(() => reject(new Error("Scan session timed out.")), 10000);
    socket.addEventListener("open", () => {
      window.clearTimeout(timeout);
      wsConnected.value = true;
      resolve();
    });
    socket.addEventListener("message", handleSocketMessage);
    socket.addEventListener("close", () => {
      wsConnected.value = false;
    });
    socket.addEventListener("error", () => {
      window.clearTimeout(timeout);
      reject(new Error("The secure scan connection failed."));
    });
  });
}

function sendEvent(payload) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(payload));
  }
}

async function startScan() {
  const run = ++scanGeneration;
  clearError();
  busy.value = true;
  voiceUnlocked = true;
  if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
    document.documentElement.requestFullscreen({ navigationUI: "hide" }).catch(() => {});
  }
  step.value = 1;
  quality.value = null;
  candidates.value = [];
  selectedCandidate.value = null;
  candidateToken.value = "";
  enrollmentTicket.value = "";
  loginPassword.value = "";
  lastActionSent = 0;
  actionBaselineYaw = null;
  pauseFrameUpload = false;
  lightingPromptPending = false;
  pendingLighting = null;
  smoothedFaceLandmarks = null;
  landmarkDetected.value = false;
  statusKey.value = "scanner.keepFace";
  screen.value = "scanner";
  await nextTick();
  instructionKey.value = "scanner.starting";
  try {
    const sensorPromise = loadFaceSensor();
    await openCamera();
    if (run !== scanGeneration) {
      mediaStream?.getTracks().forEach((track) => track.stop());
      mediaStream = null;
      cameraConnected.value = false;
      return;
    }
    instructionKey.value = "scanner.preparing";
    await sensorPromise;
    if (!faceLandmarker) throw new Error("The local face sensor is unavailable.");
    const session = await api("/api/face/sessions", { method: "POST", body: "{}" });
    action.value = session.challenge.action;
    instructionKey.value = `action.${session.challenge.action}`;
    await connectSocket(session.sessionId);
    startVideoLoop();
  } catch (scanError) {
    error.value = localizeCaughtError(scanError);
    screen.value = "failed";
    stopScan(false);
  } finally {
    if (run === scanGeneration) busy.value = false;
  }
}

function startVideoLoop() {
  cancelAnimationFrame(frameLoop);
  const processFrame = () => {
    if (!cameraView.value) return;
    const video = videoRef.value;
    if (video && video.readyState >= 2) {
      try {
        if (video.currentTime !== lastVideoTime) {
          lastVideoTime = video.currentTime;
          const result = faceLandmarker?.detectForVideo(video, performance.now());
          drawFaceLandmarks(result);
          inspectAction(result);
        }
        sendFrame();
      } catch (frameError) {
        console.debug("Frame skipped", frameError);
      }
    }
    frameLoop = requestAnimationFrame(processFrame);
  };
  frameLoop = requestAnimationFrame(processFrame);
}

function sendFrame() {
  const video = videoRef.value;
  if (pauseFrameUpload || !video || !socket || socket.readyState !== WebSocket.OPEN) {
    return;
  }
  const now = performance.now();
  if (now - lastFrameSent < 100) return;
  lastFrameSent = now;
  workCanvas.width = 640;
  workCanvas.height = Math.round(
    (video.videoHeight / Math.max(1, video.videoWidth)) * workCanvas.width
  );
  const context = workCanvas.getContext("2d", { alpha: false });
  context.drawImage(video, 0, 0, workCanvas.width, workCanvas.height);
  workCanvas.toBlob(
    async (blob) => {
      if (!blob || !socket || socket.readyState !== WebSocket.OPEN) return;
      socket.send(await blob.arrayBuffer());
    },
    "image/jpeg",
    0.7
  );
}

function blendScores(result) {
  const categories = result?.faceBlendshapes?.[0]?.categories || [];
  return Object.fromEntries(categories.map((entry) => [entry.categoryName, entry.score]));
}

function faceYaw(landmarks) {
  const leftCheek = landmarks?.[234];
  const rightCheek = landmarks?.[454];
  const nose = landmarks?.[1];
  if (!leftCheek || !rightCheek || !nose) return null;
  const leftSpan = Math.abs(nose.x - leftCheek.x) + 0.0001;
  const rightSpan = Math.abs(rightCheek.x - nose.x) + 0.0001;
  return (rightSpan - leftSpan) / (rightSpan + leftSpan);
}

function drawFaceLandmarks(result) {
  const canvas = landmarkCanvasRef.value;
  const video = videoRef.value;
  if (!canvas || !video) return;
  const width = Math.max(1, video.videoWidth);
  const height = Math.max(1, video.videoHeight);
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, width, height);

  const landmarks = result?.faceLandmarks?.[0];
  if (!landmarks?.length) {
    landmarkDetected.value = false;
    smoothedFaceLandmarks = null;
    return;
  }
  landmarkDetected.value = true;
  if (!smoothedFaceLandmarks || smoothedFaceLandmarks.length !== landmarks.length) {
    smoothedFaceLandmarks = landmarks.map((point) => ({
      x: point.x,
      y: point.y,
      z: point.z
    }));
  } else {
    smoothedFaceLandmarks = landmarks.map((point, index) => {
      const previous = smoothedFaceLandmarks[index];
      return {
        x: previous.x + (point.x - previous.x) * 0.48,
        y: previous.y + (point.y - previous.y) * 0.48,
        z: previous.z + (point.z - previous.z) * 0.48
      };
    });
  }

  const lineWidth = Math.max(1.4, width / 850);
  context.save();
  context.lineCap = "round";
  context.lineJoin = "round";
  for (const [connections, multiplier, color, blur] of [
    [faceLandmarkConnections, 4.8, "rgba(119, 255, 218, 0.16)", 13],
    [faceLandmarkConnections, 1, "rgba(223, 244, 125, 0.82)", 7]
  ]) {
    if (!connections) continue;
    context.beginPath();
    for (const connection of connections) {
      const start = smoothedFaceLandmarks[connection.start];
      const end = smoothedFaceLandmarks[connection.end];
      if (!start || !end) continue;
      context.moveTo(start.x * width, start.y * height);
      context.lineTo(end.x * width, end.y * height);
    }
    context.lineWidth = lineWidth * multiplier;
    context.strokeStyle = color;
    context.shadowColor = "rgba(194, 255, 218, 0.55)";
    context.shadowBlur = blur;
    context.stroke();
  }

  context.shadowBlur = 9;
  context.fillStyle = "rgba(238, 255, 190, 0.9)";
  for (const index of [1, 13, 14, 33, 61, 133, 263, 291, 362]) {
    const point = smoothedFaceLandmarks[index];
    if (!point) continue;
    context.beginPath();
    context.arc(point.x * width, point.y * height, lineWidth * 1.3, 0, Math.PI * 2);
    context.fill();
  }
  context.restore();
}

function inspectAction(result) {
  if (
    step.value !== 1 ||
    !action.value ||
    !result?.faceBlendshapes?.length ||
    !result?.faceLandmarks?.length
  ) {
    return;
  }
  const scores = blendScores(result);
  let confidence = 0;
  if (action.value === "blink_both") {
    const leftEye = scores.eyeBlinkLeft || 0;
    const rightEye = scores.eyeBlinkRight || 0;
    confidence = Math.min(leftEye, rightEye);
  } else if (action.value === "open_mouth") {
    confidence = scores.jawOpen || 0;
  } else if (action.value === "turn_head") {
    const yaw = faceYaw(result.faceLandmarks[0]);
    if (yaw !== null) {
      if (actionBaselineYaw === null) actionBaselineYaw = yaw;
      confidence = Math.min(1, Math.abs(yaw - actionBaselineYaw) / 0.3);
    }
  }
  const threshold =
    action.value === "open_mouth" ? 0.22 : action.value === "turn_head" ? 0.55 : 0.34;
  const now = performance.now();
  if (confidence >= threshold && now - lastActionSent > 1200) {
    lastActionSent = now;
    sendEvent({
      type: "action_detected",
      action: action.value,
      confidence: Number(confidence.toFixed(3))
    });
  }
}

async function handleSocketMessage(event) {
  let message;
  try {
    message = JSON.parse(event.data);
  } catch {
    return;
  }
  if (message.type === "session_ready") {
    step.value = 1;
    action.value = message.action;
    actionBaselineYaw = null;
    instructionKey.value = `action.${message.action}`;
  } else if (message.type === "frame_quality") {
    quality.value = message.quality;
  } else if (message.type === "action_retry") {
    statusKey.value = "scanner.holdMoment";
  } else if (message.type === "action_passed") {
    pendingLighting = message.lighting;
    void beginLightingChallenge();
  } else if (message.type === "lighting_started") {
    pauseFrameUpload = false;
    runLightingSequence(message.lighting || pendingLighting);
  } else if (message.type === "step_started" && message.step === 3) {
    step.value = 3;
    instructionKey.value = "scanner.holdFace";
    window.setTimeout(() => sendEvent({ type: "capture_final" }), 650);
  } else if (message.type === "face_match") {
    candidates.value = message.candidates || [];
    screen.value = "accounts";
    speakText(t("account.spoken"), true);
    stopScan(false);
  } else if (message.type === "face_no_match") {
    enrollmentTicket.value = message.enrollmentTicket;
    screen.value = "no-match";
    speakText(t("noMatch.spoken"), true);
    stopScan(false);
  } else if (message.type === "scan_failed") {
    error.value = localizeServerMessage(message.reason);
    screen.value = "failed";
    stopScan(false);
  } else if (message.type === "session_expired") {
    error.value = t("server.expired");
    screen.value = "failed";
    stopScan(false);
  } else if (message.type === "error") {
    error.value = localizeServerMessage(message.message);
    speakText(error.value);
  }
}

function wait(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

async function runLightingSequence(lighting) {
  const run = ++lightingRun;
  const phases = lighting?.phases || [];
  const sequenceStartedAt = performance.now();
  let elapsedPlanMs = 0;
  for (const entry of phases) {
    if (run !== lightingRun || screen.value !== "scanner") return;
    currentPhase.value = entry.name === "ambient" ? null : entry.name;
    elapsedPlanMs += entry.durationMs;
    const targetTime = sequenceStartedAt + elapsedPlanMs;
    await wait(Math.max(0, targetTime - performance.now()));
  }
  if (run === lightingRun && socket?.readyState === WebSocket.OPEN) {
    currentPhase.value = null;
    sendEvent({ type: "lighting_complete" });
  }
}

async function beginLightingChallenge() {
  pauseFrameUpload = true;
  lightingPromptPending = true;
  step.value = 2;
  statusKey.value = "scanner.keepFace";
  instructionKey.value = "scanner.holdLight";
  await speakText(t("scanner.holdLight"), true);
  lightingPromptPending = false;
  if (screen.value !== "scanner" || socket?.readyState !== WebSocket.OPEN) {
    pauseFrameUpload = false;
    return;
  }
  sendEvent({ type: "lighting_ready" });
}

function stopScan(resetScreen = true) {
  scanGeneration += 1;
  busy.value = false;
  if (document.fullscreenElement && document.exitFullscreen) {
    document.exitFullscreen().catch(() => {});
  }
  lightingRun += 1;
  currentPhase.value = null;
  wsConnected.value = false;
  if (socket) {
    socket.close();
    socket = null;
  }
  cancelAnimationFrame(frameLoop);
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }
  cameraConnected.value = false;
  landmarkDetected.value = false;
  smoothedFaceLandmarks = null;
  actionBaselineYaw = null;
  pauseFrameUpload = false;
  lightingPromptPending = false;
  pendingLighting = null;
  if (videoRef.value) videoRef.value.srcObject = null;
  if (resetScreen) screen.value = "welcome";
}

function rescan() {
  stopScan(false);
  window.setTimeout(startScan, 60);
}

function selectAccount(candidate) {
  selectedCandidate.value = candidate;
  candidateToken.value = candidate.token;
  loginPassword.value = "";
  clearError();
  screen.value = "password";
  speakText(t("password.spoken", { name: candidate.name }), true);
}

function openRegistration() {
  clearError();
  screen.value = "register";
}

function openRecovery() {
  stopScan(false);
  selectedCandidate.value = null;
  candidateToken.value = "";
  loginPassword.value = "";
  recoveryStage.value = "identity";
  recoveryName.value = "";
  recoveryQuestions.value = [];
  recoveryAnswer.value = "";
  recoveryPassword.value = "";
  clearError();
  screen.value = "recovery";
}

async function openSelectedAccountRecovery() {
  if (!selectedCandidate.value) {
    openRecovery();
    return;
  }
  clearError();
  recoveryStage.value = "identity";
  recoveryName.value = selectedCandidate.value.name;
  recoveryQuestions.value = [];
  recoveryAnswer.value = "";
  recoveryPassword.value = "";
  screen.value = "recovery";
  await loadRecoveryQuestions();
}

function leaveRecovery() {
  clearError();
  screen.value = selectedCandidate.value ? "password" : "welcome";
}

async function submitPassword() {
  clearError();
  busy.value = true;
  try {
    const result = await api("/api/auth/password", {
      method: "POST",
      body: JSON.stringify({
        candidate_token: candidateToken.value,
        password: loginPassword.value
      })
    });
    signedInUser.value = result.user;
    authMethod.value = "face-password";
    loginPassword.value = "";
    if (redirectAdmin(result.user)) return;
    screen.value = "success";
  } catch (passwordError) {
    error.value = localizeCaughtError(passwordError);
  } finally {
    busy.value = false;
  }
}

async function submitNameLogin() {
  clearError();
  busy.value = true;
  try {
    const result = await api("/api/auth/name-login", {
      method: "POST",
      body: JSON.stringify({
        display_name: nameLogin.displayName,
        password: nameLogin.password
      })
    });
    signedInUser.value = result.user;
    authMethod.value = "name-password";
    nameLogin.password = "";
    if (redirectAdmin(result.user)) return;
    screen.value = "success";
  } catch (loginError) {
    error.value = localizeCaughtError(loginError);
  } finally {
    busy.value = false;
  }
}

async function submitRegistration() {
  clearError();
  if (registration.displayName.trim().length < 2) {
    error.value = t("error.nameShort");
    return;
  }
  if (registration.password !== registration.confirmPassword) {
    error.value = t("error.passwordMismatch");
    return;
  }
  if (registration.firstQuestion.trim().length < 5) {
    error.value = t("error.questions");
    return;
  }
  if (registration.firstAnswer.trim().length < 4) {
    error.value = t("error.answers");
    return;
  }
  if (!registration.agreementAccepted) {
    error.value = t("error.terms");
    return;
  }
  busy.value = true;
  try {
    const result = await api("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        enrollment_ticket: enrollmentTicket.value,
        display_name: registration.displayName,
        password: registration.password,
        terms_accepted: registration.agreementAccepted,
        biometric_consent: registration.agreementAccepted,
        security_answers: [
          { question: registration.firstQuestion, answer: registration.firstAnswer }
        ]
      })
    });
    signedInUser.value = result.user;
    authMethod.value = "registered";
    registration.password = "";
    registration.confirmPassword = "";
    screen.value = "success";
  } catch (registrationError) {
    error.value = localizeCaughtError(registrationError);
  } finally {
    busy.value = false;
  }
}

async function loadRecoveryQuestions() {
  clearError();
  if (!recoveryName.value.trim()) {
    error.value = t("error.nameRequired");
    return;
  }
  busy.value = true;
  try {
    const result = await api("/api/auth/recovery/questions", {
      method: "POST",
      body: JSON.stringify({ display_name: recoveryName.value })
    });
    recoveryQuestions.value = result.questions;
    recoveryStage.value = "questions";
  } catch (recoveryError) {
    error.value = localizeCaughtError(recoveryError);
  } finally {
    busy.value = false;
  }
}

async function resetPassword() {
  clearError();
  busy.value = true;
  try {
    await api("/api/auth/recovery/reset", {
      method: "POST",
      body: JSON.stringify({
        display_name: recoveryName.value,
        answers: [
          {
            question: recoveryQuestions.value[0],
            answer: recoveryAnswer.value
          }
        ],
        new_password: recoveryPassword.value
      })
    });
    recoveryStage.value = "complete";
    selectedCandidate.value = null;
    candidateToken.value = "";
  } catch (recoveryError) {
    error.value = localizeCaughtError(recoveryError);
  } finally {
    busy.value = false;
  }
}

async function signOut() {
  await api("/api/auth/logout", { method: "POST", body: "{}" }).catch(() => {});
  signedInUser.value = null;
  authMethod.value = "";
  selectedCandidate.value = null;
  candidateToken.value = "";
  loginPassword.value = "";
  screen.value = "welcome";
}

async function deleteAccount() {
  clearError();
  busy.value = true;
  try {
    await api("/api/auth/account/delete", {
      method: "POST",
      body: JSON.stringify({ password: deletePassword.value })
    });
    signedInUser.value = null;
    authMethod.value = "";
    deletePassword.value = "";
    showDeleteAccount.value = false;
    screen.value = "welcome";
    speakText(t("success.deleted"), true);
  } catch (deleteError) {
    error.value = localizeCaughtError(deleteError);
  } finally {
    busy.value = false;
  }
}

function initials(name) {
  return String(name)
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

function clearError() {
  error.value = "";
}

onMounted(() => {
  checkExistingSession();
  const preloadSensor = () => {
    if (!navigator.connection?.saveData) loadFaceSensor();
  };
  if ("requestIdleCallback" in window) {
    window.requestIdleCallback(preloadSensor, { timeout: 4000 });
  } else {
    window.setTimeout(preloadSensor, 1500);
  }
});

onBeforeUnmount(() => {
  stopScan(false);
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  faceLandmarker?.close();
});

watch(instruction, (value) => {
  if (lightingPromptPending) return;
  if (screen.value === "scanner" || screen.value === "verifying") speakText(value);
});

watch(screen, (value) => {
  const key = spokenScreenKeys[value];
  if (value === "success" && returnTo) {
    window.setTimeout(() => window.location.assign(returnTo), 220);
  }
  if (
    !["scanner", "accounts", "password", "no-match", "failed"].includes(value) &&
    key
  ) {
    speakText(t(key));
  }
});

watch(error, (value) => {
  if (value) speakText(value);
});

watch(
  locale,
  (value) => {
    document.documentElement.lang = value;
    document.title = t("app.title");
  },
  { immediate: true }
);
</script>

<template>
  <main class="stage" :class="{ 'camera-is-open': cameraView }">
    <div v-if="cameraView" class="camera-stage">
      <video ref="videoRef" autoplay muted playsinline :aria-label="t('welcome.title')"></video>
      <div class="camera-shade"></div>
      <canvas
        ref="landmarkCanvasRef"
        class="landmark-overlay"
        :class="{ visible: landmarkDetected }"
        aria-hidden="true"
      ></canvas>
      <div
        v-if="landmarkDetected"
        class="landmark-detected"
        role="status"
        aria-live="polite"
      >
        <span aria-hidden="true"></span>
        {{ t("landmark.detected") }}
      </div>
      <div
        class="screen-tint"
        :class="{ visible: Boolean(currentPhase) }"
        :style="{ background: lightTint }"
      ></div>

      <header class="camera-header">
        <span class="mini-brand"><i></i> FaceSignUp</span>
        <div class="header-actions">
          <span class="camera-live"><i></i>{{ cameraStatus }}</span>
          <label class="language-picker">
            <span class="sr-only">{{ t("language.label") }}</span>
            <select v-model="locale" :aria-label="t('language.label')" @change="changeLanguage">
              <option v-for="option in localeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <button
            class="voice-toggle"
            type="button"
            :aria-pressed="voiceEnabled"
            @click="toggleVoice"
          >
            {{ voiceEnabled ? t("voice.on") : t("voice.off") }}
          </button>
        </div>
      </header>

      <div class="step-track">
        <span v-for="index in 3" :key="index" :class="{ done: step > index, active: step === index }">
          <b>{{ index }}</b>
          <em v-if="step === index">{{ stepText }}</em>
        </span>
      </div>

      <div class="face-target" :class="{ warning: quality && quality.faces !== 1 }">
        <span class="target-corner one"></span>
        <span class="target-corner two"></span>
        <span class="target-corner three"></span>
        <span class="target-corner four"></span>
        <div class="target-scanline"></div>
      </div>

      <div
        v-if="cameraNotice"
        class="camera-notice"
        role="status"
        aria-live="polite"
      >
        <span class="notice-icon" aria-hidden="true">!</span>
        <strong>{{ cameraNotice }}</strong>
      </div>

      <section class="challenge-copy" role="status" aria-live="assertive">
        <p>{{ stepText }}</p>
        <h1>{{ instruction }}</h1>
        <span v-if="!cameraNotice">{{ qualityText }}</span>
      </section>

      <button class="camera-cancel" type="button" @click="stopScan()">
        {{ t("common.cancel") }}
      </button>
    </div>

    <template v-else>
      <div class="panel-background"></div>
      <header class="panel-header">
        <button
          class="mini-brand button-brand"
          type="button"
          :aria-label="t('welcome.title')"
          @click="screen = 'welcome'"
        >
          <i></i> FaceSignUp
        </button>
        <div class="header-actions">
          <span class="sensor-state">{{ modelStatus }}</span>
          <label class="language-picker">
            <span class="sr-only">{{ t("language.label") }}</span>
            <select v-model="locale" :aria-label="t('language.label')" @change="changeLanguage">
              <option v-for="option in localeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <button
            class="voice-toggle"
            type="button"
            :aria-pressed="voiceEnabled"
            @click="toggleVoice"
          >
            {{ voiceEnabled ? t("voice.on") : t("voice.off") }}
          </button>
        </div>
      </header>

      <section v-if="screen === 'welcome'" class="welcome-screen">
        <button
          class="face-button"
          :disabled="busy"
          type="button"
          :aria-label="t('welcome.start')"
          @click="startScan"
        >
          <span class="face-symbol">
            <svg viewBox="0 0 128 128" aria-hidden="true">
              <defs>
                <radialGradient id="face-fill-gradient" cx="34%" cy="25%" r="78%">
                  <stop offset="0" stop-color="#fbffd9" />
                  <stop offset="0.58" stop-color="#e8f995" />
                  <stop offset="1" stop-color="#bedb55" />
                </radialGradient>
                <linearGradient id="smile-gradient" x1="42" y1="75" x2="86" y2="90">
                  <stop offset="0" stop-color="#243322" />
                  <stop offset="1" stop-color="#142118" />
                </linearGradient>
              </defs>
              <circle class="happy-face-fill" cx="64" cy="64" r="44" />
              <circle class="face-eye" cx="48" cy="57" r="4.2" />
              <circle class="face-eye" cx="80" cy="57" r="4.2" />
              <circle class="face-cheek" cx="35" cy="73" r="5" />
              <circle class="face-cheek" cx="93" cy="73" r="5" />
              <path class="smile-halo" d="M41 76Q64 98 87 76" />
              <path class="smile-line" d="M41 76Q64 98 87 76" />
            </svg>
          </span>
        </button>
        <h1>{{ t("welcome.title") }}</h1>
        <p>{{ t("welcome.subtitle") }}</p>
        <button class="primary-action" :disabled="busy" type="button" @click="startScan">
          {{ busy ? t("welcome.opening") : t("welcome.start") }}
        </button>
        <button class="quiet-action" type="button" @click="screen = 'name-login'">
          {{ t("welcome.nameLogin") }}
        </button>
        <button class="quiet-action" type="button" @click="openRecovery">
          {{ t("welcome.recovery") }}
        </button>
        <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      </section>

      <section
        v-else-if="screen === 'name-login'"
        class="center-sheet has-back"
        aria-live="polite"
      >
        <button
          class="back-button"
          type="button"
          :aria-label="t('common.back')"
          @click="screen = 'welcome'"
        >
          ←
        </button>
        <h1>{{ t("nameLogin.title") }}</h1>
        <p class="sheet-note">{{ t("nameLogin.note") }}</p>
        <form @submit.prevent="submitNameLogin">
          <label for="name-login-name">{{ t("nameLogin.name") }}</label>
          <input
            id="name-login-name"
            v-model="nameLogin.displayName"
            autocomplete="username"
            required
          />
          <label for="name-login-password">{{ t("nameLogin.password") }}</label>
          <input
            id="name-login-password"
            v-model="nameLogin.password"
            type="password"
            autocomplete="current-password"
            required
          />
          <p v-if="error" class="form-error" role="alert">{{ error }}</p>
          <button class="primary-action wide" :disabled="busy" type="submit">
            {{ busy ? t("nameLogin.signingIn") : t("nameLogin.submit") }}
          </button>
        </form>
        <button class="quiet-action" type="button" @click="openRecovery">
          {{ t("password.forgot") }}
        </button>
      </section>

      <section v-else-if="screen === 'accounts'" class="center-sheet account-sheet" aria-live="polite">
        <p class="sheet-kicker">{{ t("account.kicker") }}</p>
        <h1>{{ t("account.title") }}</h1>
        <p class="sheet-note">{{ t("account.note") }}</p>
        <div class="account-list">
          <button
            v-for="(candidate, index) in candidates"
            :key="candidate.token"
            class="account-option"
            type="button"
            @click="selectAccount(candidate)"
          >
            <span class="account-rank">{{ index + 1 }}</span>
            <span class="account-avatar">{{ initials(candidate.name) }}</span>
            <span class="account-name">{{ candidate.name }}</span>
            <span class="account-arrow">→</span>
          </button>
        </div>
        <div class="sheet-actions">
          <button class="quiet-action" type="button" @click="rescan">
            {{ t("account.scanAgain") }}
          </button>
          <button class="quiet-action" type="button" @click="openRecovery">
            {{ t("account.recover") }}
          </button>
        </div>
      </section>

      <section
        v-else-if="screen === 'password'"
        class="center-sheet has-back"
        aria-live="polite"
      >
        <button
          class="back-button"
          type="button"
          :aria-label="t('common.back')"
          @click="screen = 'accounts'"
        >
          ←
        </button>
        <span class="account-pill">{{ selectedCandidate?.name }}</span>
        <h1>{{ t("password.title") }}</h1>
        <form @submit.prevent="submitPassword">
          <label for="login-password">{{ t("password.label") }}</label>
          <input
            id="login-password"
            v-model="loginPassword"
            type="password"
            autocomplete="current-password"
            autofocus
            required
          />
          <p v-if="error" class="form-error" role="alert">{{ error }}</p>
          <button class="primary-action wide" :disabled="busy" type="submit">
            {{ busy ? t("password.verifying") : t("password.verify") }}
          </button>
        </form>
        <button class="quiet-action" type="button" @click="openSelectedAccountRecovery">
          {{ t("password.forgot") }}
        </button>
      </section>

      <section v-else-if="screen === 'no-match'" class="center-sheet" aria-live="polite">
        <span class="result-symbol">?</span>
        <h1>{{ t("noMatch.title") }}</h1>
        <p class="sheet-note">{{ t("noMatch.note") }}</p>
        <button class="primary-action wide" type="button" @click="openRegistration">
          {{ t("noMatch.register") }}
        </button>
        <button class="secondary-action wide" type="button" @click="rescan">
          {{ t("noMatch.rescan") }}
        </button>
        <button class="quiet-action" type="button" @click="openRecovery">
          {{ t("account.recover") }}
        </button>
        <button class="quiet-action" type="button" @click="screen = 'welcome'">
          {{ t("welcome.nameLogin") }}
        </button>
      </section>

      <section v-else-if="screen === 'failed'" class="center-sheet" aria-live="assertive">
        <span class="result-symbol warning">!</span>
        <h1>{{ t("failed.title") }}</h1>
        <p class="sheet-note">{{ error || t("failed.tryAgain") }}</p>
        <button class="primary-action wide" type="button" @click="rescan">
          {{ t("noMatch.rescan") }}
        </button>
        <button class="quiet-action" type="button" @click="openRecovery">
          {{ t("welcome.recovery") }}
        </button>
        <button class="quiet-action" type="button" @click="screen = 'welcome'">
          {{ t("welcome.nameLogin") }}
        </button>
      </section>

      <section v-else-if="screen === 'register'" class="center-sheet form-sheet" aria-live="polite">
        <p class="sheet-kicker">{{ t("register.kicker") }}</p>
        <h1>{{ t("register.title") }}</h1>
        <form @submit.prevent="submitRegistration">
          <div>
            <label for="display-name">{{ t("register.name") }}</label>
            <input
              id="display-name"
              v-model="registration.displayName"
              autocomplete="username"
              minlength="2"
              required
            />
            <p class="field-help">{{ t("register.nameHelp") }}</p>
          </div>
          <div class="field-pair">
            <div>
              <label for="register-password">{{ t("register.password") }}</label>
              <input id="register-password" v-model="registration.password" type="password" autocomplete="new-password" minlength="10" required />
            </div>
            <div>
              <label for="confirm-password">{{ t("register.confirm") }}</label>
              <input id="confirm-password" v-model="registration.confirmPassword" type="password" autocomplete="new-password" minlength="10" required />
            </div>
          </div>

          <fieldset>
            <legend>{{ t("register.recovery") }}</legend>
            <p class="field-help security-help">{{ t("register.securityHelp") }}</p>
            <label for="first-question">{{ t("register.question") }}</label>
            <input
              id="first-question"
              v-model="registration.firstQuestion"
              :placeholder="t('register.writeQuestion')"
              minlength="5"
              required
            />
            <label for="first-answer">{{ t("register.answer") }}</label>
            <input
              id="first-answer"
              v-model="registration.firstAnswer"
              autocomplete="off"
              minlength="4"
              required
            />
          </fieldset>
          <label class="consent-row" for="terms-consent">
            <input
              id="terms-consent"
              v-model="registration.agreementAccepted"
              type="checkbox"
              required
            />
            <span>{{ t("register.termsAgreement") }}</span>
          </label>
          <button class="terms-button" type="button" @click="showTerms = true">
            {{ t("terms.read") }}
          </button>
          <p v-if="error" class="form-error" role="alert">{{ error }}</p>
          <button class="primary-action wide" :disabled="busy" type="submit">
            {{ busy ? t("register.creating") : t("register.submit") }}
          </button>
        </form>
        <button class="quiet-action" type="button" @click="rescan">
          {{ t("register.back") }}
        </button>
      </section>

      <section v-else-if="screen === 'recovery'" class="center-sheet" aria-live="polite">
        <p class="sheet-kicker">{{ t("recovery.kicker") }}</p>
        <template v-if="recoveryStage === 'identity'">
          <h1>{{ t("recovery.find") }}</h1>
          <form @submit.prevent="loadRecoveryQuestions">
            <label for="recovery-name">{{ t("recovery.name") }}</label>
            <input id="recovery-name" v-model="recoveryName" autocomplete="username" required />
            <p v-if="error" class="form-error" role="alert">{{ error }}</p>
            <button class="primary-action wide" :disabled="busy" type="submit">
              {{ t("recovery.continue") }}
            </button>
          </form>
        </template>
        <template v-else-if="recoveryStage === 'questions'">
          <h1>{{ t("recovery.questions") }}</h1>
          <form @submit.prevent="resetPassword">
            <label>{{ recoveryQuestions[0] }}</label>
            <input v-model="recoveryAnswer" autocomplete="off" required />
            <label for="recovery-password">{{ t("recovery.newPassword") }}</label>
            <input id="recovery-password" v-model="recoveryPassword" type="password" autocomplete="new-password" minlength="10" required />
            <p v-if="error" class="form-error" role="alert">{{ error }}</p>
            <button class="primary-action wide" :disabled="busy" type="submit">
              {{ t("recovery.reset") }}
            </button>
          </form>
        </template>
        <template v-else>
          <span class="result-symbol success">✓</span>
          <h1>{{ t("recovery.changed") }}</h1>
          <p class="sheet-note">{{ t("recovery.changedNote") }}</p>
          <button class="primary-action wide" type="button" @click="screen = 'welcome'">
            {{ t("recovery.return") }}
          </button>
        </template>
        <button class="quiet-action" type="button" @click="leaveRecovery">
          {{ t("common.back") }}
        </button>
      </section>

      <section v-else-if="screen === 'success'" class="center-sheet success-sheet" aria-live="polite">
        <span class="result-symbol success">✓</span>
        <h1>{{ signedInUser?.displayName || t("success.spoken") }}</h1>
        <p class="sheet-note">{{ successMessage }}</p>
        <button class="secondary-action wide" type="button" @click="signOut">
          {{ t("success.signOut") }}
        </button>
        <button class="quiet-action danger-link" type="button" @click="showDeleteAccount = !showDeleteAccount">
          {{ t("success.delete") }}
        </button>
        <form v-if="showDeleteAccount" class="delete-account-form" @submit.prevent="deleteAccount">
          <label for="delete-password">{{ t("success.deleteLabel") }}</label>
          <input
            id="delete-password"
            v-model="deletePassword"
            type="password"
            autocomplete="current-password"
            required
          />
          <p class="form-error">{{ t("success.deleteWarning") }}</p>
          <button class="danger-action wide" :disabled="busy" type="submit">
            {{ busy ? t("success.deleting") : t("success.deleteConfirm") }}
          </button>
        </form>
      </section>
    </template>

    <div v-if="showTerms" class="terms-backdrop" @click.self="showTerms = false">
      <section
        class="terms-dialog"
        role="dialog"
        aria-modal="true"
        :aria-label="t('terms.title')"
      >
        <header class="terms-dialog-header">
          <div>
            <p class="sheet-kicker">{{ t("terms.title") }}</p>
            <span>{{ termsVersion }}</span>
          </div>
          <button class="terms-close" type="button" @click="showTerms = false">
            {{ t("terms.close") }}
          </button>
        </header>
        <p v-if="locale !== 'en'" class="terms-language-notice">
          {{ t("terms.englishNotice") }}
        </p>
        <div class="terms-content">
          <article v-for="section in localizedTerms" :key="section.title">
            <h2>{{ section.title }}</h2>
            <p v-for="paragraph in section.paragraphs" :key="paragraph">
              {{ paragraph }}
            </p>
          </article>
        </div>
        <footer class="terms-dialog-footer">
          <button
            class="primary-action wide"
            type="button"
            @click="
              registration.agreementAccepted = true;
              showTerms = false
            "
          >
            {{ t("register.terms") }}
          </button>
        </footer>
      </section>
    </div>
  </main>
</template>
