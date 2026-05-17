/* ===================================================
   GESTRA — Canvas Latihan JavaScript
   =================================================== */

function closeKuisSelesaiModal() {
  document.getElementById('modal-selesai').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
  const heading = document.querySelector('.info-header-text h2');
  if (heading) {
    heading.style.cursor = 'pointer';
    heading.addEventListener('click', () => speak('Tulis huruf dibawah ini'));
  }
});

function speak(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = 'id-ID';
  utt.rate = 0.9;
  window.speechSynthesis.speak(utt);
}

// Logika Penulisan
const video = document.getElementById('webcam');
const paintCanvas = document.getElementById('paintCanvas');
const pctx = paintCanvas.getContext('2d');
const cameraOverlay = document.getElementById('cameraOverlay');
const octx = cameraOverlay.getContext('2d');

// Ambil parameter dari config atau URL
const config = window.QUIZ_CONFIG || {};
console.log("GESTRA Quiz Config:", config);

const urlParams = new URLSearchParams(window.location.search);

const targetChar = config.target || urlParams.get('target') || 'A';
const currentMode = config.modeChar || urlParams.get('mode') || 'upper';
const isQuiz = (config.isQuiz === true);
const sessionId = config.sessionId || null;

console.log("Quiz Mode Active:", isQuiz, "| Session:", sessionId);

const latihanId = urlParams.get('latihan_id');
const kelasId = urlParams.get('kelas_id');

// Update Tampilan Target di UI
const targetDisplay = document.querySelector('.target-char');
if (targetDisplay) targetDisplay.innerText = targetChar;

// Set ukuran canvas (sesuaikan dengan workspace)
paintCanvas.width = 640; paintCanvas.height = 480;
cameraOverlay.width = 640; cameraOverlay.height = 480;

let prevPoint = null;
let smoothPoint = null;
const alpha = 0.6;

function resetCanvas() {
    pctx.fillStyle = "white";
    pctx.fillRect(0, 0, paintCanvas.width, paintCanvas.height);
    octx.clearRect(0, 0, cameraOverlay.width, cameraOverlay.height);
}
resetCanvas();

function onResults(results) {
    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        const landmarks = results.multiHandLandmarks[0];
        const rawX = (1 - landmarks[8].x) * paintCanvas.width;
        const rawY = landmarks[8].y * paintCanvas.height;

        if (smoothPoint === null) {
            smoothPoint = { x: rawX, y: rawY };
        } else {
            smoothPoint.x = alpha * rawX + (1 - alpha) * smoothPoint.x;
            smoothPoint.y = alpha * rawY + (1 - alpha) * smoothPoint.y;
        }

        const fingers = {
            index: landmarks[8].y < landmarks[6].y,
            middle: landmarks[12].y < landmarks[10].y,
            ring: landmarks[16].y < landmarks[14].y
        };

        let gesture = (fingers.index && !fingers.middle) ? "DRAW" :
                      (fingers.index && fingers.middle && fingers.ring) ? "ERASE" : "STOP";

        if (gesture === "DRAW") {
            if (prevPoint) {
                pctx.beginPath();
                pctx.strokeStyle = "black";
                pctx.lineWidth = 25;
                pctx.lineCap = "round";
                pctx.moveTo(prevPoint.x, prevPoint.y);
                pctx.lineTo(smoothPoint.x, smoothPoint.y);
                pctx.stroke();

                octx.beginPath();
                octx.strokeStyle = "#3B82F6"; 
                octx.lineWidth = 10;
                octx.lineCap = "round";
                octx.moveTo(prevPoint.x, prevPoint.y);
                octx.lineTo(smoothPoint.x, smoothPoint.y);
                octx.stroke();
            }
            prevPoint = { x: smoothPoint.x, y: smoothPoint.y };
        } 

        else if (gesture === "ERASE") {
            pctx.beginPath();
            pctx.fillStyle = "white";
            pctx.arc(smoothPoint.x, smoothPoint.y, 40, 0, Math.PI * 2);
            pctx.fill();

            octx.globalCompositeOperation = 'destination-out';
            octx.beginPath();
            octx.arc(smoothPoint.x, smoothPoint.y, 45, 0, Math.PI * 2);
            octx.fill();
            octx.globalCompositeOperation = 'source-over';
            
            prevPoint = null;
        } 
        else {
            prevPoint = null;
        }
    } else {
        prevPoint = null;   
        smoothPoint = null;
    }
}

