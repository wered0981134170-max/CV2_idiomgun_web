import { HandLandmarker, FilesetResolver }
  from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/vision_bundle.js";

let handLandmarker = null;
let lastVideoTime  = -1;

async function initMP() {
  const vision = await FilesetResolver.forVisionTasks(
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
  );
  handLandmarker = await HandLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath:
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
      delegate: "GPU",
    },
    runningMode: "VIDEO",
    numHands: 1,
  });
  const st = document.getElementById("cam-status");
  if (st) { st.textContent = "✅ 偵測器就緒"; st.style.color = "var(--neon-g)"; }
  window._mpReady = true;
}

async function startCamera() {
  const video = document.getElementById("camera-video");
  const st    = document.getElementById("cam-status");
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 1280, height: 720, facingMode: "user" },
      audio: false,
    });
    video.srcObject = stream;
    await new Promise(res => { video.onloadedmetadata = res; });
    video.play();
    if (st) { st.textContent = "📷 攝影機就緒"; st.style.color = "var(--neon-g)"; }
  } catch (err) {
    if (st) { st.textContent = "⚠ " + err.message; st.style.color = "var(--neon-r)"; }
  }
}

const SMOOTH = 0.65, LOST_TIMEOUT = 800;
let smoothX = 0, smoothY = 0, lastValidX = 0, lastValidY = 0, lastSeenTime = 0;

function detectHands(video) {
  if (!handLandmarker || !video || !video.videoWidth) return;
  if (video.currentTime === lastVideoTime) return;
  lastVideoTime = video.currentTime;
  const now = performance.now();
  const res = handLandmarker.detectForVideo(video, now);
  if (res.landmarks && res.landmarks.length > 0) {
    const lm = res.landmarks[0];
    lastSeenTime = now;

    // 食指尖(8) 高於食指掌骨根(5)，中指尖(12) 低於中指第一關節(10)
    const indexUp   = lm[8].y < lm[5].y;
    const middleDown = lm[12].y > lm[10].y;

    if (indexUp && middleDown) {
      const rx = 1 - lm[8].x;
      const tx = Math.max(0.02, Math.min(0.98, rx))      * window.innerWidth;
      const ty = Math.max(0.04, Math.min(0.90, lm[8].y)) * window.innerHeight;
      smoothX = SMOOTH * smoothX + (1 - SMOOTH) * tx;
      smoothY = SMOOTH * smoothY + (1 - SMOOTH) * ty;
      lastValidX = smoothX; lastValidY = smoothY;
      window._gesture = { thumbActive: true, x: smoothX, y: smoothY };
    } else {
      window._gesture = { thumbActive: false, x: smoothX, y: smoothY };
    }
  } else {
    if (now - lastSeenTime < LOST_TIMEOUT) {
      smoothX = lastValidX; smoothY = lastValidY;
      window._gesture = { thumbActive: true, x: smoothX, y: smoothY };
    } else {
      window._gesture = { thumbActive: false, x: smoothX, y: smoothY };
    }
  }
}

window._detectHands = detectHands;
window._gesture = { thumbActive: false, x: 0, y: 0 };
await initMP();
await startCamera();
