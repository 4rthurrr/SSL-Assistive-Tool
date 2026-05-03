console.log('🚀 SSL App v2 Loading...');

// ─── Configuration ────────────────────────────────────────────────
const API_URL = 'http://127.0.0.1:8001';
const SEQUENCE_LENGTH   = 50;
const FRAME_INTERVAL    = 50;        // 20 FPS
const RECORDING_DURATION= 4000;      // 4 s single-shot (was 5 s)
const REAL_TEST_PREP_MS = 800;
const VOTE_ROUND_DURATION= 3000;     // 3 s per round in voting mode
const VOTE_ROUNDS       = 3;
const AUTO_SLIDE_STEP   = 15;        // Slide window by 15 frames in auto-mode
const QUALITY_THRESHOLD = 0.35;      // Min avg visibility to count a frame (relaxed from 0.45)
const RECORD_QUALITY_THRESHOLD = 0.20; // Recording tolerates imperfect frames; backend normalizes
const MIN_RECORD_FRAMES = 10;
const ANCHOR_VIS_THRESH = 0.25;      // Min visibility for normalization anchors (relaxed for demo)
const AUTO_MIN_CONFIDENCE = 20;      // Lowered — backend now sharpens via temperature scaling
const AUTO_MIN_MARGIN = 6;           // Top-1 should beat top-2 by at least this much
const AUTO_SAFE_CONFIDENCE = 30;
const AUTO_SAFE_MARGIN = 10;
const AUTO_BUFFER_SIZE  = 5;         // Larger buffer = more stable temporal smoothing
const AUTO_SWITCH_MIN_CONFIDENCE = 30;
const AUTO_IDLE_RESET_MS = 1500;     // Slightly longer to avoid premature resets
const AUTO_REQUEST_COOLDOWN_MS = 700; // Slightly faster for responsiveness
const MIN_SEQUENCE_HAND_RATE = 0.15; // Relaxed — some signs are primarily pose-based
const RECORD_MAX_SEQUENCES = 5;      // More windows = better ensemble averaging
const RECORD_WINDOW_STEP = 6;        // Denser window sampling
const MOTION_THRESHOLD  = 0.008;     // Lower threshold — catch subtler signs

// ─── Demo Mode Config ─────────────────────────────────────────────
const DEMO_BUFFER_SIZE  = 5;     // Rolling window: vote across last N results
const DEMO_TEMP         = 0.5;   // Temperature for confidence sharpening (0.5 = square+renorm)
const DEMO_HIGH_THRESH  = 40;    // Lowered — backend sharpening already boosts confidence
const DEMO_MID_THRESH   = 22;    // Lowered — with 353 classes, 22%+ is meaningful

// ─── State ────────────────────────────────────────────────────────
let camera = null;
let holistic = null;
let isCapturing = false;
let isRecording = false;
let isAutoPredict = false;
let isVoting = false;
let isDemoMode = false;
let demoPredBuffer = [];     // Rolling buffer for demo temporal smoothing
let autoPredBuffer = [];     // Rolling buffer for auto-predict temporal smoothing
let collectedFrames = [];
let autoBuffer = [];         // Sliding window buffer for auto-predict
let mediapipeReady = false;
let predictionHistory = [];  // Last 8 predictions for history panel
let currentQuality = 0;      // Live landmark quality 0-1
let emaConfidence = 0;        // EMA-smoothed confidence for display
let autoPredictionInFlight = false;
let autoSessionId = 0;
let lastAutoActivityAt = 0;
let lastAutoRequestAt = 0;

// ─── DOM refs ─────────────────────────────────────────────────────
const elements = {
    webcam:          document.getElementById('webcam'),
    canvas:          document.getElementById('canvas'),
    overlay:         document.getElementById('overlay'),
    startBtn:        document.getElementById('startBtn'),
    stopBtn:         document.getElementById('stopBtn'),
    recordBtn:       document.getElementById('recordBtn'),
    voteBtn:         document.getElementById('voteBtn'),
    autoBtn:         document.getElementById('autoBtn'),
    serverDot:       document.getElementById('serverDot'),
    serverStatus:    document.getElementById('serverStatus'),
    mediapipeDot:    document.getElementById('mediapipeDot'),
    mediapipeStatus: document.getElementById('mediapipeStatus'),
    handDot:         document.getElementById('handDot'),
    handStatus:      document.getElementById('handStatus'),
    loading:         document.getElementById('loading'),
    errorMessage:    document.getElementById('errorMessage'),
    results:         document.getElementById('results'),
    mainSinhala:     document.getElementById('mainSinhala'),
    mainEnglish:     document.getElementById('mainEnglish'),
    mainCategory:    document.getElementById('mainCategory'),
    mainConfidence:  document.getElementById('mainConfidence'),
    topPredictions:  document.getElementById('topPredictions'),
    voteProgress:    document.getElementById('voteProgress'),
    voteProgressText:document.getElementById('voteProgressText'),
    autoIndicator:   document.getElementById('autoIndicator'),
    qualityBar:      document.getElementById('qualityBar'),
    qualityLabel:    document.getElementById('qualityLabel'),
    predHistory:     document.getElementById('predHistory'),
    historyList:     document.getElementById('historyList'),
    demoBtn:         document.getElementById('demoBtn'),
};

// ─── Init ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ DOM Ready');
    initializeApp();
});

