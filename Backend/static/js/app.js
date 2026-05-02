/**
 * app.js  -  Deaf Kids Training System (Flask Web UI)
 *
 * Camera is captured server-side (cv2.VideoCapture) and streamed
 * to the browser as MJPEG via <img src="/video_feed">.
 * This file only handles: letter selection, training flow, status polling.
 */

// ─── DOM refs ──────────────────────────────────────────────────────────────
const letterItems     = document.querySelectorAll('.letter-item');
const startBtn        = document.getElementById('startBtn');
const stopBtn         = document.getElementById('stopBtn');
const statusBar       = document.getElementById('statusBar');
const statusIcon      = document.getElementById('statusIcon');
const statusText      = document.getElementById('statusText');
const practiceVideo   = document.getElementById('practiceVideo');
const practiceSource  = document.getElementById('practiceSource');
const videoPh         = document.getElementById('videoPh');
const resultCard      = document.getElementById('resultCard');
const resultIcon      = document.getElementById('resultIcon');
const resultText      = document.getElementById('resultText');
const resultBar       = document.getElementById('resultBar');
const resultConf      = document.getElementById('resultConfidence');
const infoSelected    = document.getElementById('infoSelected');
const infoPhase       = document.getElementById('infoPhase');
const countdownNum    = document.getElementById('countdownNum');
const countdownCircle = document.getElementById('countdownCircle');
const phaseSteps      = {
  watching:  document.getElementById('ps-watching'),
  countdown: document.getElementById('ps-countdown'),
  recording: document.getElementById('ps-recording'),
  analyzing: document.getElementById('ps-analyzing'),
  result:    document.getElementById('ps-result'),
};

// ─── State ─────────────────────────────────────────────────────────────────
let selectedKey      = null;
let selectedDisplay  = null;
let practiceLoops    = 0;
let studentTurnFired = false;
let pollInterval     = null;
let lastPhase        = 'idle';

// ─── Letter selection ──────────────────────────────────────────────────────
letterItems.forEach(item => {
  item.addEventListener('click', () => {
    if (lastPhase !== 'idle') return;
    letterItems.forEach(i => i.classList.remove('active'));
    item.classList.add('active');
    selectedKey     = item.dataset.key;
    selectedDisplay = item.dataset.display;
    infoSelected.textContent = selectedDisplay;
    startBtn.disabled = false;
    setStatus('💡', `Ready: ${selectedDisplay}`, '');
  });
});

// ─── Start training ────────────────────────────────────────────────────────
startBtn.addEventListener('click', async () => {
  if (!selectedKey) return;
  practiceLoops    = 0;
  studentTurnFired = false;
  resultCard.classList.add('hidden');
  resultCard.classList.remove('ok-card', 'fail-card');

  const res  = await fetch('/start_training', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ letter: selectedKey }),
  });
  const data = await res.json();
  if (!data.ok) return;

  startBtn.disabled = true;
  stopBtn.disabled  = false;
  loadPracticeVideo(selectedKey);
  setStatus('👀', `Watch carefully: ${selectedDisplay}`, 'warn');
  startPolling();
});

// ─── Stop training ─────────────────────────────────────────────────────────
stopBtn.addEventListener('click', async () => {
  await fetch('/stop_training', { method: 'POST' });
  resetUI();
});

// ─── Practice video (3 loops then student turn) ────────────────────────────
function loadPracticeVideo(letterKey) {
  practiceSource.src = `/practice_video/${letterKey.replace(/ /g, '_')}`;
  practiceLoops      = 0;
  studentTurnFired   = false;
  practiceVideo.load();
  practiceVideo.play().catch(() => {});
  videoPh.classList.add('hidden');
}

practiceVideo.addEventListener('ended', () => {
  practiceLoops++;
  if (practiceLoops < 3) {
    practiceVideo.play();
  } else if (!studentTurnFired) {
    studentTurnFired = true;
    practiceVideo.pause();
    setStatus('⏱', 'Get ready! Your turn is coming...', 'warn');
    fetch('/student_turn', { method: 'POST' });
  }
});

// ─── Status polling ────────────────────────────────────────────────────────
function startPolling() {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(pollStatus, 500);
}
function stopPolling() {
  if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
}

async function pollStatus() {
  let data;
  try {
    const res = await fetch('/status');
    data = await res.json();
  } catch (e) { return; }

  const phase = data.phase;
  if (phase === lastPhase && phase !== 'countdown') return;
  lastPhase = phase;

  Object.values(phaseSteps).forEach(el => el.classList.remove('active'));
  if (phaseSteps[phase]) phaseSteps[phase].classList.add('active');
  infoPhase.textContent = capitalize(phase);

  switch (phase) {
    case 'watching':
      setStatus('👀', `Watch the practice video: ${data.display_letter}`, 'warn');
      break;
    case 'countdown':
      const cd = data.countdown;
      countdownNum.textContent = cd > 0 ? cd : '▶';
      countdownCircle.classList.toggle('active', cd > 0);
      setStatus('⏱', `Get ready! Starting in ${cd}...`, 'warn');
      break;
    case 'recording':
      countdownNum.textContent = '🔴';
      countdownCircle.classList.remove('active');
      setStatus('🔴', 'Recording... Show the sign now!', 'danger');
      break;
    case 'analyzing':
      countdownNum.textContent = '🧠';
      setStatus('🧠', 'Analyzing your movement...', '');
      break;
    case 'result':
      stopPolling();
      showResult(data);
      break;
    case 'idle':
      resetUI();
      break;
  }
}

// ─── Result display ────────────────────────────────────────────────────────
function showResult(data) {
  const ok   = data.result_ok;
  const conf = data.result_confidence;
  resultCard.classList.remove('hidden', 'ok-card', 'fail-card');
  resultCard.classList.add(ok ? 'ok-card' : 'fail-card');
  resultIcon.textContent = ok ? '🎉' : '🔄';
  resultText.textContent = data.result_label;
  resultBar.style.width  = Math.min(conf, 100) + '%';
  resultBar.style.background = ok
    ? 'linear-gradient(90deg,#4ade80,#22c55e)'
    : 'linear-gradient(90deg,#f87171,#ef4444)';
  resultConf.textContent = `Confidence: ${conf.toFixed(1)}%`;
  setStatus(ok ? '✅' : '❌', `${data.result_label} — ${conf.toFixed(1)}%`, ok ? 'ok' : 'danger');
  startBtn.disabled        = false;
  stopBtn.disabled         = true;
  infoPhase.textContent    = 'Result';
  countdownNum.textContent = '—';
  countdownCircle.classList.remove('active');
}

// ─── Helpers ──────────────────────────────────────────────────────────────
function setStatus(icon, text, type) {
  statusIcon.textContent = icon;
  statusText.textContent = text;
  statusBar.className    = 'status-bar' + (type ? ' ' + type : '');
}

function resetUI() {
  stopPolling();
  lastPhase        = 'idle';
  practiceLoops    = 0;
  studentTurnFired = false;
  startBtn.disabled = (selectedKey == null);
  stopBtn.disabled  = true;
  setStatus('💡', 'Select a letter and press Start to begin training.', '');
  countdownNum.textContent = '—';
  countdownCircle.classList.remove('active');
  practiceVideo.pause();
  videoPh.classList.remove('hidden');
  Object.values(phaseSteps).forEach(el => el.classList.remove('active'));
  infoPhase.textContent = 'Idle';
}

function capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''; }