// Helper to dynamically load external scripts in a non-blocking way
function loadScript(url) {
    return new Promise((resolve, reject) => {
        if (document.querySelector(`script[src="${url}"]`)) {
            resolve();
            return;
        }
        const script = document.createElement('script');
        script.src = url;
        script.async = true;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// Global references for MediaPipe instances
let handsInstance = null;
let cameraInstance = null;

async function initCameraAndHandTracking() {
    try {
        // Show playful camera loading state in the video's parent element
        const videoWrapper = video.parentElement;
        const loader = document.createElement('div');
        loader.id = 'camera-loader';
        loader.innerHTML = `
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; width:100%; height:100%; color:white; font-weight:700;">
                <div style="font-size: 3.5rem; animation: bounce-camera-icon 0.8s infinite ease-in-out;">🎥</div>
                <div style="margin-top: 12px; font-size:1.15rem; letter-spacing:-0.3px;">Menghubungkan Kamera...</div>
                <div style="font-size:0.85rem; opacity:0.75; margin-top:4px; font-weight:600;">Tunggu sebentar ya! 😊</div>
            </div>
            <style>
              @keyframes bounce-camera-icon {
                0%, 100% { transform: translateY(0) scale(1); }
                50% { transform: translateY(-12px) scale(1.05); }
              }
            </style>
        `;
        loader.style.cssText = "position:absolute; top:0; left:0; width:100%; height:100%; background:#1E293B; display:flex; z-index:100; justify-content:center; align-items:center; border-radius:12px;";
        videoWrapper.appendChild(loader);

        // Load MediaPipe scripts dynamically & in parallel!
        console.log("Loading MediaPipe scripts in parallel...");
        await Promise.all([
            loadScript("https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1646424915/hands.js"),
            loadScript("https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js")
        ]);
        console.log("MediaPipe scripts loaded successfully!");

        // Initialize Hands
        handsInstance = new Hands({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1646424915/${file}`
        });
        handsInstance.setOptions({ 
            maxNumHands: 1, 
            modelComplexity: 1, 
            minDetectionConfidence: 0.5, 
            minTrackingConfidence: 0.5 
        });
        handsInstance.onResults(onResults);

        // Initialize Camera
        cameraInstance = new Camera(video, {
            onFrame: async () => { 
                if (handsInstance) {
                    await handsInstance.send({ image: video }); 
                }
            },
            width: 640,
            height: 480
        });

        console.log("Starting webcam...");
        await cameraInstance.start();
        console.log("Webcam started successfully!");
        
        // Hide loader smoothly
        loader.style.transition = "opacity 0.4s ease";
        loader.style.opacity = "0";
        setTimeout(() => loader.remove(), 400);

    } catch (err) {
        console.error("Gagal memuat kamera & hand tracking:", err);
        const loader = document.getElementById('camera-loader');
        if (loader) {
            loader.innerHTML = `
                <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; width:100%; height:100%; color:#EF4444; font-weight:700; padding:20px; text-align:center;">
                    <div style="font-size: 3.5rem; margin-bottom:10px;">⚠️</div>
                    <div style="font-size:1.15rem; letter-spacing:-0.3px;">Kamera Gagal Dibuka</div>
                    <div style="font-size:0.85rem; opacity:0.9; margin-top:6px; font-weight:600; line-height:1.4;">Pastikan izin kamera sudah diaktifkan di browsermu ya!</div>
                </div>
            `;
        }
    }
}

// Trigger initializations
initCameraAndHandTracking();

async function periksaTulisan() {
    // Hentikan timer jika ada
    if (window.quizTimerInterval) {
        clearInterval(window.quizTimerInterval);
    }

    const dataURL = paintCanvas.toDataURL('image/png');
    const btn = document.getElementById('btn-periksa');
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Memproses...";
    }
    
    console.log("MENGIRIM KE BACKEND -> Mode:", currentMode, "| Target:", targetChar);
    
    try {
        let endpoint = "/save";
        let payload = {
            mode: currentMode,
            target: targetChar,
            image: dataURL,
            latihan_id: latihanId ? parseInt(latihanId) : null,
            kelas_id: kelasId ? parseInt(kelasId) : null
        };

        if (isQuiz && sessionId) {
            endpoint = `/murid/quiz/submit/${sessionId}`;
            payload = {
                image: dataURL,
                target: targetChar,
                mode: currentMode,
                question_no: config.questionNo || 1
            };
        }

        const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        showModalResult(data);
    } catch (error) {
        console.error(error);
        alert("Gagal terhubung ke server FastAPI");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "Periksa Tulisan";
        }
    }
}

function showModalResult(data) {
    const modal = document.getElementById("modal-selesai");
    const title = document.getElementById("modal-title");
    const confidenceText = document.getElementById("modal-confidence");
    const iconContainer = document.getElementById("result-icon");
    
    const nextBtn = document.getElementById('btn-next-quiz');
    const retryBtn = document.getElementById('btn-retry-quiz');

    if (!modal || !title || !confidenceText) return;

    // Reset state awal tombol
    if (nextBtn) {
        nextBtn.disabled = false;
        nextBtn.innerText = "Lanjut ke Soal Berikutnya";
        nextBtn.style.display = "block"; // Selalu ada Lanjut
    }
    if (retryBtn) retryBtn.style.display = "none";

    // Setup Feedback
    if (data.correct) {
        title.innerText = `Jawaban Benar!`;
        title.style.color = "#16a34a";
        if (iconContainer) iconContainer.innerHTML = '🌟'; 
        speak(`Hebat! Jawabanmu benar.`);
        // Jika benar, Coba Lagi tidak perlu
        if (retryBtn) retryBtn.style.display = "none";
    } else {
        title.innerText = `Jawaban Salah!`;
        title.style.color = "#dc2626";
        if (iconContainer) iconContainer.innerHTML = '❌';
        speak(`Ayo coba lagi, kamu pasti bisa.`);

        // Logika Coba Lagi berdasarkan waktu
        const isTimerMode = window.QUIZ_CONFIG && window.QUIZ_CONFIG.mode === "timer";
        const hasTime = typeof window.timeLeft !== 'undefined' ? window.timeLeft > 0 : true;

        if (isQuiz && (hasTime || !isTimerMode)) {
            // Tampilkan Coba Lagi jika waktu masih ada
            if (retryBtn) retryBtn.style.display = "block";
        } else if (isQuiz && isTimerMode && !hasTime) {
            // Sembunyikan Coba Lagi jika waktu habis
            if (retryBtn) retryBtn.style.display = "none";
        }
    }

    confidenceText.innerText = `Akurasi: ${data.confidence}%`;
    modal.style.display = "flex";

    // Handle Tombol Lanjut (Next Question)
    if (nextBtn && data.next_url) {
        nextBtn.onclick = function(e) {
            e.preventDefault();
            this.disabled = true;
            this.innerText = "Memuat...";
            
            console.log("Navigating to next question:", data.next_url);
            
            // Tambahkan cache buster untuk memaksa navigasi/reload
            const separator = data.next_url.includes('?') ? '&' : '?';
            const finalUrl = data.next_url + separator + "q=" + new Date().getTime();
            
            window.location.href = finalUrl;
        };
    }
}

function closeKuisSelesaiModal() {
    document.getElementById("modal-selesai").style.display = "none";
    resetCanvas();
    
    // Jika dalam mode kuis timer, restart timernya
    if (window.QUIZ_CONFIG && window.QUIZ_CONFIG.mode === "timer" && typeof window.timeLeft !== 'undefined') {
        // Hapus interval lama jika masih ada (keamanan)
        if (window.quizTimerInterval) clearInterval(window.quizTimerInterval);
        
        window.quizTimerInterval = setInterval(() => {
            window.timeLeft--;
            const timerDisplay = document.getElementById('timer-val');
            if (timerDisplay) timerDisplay.innerText = window.timeLeft;
            if (window.timeLeft <= 0) {
                clearInterval(window.quizTimerInterval);
                if (typeof handleTimeout === 'function') handleTimeout();
            }
        }, 1000);
    }
}