async function initializeApp() {
    elements.startBtn.addEventListener('click', startCamera);
    elements.stopBtn.addEventListener('click', stopCamera);
    elements.recordBtn.addEventListener('click', startRecording);
    elements.voteBtn.addEventListener('click', startVoting);
    elements.autoBtn.addEventListener('click', toggleAutoPredict);
    elements.demoBtn.addEventListener('click', toggleDemoMode);
    await initializeMediaPipe();
    checkServer();
    setInterval(checkServer, 5000);
}

// ─── MediaPipe ────────────────────────────────────────────────────
async function initializeMediaPipe() {
    try {
        console.log('⏳ Initializing MediaPipe Holistic...');
        updateMediaPipeStatus('loading');

        holistic = new Holistic({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/holistic/${file}`
        });

        holistic.setOptions({
            modelComplexity: 1,          // IMPROVED: Full model for better accuracy
            smoothLandmarks: true,        // IMPROVED: Smooth out jitter
            enableSegmentation: false,
            smoothSegmentation: false,
            refineFaceLandmarks: false,
            minDetectionConfidence: 0.5,  // IMPROVED: Higher quality threshold
            minTrackingConfidence: 0.5    // IMPROVED: Higher quality threshold
        });

        holistic.onResults(onHolisticResults);

        mediapipeReady = true;
        updateMediaPipeStatus('ready');
        console.log('✅ MediaPipe Holistic Ready (complexity=1, smooth=true)');
    } catch (error) {
        console.error('❌ MediaPipe Error:', error);
        updateMediaPipeStatus('error');
    }
}

// ─── Server ───────────────────────────────────────────────────────
async function fetchWithTimeout(url, options = {}, timeoutMs = 2500) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
        return await fetch(url, { ...options, signal: controller.signal });
    } finally {
        clearTimeout(timer);
    }
}

async function checkServer() {
    try {
        const response = await fetchWithTimeout(`${API_URL}/health`, {}, 2500);
        const data = await response.json();
        if (data.status === 'healthy' && data.model_loaded) updateServerStatus('connected');
        else updateServerStatus('error');
    } catch { updateServerStatus('error'); }
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ─── Camera ───────────────────────────────────────────────────────
async function startCamera() {
    try {
        console.log('📷 Starting camera...');
        showOverlay('Starting camera...');

        if (!mediapipeReady) throw new Error('MediaPipe not ready');

        camera = new Camera(elements.webcam, {
            onFrame: async () => {
                if (holistic && isCapturing) {
                    await holistic.send({ image: elements.webcam });
                }
            },
            width: 640,
            height: 480
        });

        await camera.start();
        isCapturing = true;
        hideOverlay();
        updateButtons();
        hideError();
        console.log('✅ Camera started');
    } catch (error) {
        console.error('❌ Camera error:', error);
        showError(error.message);
    }
}

function stopCamera() {
    if (camera) { camera.stop(); camera = null; }
    isCapturing  = false;
    isRecording  = false;
    isVoting     = false;
    collectedFrames = [];
    setAutoPredict(false);
    elements.voteProgress.classList.remove('active');
    showOverlay('Click "Start Camera" to begin');
    updateButtons();
    console.log('⏹️ Camera stopped');
}

// ─── Frame quality helper ─────────────────────────────────────────
/**
 * Returns a 0-1 quality score for a pose results object.
 * Uses average visibility of key upper-body landmarks.
 */
function computeFrameQuality(poseLandmarks) {
    if (!poseLandmarks) return 0;
    // Key landmarks: nose(0), shoulders(11,12), elbows(13,14), wrists(15,16), hips(23,24)
    const keyIdxs = [0, 11, 12, 13, 14, 15, 16, 23, 24];
    let sum = 0;
    for (const i of keyIdxs) {
        sum += (poseLandmarks[i] && poseLandmarks[i].visibility !== undefined)
            ? poseLandmarks[i].visibility : 0;
    }
    return sum / keyIdxs.length;
}

/**
 * Check that the 4 normalization anchor landmarks (shoulders + hips)
 * have adequate visibility. Bad anchors → bad normalization → bad prediction.
 */
function checkAnchorVisibility(poseLandmarks) {
    if (!poseLandmarks) return false;
    const anchors = [11, 12, 23, 24]; // L shoulder, R shoulder, L hip, R hip
    for (const i of anchors) {
        const vis = poseLandmarks[i]?.visibility ?? 0;
        if (vis < ANCHOR_VIS_THRESH) return false;
    }
    return true;
}

function hasHandLandmarks(results) {
    return Boolean(
        (results.leftHandLandmarks && results.leftHandLandmarks.length > 0) ||
        (results.rightHandLandmarks && results.rightHandLandmarks.length > 0)
    );
}

function getFrameHandPresence(frame) {
    if (!frame || frame.length < 300) return 0;
    for (let base = 132; base < 300; base += 4) {
        if ((frame[base + 3] || 0) > 0) return 1;
    }
    return 0;
}

function getSequenceHandRate(frames) {
    if (!frames || frames.length === 0) return 0;
    return frames.reduce((sum, frame) => sum + getFrameHandPresence(frame), 0) / frames.length;
}

function getSequenceMotionScore(frames) {
    if (!frames || frames.length < 2) return 0;
    let score = 0;
    for (let i = 1; i < frames.length; i++) {
        const prev = frames[i - 1];
        const curr = frames[i];
        const leftDx = (curr[60] || 0) - (prev[60] || 0);
        const leftDy = (curr[61] || 0) - (prev[61] || 0);
        const rightDx = (curr[64] || 0) - (prev[64] || 0);
        const rightDy = (curr[65] || 0) - (prev[65] || 0);
        score += Math.sqrt(leftDx * leftDx + leftDy * leftDy);
        score += Math.sqrt(rightDx * rightDx + rightDy * rightDy);
    }
    return score / (frames.length - 1);
}

function scorePredictionWindow(frames, start, targetLength = SEQUENCE_LENGTH) {
    const windowFrames = frames.slice(start, start + targetLength);
    const handRate = getSequenceHandRate(windowFrames);
    const motion = getSequenceMotionScore(windowFrames);
    const lastStart = Math.max(0, frames.length - targetLength);
    const tailBias = lastStart > 0 ? start / lastStart : 0;
    return handRate * 2 + motion * 12 + tailBias * 0.2;
}

function makePredictionSequences(frames, targetLength = SEQUENCE_LENGTH, maxSequences = RECORD_MAX_SEQUENCES) {
    if (!frames || frames.length === 0) return [];
    if (frames.length < targetLength) return [interpolateFrames(frames, targetLength)];

    const lastStart = frames.length - targetLength;
    const candidates = [];
    const starts = [];

    for (let start = 0; start <= lastStart; start += RECORD_WINDOW_STEP) {
        starts.push(start);
    }
    if (starts[starts.length - 1] !== lastStart) starts.push(lastStart);

    for (const start of starts) {
        const windowFrames = frames.slice(start, start + targetLength);
        const handRate = getSequenceHandRate(windowFrames);
        if (handRate < MIN_SEQUENCE_HAND_RATE) continue;
        candidates.push({
            start,
            score: scorePredictionWindow(frames, start, targetLength),
        });
    }

    if (candidates.length === 0) {
        let bestStart = lastStart;
        let bestScore = -Infinity;
        for (const start of starts) {
            const score = scorePredictionWindow(frames, start, targetLength);
            if (score > bestScore) {
                bestScore = score;
                bestStart = start;
            }
        }
        return [frames.slice(bestStart, bestStart + targetLength).map(frame => [...frame])];
    }

    candidates.sort((a, b) => b.score - a.score);
    const selected = [];
    const minStartGap = Math.max(RECORD_WINDOW_STEP, Math.floor(targetLength / 5));

    for (const candidate of candidates) {
        if (selected.every(item => Math.abs(item.start - candidate.start) >= minStartGap)) {
            selected.push(candidate);
            if (selected.length >= maxSequences) break;
        }
    }

    if (selected.length === 0) selected.push(candidates[0]);
    selected.sort((a, b) => a.start - b.start);
    return selected.map(item =>
        frames.slice(item.start, item.start + targetLength).map(frame => [...frame])
    );
}

function makePredictionSequence(frames, targetLength = SEQUENCE_LENGTH) {
    const sequences = makePredictionSequences(frames, targetLength, 1);
    return sequences[0] || [];
}

// ─── Holistic result handler ───────────────────────────────────────
function onHolisticResults(results) {
    const ctx = elements.canvas.getContext('2d');
    ctx.save();
    if (elements.canvas.width !== results.image.width || elements.canvas.height !== results.image.height) {
        elements.canvas.width = results.image.width;
        elements.canvas.height = results.image.height;
    }
    ctx.clearRect(0, 0, elements.canvas.width, elements.canvas.height);

    let hasLandmarks = false;

    if (results.faceLandmarks) {
        drawConnectors(ctx, results.faceLandmarks, FACEMESH_TESSELATION, { color: '#C0C0C070', lineWidth: 1 });
        hasLandmarks = true;
    }
    if (results.poseLandmarks) {
        drawConnectors(ctx, results.poseLandmarks, POSE_CONNECTIONS, { color: '#00FF00', lineWidth: 4 });
        drawLandmarks(ctx, results.poseLandmarks, { color: '#FF0000', lineWidth: 2, radius: 4 });
        hasLandmarks = true;
    }
    if (results.leftHandLandmarks) {
        drawConnectors(ctx, results.leftHandLandmarks, HAND_CONNECTIONS, { color: '#CC0000', lineWidth: 3 });
        drawLandmarks(ctx, results.leftHandLandmarks, { color: '#00FF00', lineWidth: 2, radius: 3 });
        hasLandmarks = true;
    }
    if (results.rightHandLandmarks) {
        drawConnectors(ctx, results.rightHandLandmarks, HAND_CONNECTIONS, { color: '#0000CC', lineWidth: 3 });
        drawLandmarks(ctx, results.rightHandLandmarks, { color: '#FF0000', lineWidth: 2, radius: 3 });
        hasLandmarks = true;
    }

    // Landmark quality indicator (live)
    const quality = computeFrameQuality(results.poseLandmarks);
    currentQuality = quality;
    updateQualityBar(quality);

    if (hasLandmarks) {
        const parts = [];
        if (results.poseLandmarks)      parts.push('pose');
        if (results.leftHandLandmarks)  parts.push('L-hand');
        if (results.rightHandLandmarks) parts.push('R-hand');
        updateHandStatus(`detected (${parts.join(', ')})`);
    } else {
        updateHandStatus('not-detected');
    }

    // ── Frame collection (single-shot recording) ─────
    if (isRecording && results.poseLandmarks) {
        const frame = extractFullFrame(results.poseLandmarks, results.leftHandLandmarks, results.rightHandLandmarks);
        // Recording should not require hands on every frame. The training data
        // contains many frames with temporarily missing hands, so collect usable
        // pose frames and let sequence selection prefer hand-visible windows.
        const acceptFrame = quality >= RECORD_QUALITY_THRESHOLD && checkAnchorVisibility(results.poseLandmarks);
        if (acceptFrame) {
            collectedFrames.push(frame);
        }
    }

    // ── Auto-predict sliding window ───────────────────
    if (isAutoPredict && results.poseLandmarks) {
        lastAutoActivityAt = Date.now();
        const frame = extractFullFrame(results.poseLandmarks, results.leftHandLandmarks, results.rightHandLandmarks);
        autoBuffer.push(frame);

        if (autoBuffer.length >= SEQUENCE_LENGTH) {
            const seq = autoBuffer.slice(0, SEQUENCE_LENGTH);
            autoBuffer.splice(0, AUTO_SLIDE_STEP); // slide window
            queueAutoPrediction(seq);
        }
    } else if (isAutoPredict) {
        maybeResetAutoAfterGap('tracking gap');
    }

    ctx.restore();
}

/**
 * Motion gate: checks if wrist landmarks moved enough across the sequence
 * to indicate an actual sign is being performed (not idle/resting).
 */
function hasSignificantMotion(frames) {
    const n = frames.length;
    if (n < 20) return true; // too short to judge, allow it
    const first10 = frames.slice(0, 10);
    const last10  = frames.slice(n - 10);
    // Landmark 15 = right wrist (index 60-63), landmark 16 = left wrist (index 64-67)
    let f_rx = 0, f_ry = 0, f_lx = 0, f_ly = 0;
    let l_rx = 0, l_ry = 0, l_lx = 0, l_ly = 0;
    for (const f of first10) { f_rx += f[60]; f_ry += f[61]; f_lx += f[64]; f_ly += f[65]; }
    for (const f of last10)  { l_rx += f[60]; l_ry += f[61]; l_lx += f[64]; l_ly += f[65]; }
    const dx_r = (l_rx - f_rx) / 10, dy_r = (l_ry - f_ry) / 10;
    const dx_l = (l_lx - f_lx) / 10, dy_l = (l_ly - f_ly) / 10;
    const motionR = Math.sqrt(dx_r * dx_r + dy_r * dy_r);
    const motionL = Math.sqrt(dx_l * dx_l + dy_l * dy_l);
    return Math.max(motionR, motionL) > MOTION_THRESHOLD;
}

/**
 * Extract 300 raw features from MediaPipe Holistic results:
 * 33 pose × 4 + 21 left hand × 4 + 21 right hand × 4 = 300 features.
 */
function extractFullFrame(poseLandmarks, leftHandLandmarks, rightHandLandmarks) {
    const frame = [];

    // Pose landmarks (33 × 4 = 132)
    for (let i = 0; i < 33; i++) {
        if (poseLandmarks && poseLandmarks[i]) {
            frame.push(
                poseLandmarks[i].x,
                poseLandmarks[i].y,
                poseLandmarks[i].z || 0,
                poseLandmarks[i].visibility !== undefined ? poseLandmarks[i].visibility : 1.0
            );
        } else {
            frame.push(0, 0, 0, 0);
        }
    }

    // Left hand landmarks (21 × 4 = 84)
    for (let i = 0; i < 21; i++) {
        if (leftHandLandmarks && leftHandLandmarks[i]) {
            frame.push(
                leftHandLandmarks[i].x,
                leftHandLandmarks[i].y,
                leftHandLandmarks[i].z || 0,
                1.0
            );
        } else {
            frame.push(0, 0, 0, 0);
        }
    }

    // Right hand landmarks (21 × 4 = 84)
    for (let i = 0; i < 21; i++) {
        if (rightHandLandmarks && rightHandLandmarks[i]) {
            frame.push(
                rightHandLandmarks[i].x,
                rightHandLandmarks[i].y,
                rightHandLandmarks[i].z || 0,
                1.0
            );
        } else {
            frame.push(0, 0, 0, 0);
        }
    }

    return frame; // 300 values
}

// ─── Single-shot Recording ────────────────────────────────────────
async function startRecording() {
    if (!isCapturing || isRecording || isVoting || isAutoPredict) return;

    isRecording = true;
    collectedFrames = [];
    updateButtons();
    console.log('🎬 Recording started (4 s, quality-gated)...');

    await delay(RECORDING_DURATION);

    isRecording = false;
    updateButtons();
    console.log(`✅ Collected ${collectedFrames.length} quality frames`);

    if (collectedFrames.length >= MIN_RECORD_FRAMES) {
        const sequences = makePredictionSequences(collectedFrames);
        await sendRecordingPrediction(sequences);
    } else {
        showError(`Only ${collectedFrames.length} quality frames captured. Keep your shoulders visible and try again.`);
    }
}

// ─── 3× Voting Mode ───────────────────────────────────────────────
async function sendRecordingPrediction(sequences) {
    if (!sequences || sequences.length === 0) return;
    if (sequences.length === 1) {
        await sendPrediction(sequences[0]);
        return;
    }

    elements.loading.classList.add('active');
    elements.results.style.display = 'none';
    hideError();

    try {
        const payload = { sequences: sequences.map(seq => seq.map(f => ({ landmarks: f }))) };
        const response = await fetch(`${API_URL}/predict-ensemble`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error('Recording ensemble API error ' + response.status);
        const result = await response.json();
        displayResults(result, false, true);
        console.log(`Recording stable result (${sequences.length} windows): ${result.prediction} (${result.confidence.toFixed(1)}%)`);
    } catch (error) {
        console.error('Recording ensemble error:', error);
        showError('Failed to get recording prediction: ' + error.message);
    } finally {
        elements.loading.classList.remove('active');
    }
}

async function startVoting() {
    if (!isCapturing || isVoting || isRecording || isAutoPredict) return;

    isVoting = true;
    updateButtons();
    elements.voteProgress.classList.add('active');
    hideError();

    const allSequences = [];
    const dots = [
        document.getElementById('dot1'),
        document.getElementById('dot2'),
        document.getElementById('dot3'),
    ];
    dots.forEach(d => { d.className = 'vote-round-dot'; });

    for (let round = 0; round < VOTE_ROUNDS; round++) {
        dots[round].classList.add('active');
        elements.voteProgressText.textContent = `🎬 Round ${round + 1}/${VOTE_ROUNDS} — hold your sign...`;
        collectedFrames = [];
        isRecording = true;

        await delay(VOTE_ROUND_DURATION);

        isRecording = false;
        dots[round].className = 'vote-round-dot done';

        if (collectedFrames.length >= MIN_RECORD_FRAMES) {
            const seq = makePredictionSequence(collectedFrames);
            allSequences.push(seq);
            elements.voteProgressText.textContent = `✅ Round ${round + 1} captured (${collectedFrames.length} frames)`;
        } else {
            elements.voteProgressText.textContent = `Round ${round + 1} skipped - too few quality frames`;
        }

        if (round < VOTE_ROUNDS - 1) await delay(400);
    }

    isVoting = false;
    elements.voteProgress.classList.remove('active');
    updateButtons();

    if (allSequences.length === 0) {
        showError('No sequences collected — check camera and lighting.');
        return;
    }

    // ── Server-side ensemble (probability averaging) ─────────────
    // Send all sequences to /predict-ensemble for proper softmax averaging.
    // Falls back to single prediction if only 1 sequence was captured.
    elements.loading.classList.add('active');
    elements.voteProgressText.textContent = `⏳ Running ${allSequences.length}-shot ensemble prediction...`;

    try {
        let result;
        if (allSequences.length >= 2) {
            const payload = { sequences: allSequences.map(seq => seq.map(f => ({ landmarks: f }))) };
            const response = await fetch(`${API_URL}/predict-ensemble`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!response.ok) throw new Error('Ensemble API error ' + response.status);
            result = await response.json();
        } else {
            // Only 1 sequence captured — fall back to single prediction
            result = await fetchSinglePrediction(allSequences[0]);
        }

        if (result) {
            displayResults(result, false, true);
            elements.results.style.display = 'block';
            console.log(`🎯 Ensemble (${allSequences.length} shots): ${result.prediction} (${result.confidence.toFixed(1)}%)`);
        } else {
            showError('Ensemble prediction failed.');
        }
    } catch (error) {
        console.error('❌ Ensemble error:', error);
        showError('Ensemble prediction failed: ' + error.message);
    } finally {
        elements.loading.classList.remove('active');
    }
}

// ─── Auto-Predict Toggle ──────────────────────────────────────────
function toggleAutoPredict() {
    if (isRecording || isVoting) return;

    setAutoPredict(!isAutoPredict);
    console.log(`Auto-predict: ${isAutoPredict ? 'ON' : 'OFF'}`);
}

function setAutoPredict(enabled) {
    isAutoPredict = enabled;
    autoBuffer = [];
    resetAutoPredictionState();
    elements.autoBtn.classList.toggle('active', isAutoPredict);
    elements.autoIndicator.classList.toggle('active', isAutoPredict);
    elements.autoBtn.textContent = isAutoPredict ? '⏹ Stop Auto' : '⚡ Auto Predict';
    updateButtons();
}

function resetAutoPredictionState() {
    autoPredBuffer = [];
    emaConfidence = 0;
    autoPredictionInFlight = false;
    lastAutoActivityAt = 0;
    lastAutoRequestAt = 0;
    autoSessionId += 1;
}

function maybeResetAutoAfterGap(reason) {
    if (!isAutoPredict) return;
    const now = Date.now();
    if (!lastAutoActivityAt) {
        lastAutoActivityAt = now;
        return;
    }
    if (now - lastAutoActivityAt < AUTO_IDLE_RESET_MS) return;
    if (autoBuffer.length || autoPredBuffer.length || emaConfidence > 0) {
        autoBuffer = [];
        resetAutoPredictionState();
        console.log(`Auto context reset after ${reason}`);
    }
}

function queueAutoPrediction(seq) {
    const now = Date.now();
    if (autoPredictionInFlight || now - lastAutoRequestAt < AUTO_REQUEST_COOLDOWN_MS) return;

    autoPredictionInFlight = true;
    lastAutoRequestAt = now;
    const session = autoSessionId;
    sendPrediction(seq, true, session).finally(() => {
        if (session === autoSessionId) autoPredictionInFlight = false;
    });
}

function getPredictionMargin(result) {
    if (!result || !Array.isArray(result.top_3) || result.top_3.length < 2) return 100;
    const top1 = Number(result.top_3[0].confidence ?? result.confidence ?? 0);
    const top2 = Number(result.top_3[1].confidence ?? 0);
    return top1 - top2;
}

function shouldAcceptAutoResult(result) {
    const confidence = Number(result?.confidence ?? 0);
    const margin = getPredictionMargin(result);

    if (confidence < AUTO_MIN_CONFIDENCE) {
        return {
            ok: false,
            reason: `low confidence ${confidence.toFixed(1)}%`,
        };
    }
    if (margin < AUTO_MIN_MARGIN) {
        return {
            ok: false,
            reason: `ambiguous margin ${margin.toFixed(1)}%`,
        };
    }
    if (confidence < AUTO_SAFE_CONFIDENCE && margin < AUTO_SAFE_MARGIN) {
        return {
            ok: false,
            reason: `not stable enough (${confidence.toFixed(1)}%, margin ${margin.toFixed(1)}%)`,
        };
    }
    return { ok: true, reason: '' };
}

// ─── Frame resampling (nearest-neighbor) ──────────────────────────
// Uses nearest real frame instead of linear interpolation to avoid
// creating blended ghost poses the model never saw during training.
function interpolateFrames(frames, targetLength) {
    const result = [];
    const ratio = (frames.length - 1) / (targetLength - 1);
    for (let i = 0; i < targetLength; i++) {
        const idx = Math.round(i * ratio);
        result.push([...frames[idx]]);
    }
    console.log(`📈 Resampled ${frames.length} → ${result.length} frames (nearest-neighbor)`);
    return result;
}

// ─── Send single prediction ───────────────────────────────────────
async function sendPrediction(frames, isAuto = false, autoSession = null) {
    try {
        if (!isAuto) {
            elements.loading.classList.add('active');
            elements.results.style.display = 'none';
        }

        // Send raw frames — normalization is done server-side to match the training pipeline
        const payload = { sequence: frames.map(f => ({ landmarks: f })) };

        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Prediction API error ' + response.status);

        const result = await response.json();

        if (isAuto && autoSession !== autoSessionId) {
            console.log('Auto: discarded stale prediction response');
            return;
        }

        // Auto-predict: apply confidence gate + temporal smoothing to reduce flickering
        if (isAuto) {
            const smoothed = applyAutoFilter(result);
            displayResults(smoothed, true);
            console.log(`✅ Auto: ${smoothed.prediction} (${smoothed.confidence.toFixed(1)}%) [raw: ${result.prediction} ${result.confidence.toFixed(1)}%]`);
        } else {
            displayResults(result, false);
            console.log(`✅ Prediction: ${result.prediction} (${result.confidence.toFixed(1)}%)`);
        }
    } catch (error) {
        console.error('❌ Prediction error:', error);
        if (!isAuto) showError('Failed to get prediction: ' + error.message);
    } finally {
        if (!isAuto) elements.loading.classList.remove('active');
    }
}

// ─── Fetch single prediction (no UI side effects) ──────────────
async function fetchSinglePrediction(frames) {
    try {
        // Send raw frames — normalization is done server-side to match the training pipeline
        const payload = { sequence: frames.map(f => ({ landmarks: f })) };
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) return null;
        return await response.json();
    } catch { return null; }
}

// ─── Demo Mode: temperature sharpening ───────────────────────────
// Raises each top-3 probability to power (1/DEMO_TEMP), then renormalizes
// so the distribution sum is preserved. With T=0.5 (power=2):
//   40% raw leader → ~65% sharpened  |  25% raw → ~38%  |  55% raw → ~80%
function sharpenTop3(top3) {
    const power  = 1 / DEMO_TEMP;
    const probs  = top3.map(p => p.confidence / 100);
    const sharp  = probs.map(p => Math.pow(Math.max(p, 1e-9), power));
    const origSum = probs.reduce((a, b) => a + b, 0);
    const newSum  = sharp.reduce((a, b) => a + b, 0);
    return top3.map((p, i) => ({
        ...p,
        confidence: parseFloat(((sharp[i] / newSum) * origSum * 100).toFixed(2))
    }));
}

// ─── Demo Mode: temporal vote buffer ─────────────────────────────
// Keeps last DEMO_BUFFER_SIZE raw results. Winner = most-voted top-1 sign.
// Displayed confidence = BEST reading for that sign seen in the buffer.
// This eliminates flickering and surfaces the model's peak performance.
function applyTemporalFilter(result, buffer, bufferSize, sharpenConfidence = false) {
    buffer.push(result);
    if (buffer.length > bufferSize) buffer.shift();

    // Tally votes and max confidence per sign
    const votes    = {};
    const sumConf  = {};
    const bestResult = {};
    for (const r of buffer) {
        const s = r.prediction;
        votes[s]   = (votes[s] || 0) + 1;
        sumConf[s] = (sumConf[s] || 0) + r.confidence;
        if (!bestResult[s] || r.confidence > bestResult[s].confidence) {
            bestResult[s] = r;
        }
    }

    // Pick winner: most votes, tiebreak by average confidence
    const winner = Object.keys(votes).sort(
        (a, b) => votes[b] - votes[a] || (sumConf[b]/votes[b]) - (sumConf[a]/votes[a])
    )[0];

    // Return winner's best snapshot with averaged confidence.
    const out      = { ...bestResult[winner] };
    out.confidence  = sumConf[winner] / votes[winner]; // average, not max
    if (sharpenConfidence) {
        out.top_3 = sharpenTop3(out.top_3);
        const top1Entry = out.top_3.find(p => p.sign === winner);
        if (top1Entry) out.confidence = top1Entry.confidence;
    } else {
        out.top_3 = out.top_3.map(p => ({ ...p }));
        const top1Entry = out.top_3.find(p => p.sign === winner);
        if (top1Entry) top1Entry.confidence = out.confidence;
    }
    return out;
}

// Convenience wrappers for the two temporal filter buffers
function applyDemoFilter(result) {
    return applyTemporalFilter(result, demoPredBuffer, DEMO_BUFFER_SIZE, true);
}

function getTemporalWinner(buffer) {
    if (!buffer || buffer.length === 0) return null;
    const votes = {};
    const sumConf = {};
    for (const r of buffer) {
        votes[r.prediction] = (votes[r.prediction] || 0) + 1;
        sumConf[r.prediction] = (sumConf[r.prediction] || 0) + r.confidence;
    }
    const sign = Object.keys(votes).sort(
        (a, b) => votes[b] - votes[a] || (sumConf[b] / votes[b]) - (sumConf[a] / votes[a])
    )[0];
    return {
        sign,
        votes: votes[sign],
        avgConfidence: sumConf[sign] / votes[sign],
    };
}

function applyAutoFilter(result) {
    const winner = getTemporalWinner(autoPredBuffer);
    if (
        winner &&
        result.prediction !== winner.sign &&
        result.confidence >= AUTO_SWITCH_MIN_CONFIDENCE &&
        result.confidence >= winner.avgConfidence * 0.8
    ) {
        autoPredBuffer = [];
        emaConfidence = 0;
        console.log(`Auto: switching from ${winner.sign} to ${result.prediction}`);
    }
    return applyTemporalFilter(result, autoPredBuffer, AUTO_BUFFER_SIZE, false);
}

// ─── Toggle Demo Mode ─────────────────────────────────────────────
function toggleDemoMode() {
    isDemoMode = !isDemoMode;
    demoPredBuffer = [];  // Reset buffer each toggle
    elements.demoBtn.textContent = isDemoMode ? '🎯 Demo Mode: ON' : '🎯 Demo Mode: OFF';
    elements.demoBtn.classList.toggle('active', isDemoMode);
    console.log(`🎯 Demo mode: ${isDemoMode ? 'ON (temporal vote + confidence sharpening)' : 'OFF'}`);
    if (isDemoMode) {
        // Flash a quick toast
        const toast = document.createElement('div');
        toast.textContent = '🎯 Demo Mode ON — predictions stabilized & sharpened';
        Object.assign(toast.style, {
            position:'fixed', bottom:'30px', left:'50%', transform:'translateX(-50%)',
            background:'#ee0979', color:'white', padding:'12px 28px',
            borderRadius:'30px', fontSize:'0.95rem', fontWeight:'700',
            zIndex:'9999', boxShadow:'0 4px 20px rgba(238,9,121,0.5)',
            transition:'opacity 0.5s'
        });
        document.body.appendChild(toast);
        setTimeout(() => { toast.style.opacity='0'; setTimeout(() => toast.remove(), 500); }, 2500);
    }
}

// ─── Display results ──────────────────────────────────────────────
function displayResults(result, isAuto = false, isEnsemble = false) {
    // Apply demo filter if active (temporal vote + confidence sharpening)
    const display = isDemoMode ? applyDemoFilter(result) : result;

    const conf    = display.confidence;
    const hiThr   = isDemoMode ? DEMO_HIGH_THRESH : 50;
    const midThr  = isDemoMode ? DEMO_MID_THRESH  : 30;

    // EMA-smooth confidence to prevent erratic jumping
    const EMA_ALPHA = 0.35;
    emaConfidence = emaConfidence < 1 ? conf : EMA_ALPHA * conf + (1 - EMA_ALPHA) * emaConfidence;
    const smoothConf = isAuto ? emaConfidence : conf; // EMA only for auto-predict

    let confColor   = smoothConf >= hiThr  ? '#2ecc71' : smoothConf >= midThr ? '#f39c12' : '#e74c3c';
    let confWarning = smoothConf >= hiThr  ? ' ✅'      : smoothConf >= midThr ? ' ⚠️'     : ' ❌';
    let modeTag     = isEnsemble ? ' [3× Ensemble]' : isAuto ? ' [Auto]' : '';
    const demoBadge = isDemoMode ? '<span class="demo-badge">🎯 DEMO</span>' : '';

    elements.mainSinhala.textContent    = display.sinhala || display.prediction;
    elements.mainEnglish.innerHTML      = (display.english || display.prediction.split('/')[1] || display.prediction) + demoBadge;
    elements.mainCategory.textContent   = display.prediction + modeTag;
    elements.mainConfidence.textContent = smoothConf.toFixed(1) + '%' + confWarning;
    elements.mainConfidence.style.color = confColor;
    elements.mainConfidence.className = 'conf-badge ' + (smoothConf >= hiThr ? 'conf-high' : smoothConf >= midThr ? 'conf-mid' : 'conf-low');

    elements.topPredictions.innerHTML = display.top_3.map((p, i) => `
        <div class="pred-item">
            <div class="pred-item-text">
                <div class="pred-item-sinhala">${i + 1}. ${p.sinhala || p.sign}</div>
                <div class="pred-item-english">${p.english || p.sign}</div>
            </div>
            <div class="pred-item-confidence" style="color:${p.confidence >= hiThr ? '#28a745' : p.confidence >= midThr ? '#f39c12' : '#dc3545'}">${p.confidence.toFixed(1)}%</div>
        </div>
    `).join('');

    elements.results.style.display = 'block';

    // Add to history using original (unfiltered) result
    addToHistory(result, isEnsemble);

    // Show image generation button
    const imageSection = document.getElementById('imageSection');
    if (imageSection) imageSection.style.display = 'block';
    window.currentPrediction = display.english || display.prediction.split('/')[1] || display.prediction;
    window.currentSinhala = display.sinhala || '';
}

// ─── Prediction history ───────────────────────────────────────────
function addToHistory(result, isEnsemble) {
    predictionHistory.unshift({
        sign:     result.english || result.prediction.split('/')[1] || result.prediction,
        sinhala:  result.sinhala || '—',
        conf:     result.confidence,
        ensemble: isEnsemble
    });
    if (predictionHistory.length > 6) predictionHistory.pop();

    elements.predHistory.style.display = 'block';
    elements.historyList.innerHTML = predictionHistory.map(h => {
        const badge = h.conf >= 70 ? 'badge-high' : h.conf >= 50 ? 'badge-mid' : 'badge-low';
        return `<div class="history-item">
            <span class="history-badge ${badge}">${h.conf.toFixed(0)}%${h.ensemble ? ' 🗳️' : ''}</span>
            <span class="history-sign">${h.sign}</span>
            <span class="history-sinhala">${h.sinhala}</span>
        </div>`;
    }).join('');
}

// ─── Quality bar ──────────────────────────────────────────────────
function updateQualityBar(quality) {
    const pct = Math.round(quality * 100);
    elements.qualityBar.style.width = pct + '%';
    elements.qualityBar.style.background =
        quality >= 0.7 ? '#28a745' : quality >= 0.45 ? '#ffc107' : '#dc3545';
    elements.qualityLabel.textContent =
        quality >= 0.7 ? `Good (${pct}%)` : quality >= 0.45 ? `Fair (${pct}%)` : `Poor (${pct}%) - move back`;
}

function updateHandStatus(status) {
    if (status === 'not-detected') {
        elements.handDot.className = 'status-dot';
        elements.handStatus.textContent = 'Not detected';
    } else {
        elements.handDot.className = 'status-dot connected';
        elements.handStatus.textContent = status;
    }
}

// ─── Button state ─────────────────────────────────────────────────
function updateButtons() {
    const busy = isRecording || isVoting;
    elements.startBtn.disabled = isCapturing;
    elements.stopBtn.disabled  = !isCapturing;
    elements.recordBtn.disabled= !isCapturing || busy || isAutoPredict;
    elements.voteBtn.disabled  = !isCapturing || busy || isAutoPredict;
    elements.autoBtn.disabled  = !isCapturing || busy;
    elements.demoBtn.disabled  = false;
}

// ─── Utility ──────────────────────────────────────────────────────
function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

function showOverlay(text) {
    elements.overlay.textContent = text;
    elements.overlay.classList.remove('hidden');
}
function hideOverlay() { elements.overlay.classList.add('hidden'); }
function showError(msg) {
    elements.errorMessage.textContent = msg;
    elements.errorMessage.classList.add('active');
}
function hideError() { elements.errorMessage.classList.remove('active'); }
function updateServerStatus(s) {
    elements.serverDot.className   = 'status-dot ' + s;
    elements.serverStatus.textContent = s === 'connected' ? 'Connected' : 'Disconnected';
}
function updateMediaPipeStatus(s) {
    elements.mediapipeDot.className   = 'status-dot ' + (s === 'ready' ? 'connected' : s === 'error' ? 'error' : '');
    elements.mediapipeStatus.textContent = s === 'ready' ? 'Ready' : s === 'error' ? 'Error' : 'Loading...';
}

// ─── Image Generation (Token-Safe) ────────────────────────────────
let _imageGenLock = false;
let _imageGenAbort = null;

async function generateImage() {
    const generateBtn    = document.getElementById('generateImageBtn');
    const imageResult    = document.getElementById('imageResult');
    const generatedImage = document.getElementById('generatedImage');
    const captionSinhala = document.getElementById('imageCaptionSinhala');

    if (!window.currentPrediction) {
        alert('No prediction available to generate image!');
        return;
    }

    // Prevent double-fire / allow cancel
    if (_imageGenLock) {
        const abort = confirm('Image generation is already in progress.\n\nCancel the current generation?');
        if (abort && _imageGenAbort) {
            _imageGenAbort.abort();
            _imageGenLock = false;
            generateBtn.disabled = false;
            generateBtn.textContent = '✨ Generate Visual Aid';
        }
        return;
    }

    // Lock the word at click-time so changing predictions don't matter
    const lockedWord    = window.currentPrediction;
    const lockedSinhala = window.currentSinhala || '';

    _imageGenLock = true;
    _imageGenAbort = new AbortController();

    try {
        generateBtn.disabled = true;
        generateBtn.textContent = `⏳ Generating "${lockedWord}"…`;

        const response = await fetch(`${API_URL}/generate-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: _imageGenAbort.signal,
            body: JSON.stringify({
                text: lockedWord,
                sinhala: lockedSinhala,
                style: 'educational, child-friendly, simple illustration, colorful, clear'
            })
        });
        const data = await response.json();
        if (response.status === 429) {
            alert('⏳ ' + (data.detail || 'Image generation quota exhausted. Try again later.'));
        } else if (!response.ok) {
            alert('❌ ' + (data.detail || 'Image generation failed.'));
        } else if (data.success && data.image_url) {
            generatedImage.src = data.image_url;
            imageResult.style.display = 'block';
            if (data.sinhala && captionSinhala) {
                captionSinhala.textContent = data.sinhala;
                captionSinhala.style.display = 'block';
            } else if (captionSinhala) {
                captionSinhala.style.display = 'none';
            }
        } else {
            alert('Failed to generate image: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Image generation cancelled by user');
        } else {
            console.error('Image generation error:', error);
            alert('Network error. Please check if server is running.');
        }
    } finally {
        _imageGenLock = false;
        _imageGenAbort = null;
        generateBtn.disabled = false;
        generateBtn.textContent = '✨ Generate Visual Aid';
    }
}

document.getElementById('generateImageBtn').addEventListener('click', generateImage);

console.log('✅ SSL App v2 Initialized');
