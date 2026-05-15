const TTS_SAMPLE_RATE = 24000;

const VOICES = [
  "Adrian",
  "Claire",
  "Daniel",
  "Emma",
  "Grace",
  "Jack",
  "Kenji",
  "Maya",
  "Mina",
  "Nina",
  "Noah",
  "Owen",
];

const LANGUAGES = [
  ["af", "Afrikaans"],
  ["sq", "Albanian"],
  ["ar", "Arabic"],
  ["az", "Azerbaijani"],
  ["eu", "Basque"],
  ["be", "Belarusian"],
  ["bn", "Bengali"],
  ["bs", "Bosnian"],
  ["bg", "Bulgarian"],
  ["ca", "Catalan"],
  ["zh", "Chinese"],
  ["hr", "Croatian"],
  ["cs", "Czech"],
  ["da", "Danish"],
  ["nl", "Dutch"],
  ["en", "English"],
  ["et", "Estonian"],
  ["fi", "Finnish"],
  ["fr", "French"],
  ["gl", "Galician"],
  ["de", "German"],
  ["el", "Greek"],
  ["gu", "Gujarati"],
  ["he", "Hebrew"],
  ["hi", "Hindi"],
  ["hu", "Hungarian"],
  ["id", "Indonesian"],
  ["it", "Italian"],
  ["ja", "Japanese"],
  ["kn", "Kannada"],
  ["kk", "Kazakh"],
  ["ko", "Korean"],
  ["lv", "Latvian"],
  ["lt", "Lithuanian"],
  ["mk", "Macedonian"],
  ["ms", "Malay"],
  ["ml", "Malayalam"],
  ["mr", "Marathi"],
  ["no", "Norwegian"],
  ["fa", "Persian"],
  ["pl", "Polish"],
  ["pt", "Portuguese"],
  ["pa", "Punjabi"],
  ["ro", "Romanian"],
  ["ru", "Russian"],
  ["sr", "Serbian"],
  ["sk", "Slovak"],
  ["sl", "Slovenian"],
  ["es", "Spanish"],
  ["sw", "Swahili"],
  ["sv", "Swedish"],
  ["tl", "Tagalog"],
  ["ta", "Tamil"],
  ["te", "Telugu"],
  ["th", "Thai"],
  ["tr", "Turkish"],
  ["uk", "Ukrainian"],
  ["ur", "Urdu"],
  ["vi", "Vietnamese"],
  ["cy", "Welsh"],
];

let ws = null;

function openWebSocket(extraParams = {}) {
  // Build URL: same-origin, ws:// or wss:// based on page protocol.
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const params = new URLSearchParams({
    target_lang: $targetLang.value,
    lang_id: $langId.checked,
    diarize: $diarization.checked,
    voice: $voice.value,
    tts: $tts.checked,
    ...extraParams,
  });
  const url = `${proto}//${location.host}/ws/translate?${params}`;

  ws = new WebSocket(url);
  ws.binaryType = "arraybuffer"; // we want binary frames as ArrayBuffer, not Blob

  ws.onmessage = (event) => {
    if (typeof event.data === "string") {
      const data = JSON.parse(event.data);
      handleSttResult(data);
    } else {
      handleTtsAudio(new Uint8Array(event.data));
    }
  };

  return new Promise((resolve, reject) => {
    ws.onopen = () => resolve();
    ws.onerror = (e) => reject(e);
  });
}

function handleSttResult(data) {
  if (data.session_done) {
    // Backend has confirmed all STT/TTS work is done. Any TTS audio chunks
    // arrived before this message, so they're already queued in audioCtx and
    // will play out even after we close the WS.
    stop();
    return;
  }

  currentUtt.originalPartial = "";
  currentUtt.translationPartial = "";

  for (const t of data.tokens || []) {
    if (!t.text) continue;

    // <end> token: speaker finished an utterance
    if (t.text === "<end>") {
      if (
        currentUtt.originalFinal ||
        currentUtt.translationFinal ||
        currentUtt.originalPartial ||
        currentUtt.translationPartial
      ) {
        utterances.push(currentUtt);
        currentUtt = newUtt();
      }
      continue;
    }

    if (t.speaker != null) currentUtt.speaker = t.speaker;

    const isTranslation = t.translation_status === "translation";
    const spokenLang = isTranslation ? t.source_language : t.language;
    if (spokenLang) currentUtt.language = spokenLang;

    const side = isTranslation ? "translation" : "original";
    if (t.is_final) {
      currentUtt[`${side}Final`] += t.text;
    } else {
      currentUtt[`${side}Partial`] += t.text;
    }
  }

  render();
}

