function $(id) { return document.getElementById(id); }

const baseUrlEl = $("baseUrl");
const statusEl = $("status");
const outputEl = $("output");

const video = $("video");
const overlay = $("overlay");
const octx = overlay.getContext("2d");

// 用于截图上传（不显示）
const captureCanvas = document.createElement("canvas");
const cctx = captureCanvas.getContext("2d");

let stream = null;
let timer = null;
let inFlight = false;

function setStatus(msg, ok = true) {
  statusEl.textContent = msg;
  statusEl.className = ok ? "ok" : "bad";
}

function log(obj) {
  outputEl.textContent = typeof obj === "string" ? obj : JSON.stringify(obj, null, 2);
}

function clearOverlay() {
  octx.clearRect(0, 0, overlay.width, overlay.height);
}

async function healthCheck() {
  const base = baseUrlEl.value.replace(/\/+$/, "");
  try {
    const r = await fetch(`${base}/health`);
    const t = await r.text();
    setStatus(`health: ${t}`, r.ok);
    log(t);
  } catch (e) {
    setStatus("health failed", false);
    log(String(e));
  }
}

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false
    });
    video.srcObject = stream;

    // 等 video 真正有尺寸
    await new Promise((resolve) => {
      video.onloadedmetadata = () => resolve();
    });

    // 让 overlay / captureCanvas 的“像素尺寸”与视频一致
    const vw = video.videoWidth;
    const vh = video.videoHeight;

    overlay.width = vw;
    overlay.height = vh;

    captureCanvas.width = vw;
    captureCanvas.height = vh;

    setStatus("camera started", true);
    log("camera started");

    startLoop();
  } catch (e) {
    setStatus("camera permission denied / no camera", false);
    log(String(e));
  }
}

function stopCamera() {
  stopLoop();
  clearOverlay();

  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
  video.srcObject = null;
  setStatus("stopped", true);
}

function startLoop() {
  stopLoop();
  const interval = Math.max(200, parseInt($("intervalMs").value || "400", 10));
  timer = setInterval(tick, interval);
}

function stopLoop() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
  inFlight = false;
}

function drawBoxes(faces, mirrored) {
  clearOverlay();

  // 如果镜像：画框时要把 x 坐标翻转
  const W = overlay.width;
  const H = overlay.height;

  octx.lineWidth = Math.max(2, Math.round(Math.min(W, H) / 250));
  octx.font = `${Math.max(14, Math.round(Math.min(W, H) / 35))}px system-ui`;
  octx.strokeStyle = "red";

  faces.forEach((f, i) => {
    let x1 = f.x1, x2 = f.x2;
    const y1 = f.y1, y2 = f.y2;

    if (mirrored) {
      // 翻转：x' = W - x
      const nx1 = W - x2;
      const nx2 = W - x1;
      x1 = nx1; x2 = nx2;
    }

    const w = x2 - x1;
    const h = y2 - y1;

    octx.strokeRect(x1, y1, w, h);

    const label = `#${i + 1} ${(f.score * 100).toFixed(1)}%`;
    const pad = 6;
    const tw = octx.measureText(label).width;
    const th = parseInt(octx.font, 10) + pad;

    octx.fillStyle = "rgba(255,0,0,0.85)";
    octx.fillRect(x1, Math.max(0, y1 - th), tw + pad * 2, th);
    octx.fillStyle = "white";
    octx.fillText(label, x1 + pad, Math.max(14, y1 - pad));
  });
}

function tick() {
  if (!stream) return;
  if (inFlight) return; // 防止请求堆积
  inFlight = true;

  const base = baseUrlEl.value.replace(/\/+$/, "");
  const mirrored = $("mirror").checked;

  // 截图：把 video 画到 captureCanvas
  cctx.save();
  cctx.clearRect(0, 0, captureCanvas.width, captureCanvas.height);

  if (mirrored) {
    // 镜像显示（自拍效果）：先翻转画面
    cctx.translate(captureCanvas.width, 0);
    cctx.scale(-1, 1);
  }
  cctx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
  cctx.restore();

  // 转成 blob 上传
  captureCanvas.toBlob(async (blob) => {
    try {
      const fd = new FormData();
      fd.append("image", blob, "frame.jpg");

      const r = await fetch(`${base}/detect`, {
        method: "POST",
        body: fd
      });

      const data = await r.json();
      if (!r.ok) {
        setStatus("detect failed", false);
        log(data);
        clearOverlay();
        inFlight = false;
        return;
      }

      setStatus(`running: faces=${data.count ?? 0}`, true);
      log(data);

      // 注意：我们上传时如果 mirrored=true，上传给后端的图像已经是镜像后的，
      // 因此后端返回坐标是“镜像图坐标”。我们在 overlay 上也按同样坐标画即可（不需要再翻）。
      // 但如果你选择 mirrored=false，上面上传也不镜像，画框也不镜像。
      // 所以这里 mirrored 传 false（不要二次翻转）。
      drawBoxes(data.faces || [], false);

    } catch (e) {
      setStatus("request error", false);
      log(String(e));
      clearOverlay();
    } finally {
      inFlight = false;
    }
  }, "image/jpeg", 0.85);
}

// 绑定按钮
$("btnHealth").addEventListener("click", healthCheck);
$("btnStartCam").addEventListener("click", startCamera);
$("btnStopCam").addEventListener("click", stopCamera);
$("btnClear").addEventListener("click", () => { clearOverlay(); log(""); setStatus("cleared"); });