async function startRecorder() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0 && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(e.data);
    }
  };

  mediaRecorder.start(100); // emit a chunk every 100ms
}

const $targetLang = document.getElementById("target-language");
const $voice = document.getElementById("voice");
const $diarization = document.getElementById("diarization");
const $langId = document.getElementById("lang-id");
const $tts = document.getElementById("tts");
const $actionRow = document.querySelector(".action-row");
const $actionBtn = document.getElementById("action");
const $actionLabel = $actionBtn.querySelector(".btn-label");
const $modeToggle = document.getElementById("mode-toggle");
const $audioUrl = document.getElementById("audio-url");
const $originalCol = document.getElementById("original");
const $translationCol = document.getElementById("translation");
const $status = document.getElementById("status");

for (const [code, name] of LANGUAGES) {
  const opt = document.createElement("option");
  opt.value = code;
  opt.textContent = name;
  $targetLang.appendChild(opt);
}
$targetLang.value = "en";

for (const name of VOICES) {
  const opt = document.createElement("option");
  opt.value = name;
  opt.textContent = name;
  $voice.appendChild(opt);
}
$voice.value = "Maya";

const DEFAULT_AUDIO_URL = "https://soniox.com/media/examples/spanish_weather_report.mp3";
$audioUrl.value =
  new URLSearchParams(location.search).get("audio") || DEFAULT_AUDIO_URL;

let mode = "file";
let state = "idle";
let mediaRecorder = null;
let audioCtx = null;
let nextPlayTime = 0;
let utterances = [];
let currentUtt = newUtt();
let fileAudio = null;
let fileTtsHeard = false;

function newUtt() {
  return {
    speaker: null,
    language: null,
    originalFinal: "",
    originalPartial: "",
    translationFinal: "",
    translationPartial: "",
  };
}

function playPcmChunk(chunk) {
  if (!audioCtx) return;
  const evenLen = chunk.byteLength - (chunk.byteLength % 2);
  const int16 = new Int16Array(chunk.buffer, chunk.byteOffset, evenLen / 2);
  const float32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768;
  const buffer = audioCtx.createBuffer(1, float32.length, TTS_SAMPLE_RATE);
  buffer.getChannelData(0).set(float32);
  const source = audioCtx.createBufferSource();
  source.buffer = buffer;
  source.connect(audioCtx.destination);
  const startAt = Math.max(audioCtx.currentTime, nextPlayTime);
  source.start(startAt);
  nextPlayTime = startAt + buffer.duration;
}

function handleTtsAudio(chunk) {
  playPcmChunk(chunk);
  if (state !== "playing-file" || !fileAudio || fileTtsHeard) return;
  // Duck the source audio so the spoken translation is audible.
  fileTtsHeard = true;
  fileAudio.volume = 0.1;
}

function resetSession() {
  audioCtx = new AudioContext({ sampleRate: TTS_SAMPLE_RATE });
  nextPlayTime = 0;
  utterances = [];
  currentUtt = newUtt();
  render();
}

async function start() {
  setState("recording");
  resetSession();

  try {
    await openWebSocket();
    await startRecorder();
  } catch (err) {
    console.error(err);
    setStatus(`Failed to start: ${err.message}`);
    setState("idle");
    cleanup();
  }
}

async function playFile() {
  const url = $audioUrl.value.trim();
  if (!url) {
    setStatus("Enter an audio URL");
    return;
  }

  setState("playing-file");
  resetSession();
  fileTtsHeard = false;

  try {
    // Load the audio first so we have its duration — the backend uses it
    // to pace byte streaming to STT at real-time rate.
    fileAudio = new Audio(url);
    fileAudio.volume = 1.0;
    await new Promise((resolve, reject) => {
      fileAudio.addEventListener("loadedmetadata", resolve, { once: true });
      fileAudio.addEventListener("error", () => reject(new Error("audio load failed")), { once: true });
    });

    await openWebSocket({
      audio_url: url,
      audio_duration: fileAudio.duration,
    });

    await fileAudio.play();
  } catch (err) {
    console.error(err);
    setStatus(`Failed to play file: ${err.message}`);
    setState("idle");
    cleanup();
  }
}

function stop() {
  setState("idle");
  cleanup();
}

function cleanup() {
  if (mediaRecorder) {
    if (mediaRecorder.state !== "inactive") {
      try { mediaRecorder.stop(); } catch {}
    }
    mediaRecorder.stream.getTracks().forEach((t) => t.stop());
  }
  mediaRecorder = null;
  if (fileAudio) {
    fileAudio.pause();
    fileAudio = null;
  }
  if (ws) {
    try { ws.close(); } catch {}
    ws = null;
  }
}

function setState(s) {
  state = s;
  const busy = s !== "idle";
  if (busy) {
    $actionLabel.textContent = "Stop";
    $actionBtn.dataset.state = "running";
    $actionBtn.disabled = false;
  } else {
    $actionBtn.dataset.state = "idle";
    $actionLabel.textContent = mode === "file" ? "Play audio file" : "Start talking";
    $actionBtn.disabled = mode === "file" && !$audioUrl.value.trim();
  }
  $modeToggle.disabled = busy;
  $audioUrl.disabled = busy;
  $targetLang.disabled = busy;
  $voice.disabled = busy;
  $diarization.disabled = busy;
  $langId.disabled = busy;
  $tts.disabled = busy;
  if (s === "recording") setStatus("Listening…");
  else if (s === "playing-file") setStatus("Playing audio…");
  else setStatus("Ready");
}

function setMode(m) {
  mode = m;
  $actionRow.dataset.mode = m;
  // Re-run idle setup so the action button's label/disabled state picks up the new mode.
  if (state === "idle") setState("idle");
}

function setStatus(msg) {
  $status.textContent = msg;
}

function renderUtterance(u, col, side) {
  const final = u[`${side}Final`];
  const partial = u[`${side}Partial`];
  if (!final && !partial) return;

  const div = document.createElement("div");
  div.className = "utterance";

  // Original side: show speaker / source language as toggled.
  // Translation side: show the target language whenever lang-id is on —
  // mirrors the original's language tag so the two columns line up.
  const labels = [];
  if (side === "original") {
    if ($diarization.checked && u.speaker != null) labels.push(`Speaker ${u.speaker}`);
    if ($langId.checked && u.language) labels.push(u.language);
  } else if ($langId.checked) {
    labels.push($targetLang.value);
  }
  if (labels.length) {
    const lbl = document.createElement("div");
    lbl.className = "label";
    lbl.textContent = labels.join(" · ");
    div.appendChild(lbl);
  }

  if (final) {
    const finalSpan = document.createElement("span");
    finalSpan.textContent = final;
    div.appendChild(finalSpan);
  }
  if (partial) {
    const partialSpan = document.createElement("span");
    partialSpan.className = "partial";
    partialSpan.textContent = partial;
    div.appendChild(partialSpan);
  }

  col.appendChild(div);
}

function render() {
  $originalCol.innerHTML = "";
  $translationCol.innerHTML = "";
  const all = [...utterances, currentUtt];
  for (const u of all) {
    renderUtterance(u, $originalCol, "original");
    renderUtterance(u, $translationCol, "translation");
  }
  syncRowHeights();
  $originalCol.scrollTop = $originalCol.scrollHeight;
  $translationCol.scrollTop = $translationCol.scrollHeight;
}

// The two columns render into separate DOM trees so each utterance picks its
// own height from its own text. Pair them up by index and stretch both boxes
// of each pair to the taller one, so the columns stay aligned row-by-row.
function syncRowHeights() {
  const o = $originalCol.children;
  const t = $translationCol.children;
  for (const el of o) el.style.minHeight = "";
  for (const el of t) el.style.minHeight = "";
  const n = Math.min(o.length, t.length);
  for (let i = 0; i < n; i++) {
    const h = Math.max(o[i].offsetHeight, t[i].offsetHeight);
    o[i].style.minHeight = `${h}px`;
    t[i].style.minHeight = `${h}px`;
  }
}

$actionBtn.addEventListener("click", () => {
  if (state !== "idle") {
    stop();
  } else if (mode === "file") {
    playFile();
  } else {
    start();
  }
});

$modeToggle.addEventListener("click", () => {
  if (state === "idle") setMode(mode === "file" ? "mic" : "file");
});

$audioUrl.addEventListener("input", () => {
  if (state === "idle" && mode === "file") {
    $actionBtn.disabled = !$audioUrl.value.trim();
  }
});

setMode("file");
