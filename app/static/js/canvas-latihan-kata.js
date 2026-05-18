/* ===================================================
   GESTRA — Canvas Latihan Kata (Identik Versi Huruf)
   =================================================== */

function closeKuisSelesaiModal() {
    document.getElementById('modal-selesai').style.display = 'none';
    resetCanvas();
}

document.addEventListener('DOMContentLoaded', () => {
    // 1. Ambil parameter dari URL
    const urlParams = new URLSearchParams(window.location.search);
    const targetChar = urlParams.get('target') || ''; // Ini akan mengambil "Mangga"
    const currentMode = urlParams.get('mode') || '';

    const targetDisplay = document.getElementById('display-target');
    
    if (targetDisplay) {
        targetDisplay.innerText = targetChar;
        console.log("Target berhasil dimuat:", targetChar);
    } else {
        console.error("Elemen display-target tidak ditemukan!");
    }

    // Tambahkan juga listener suara pada heading jika diklik
    const heading = document.querySelector('.info-header-text h2');
    if (heading) {
        heading.style.cursor = 'pointer';
        heading.addEventListener('click', () => speak(`Tulis kata ${targetChar}`));
    }
});

/* TTS helper */
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

// Ambil parameter kata dari URL
const urlParams = new URLSearchParams(window.location.search);
const targetWord = urlParams.get('target') || '';

// Update Tampilan Target di UI
const targetDisplay = document.querySelector('.display-target');

// Set ukuran canvas (SAMA PERSIS DENGAN VERSI HURUF)
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
                // Gambar ke Paint Canvas (Hitam untuk AI)
                pctx.beginPath();
                pctx.strokeStyle = "black";
                pctx.lineWidth = 18; // Sedikit lebih tipis dari huruf (25) agar kata tidak tumpuk
                pctx.lineCap = "round";
                pctx.moveTo(prevPoint.x, prevPoint.y);
                pctx.lineTo(smoothPoint.x, smoothPoint.y);
                pctx.stroke();

                // Gambar ke Overlay Kamera (Biru untuk User)
                octx.beginPath();
                octx.strokeStyle = "#3B82F6"; 
                octx.lineWidth = 8;
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

const hands = new Hands({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1646424915/${file}`
});
hands.setOptions({ maxNumHands: 1, modelComplexity: 1, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
hands.onResults(onResults);

const camera = new Camera(video, {
    onFrame: async () => { await hands.send({ image: video }); },
    width: 640,
    height: 480
});
camera.start();

let currentLetterIndex = 0;
let collectedPredictions = "";
let letterScores = [];

// Inisialisasi tampilan awal
function initWordTraining() {
    // Inisialisasi array skor dengan nilai 100 untuk tiap huruf
    if (letterScores.length === 0) {
        letterScores = new Array(targetWord.length).fill(100);
    }
    
    // Target Kata pada Canvas Latihan Kata
    const wordDisplay = document.getElementById('word-target-display');
    if (wordDisplay) wordDisplay.innerText = targetWord;

    // Urutan Tulisan Huruf
    const stepDisplay = document.getElementById('current-step-dash');
    if (stepDisplay) stepDisplay.innerText = currentLetterIndex + 1;

    // Huruf Yang Akan Ditulis
    const letterDisplay = document.getElementById('active-letter-target');
    if (letterDisplay) letterDisplay.innerText = targetWord[currentLetterIndex];

    updateRibbon();
}

function updateRibbon() {
    const ribbon = document.getElementById('word-ribbon');
    ribbon.innerHTML = "";
    
    // Tampilkan placeholder untuk seluruh kata
    for (let i = 0; i < targetWord.length; i++) {
        const box = document.createElement('div');
        box.style = "width: 50px; height: 60px; border: 2px dashed #cbd5e1; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: bold; color: #3B82F6;";
        
        if (i < collectedPredictions.length) {
            box.innerText = collectedPredictions[i];
            box.style.border = "2px solid #3B82F6";
            box.style.background = "#eff6ff";
        } else if (i === currentLetterIndex) {
            box.style.border = "2px solid #F59E0B"; // Highlight huruf aktif
            box.innerText = "?";
        }
        ribbon.appendChild(box);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initWordTraining(); 
});

async function periksaTulisan() {
    const dataURL = paintCanvas.toDataURL('image/png');
    const btn = document.querySelector('.btn-primary');

    const currentTarget = targetWord[currentLetterIndex];
    let modeKirim = "lower";
    if(!isNaN(currentTarget) && currentTarget.trim() !== "") {
        modeKirim = "number";
    } else if (currentTarget === currentTarget.toUpperCase() && currentTarget !== currentTarget.toLowerCase()) {
        modeKirim = "upper";
    }

    btn.disabled = true;
    btn.innerText = "Mengecek";

    try {
        let response, data;
        try {
            response = await fetch("/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    mode: modeKirim,
                    target: currentTarget,
                    image: dataURL
                })
            });
            data = await response.json();
        } catch (fetchErr) {
            console.error("Gagal terhubung ke server GESTRA:", fetchErr);
            data = {
                correct: false,
                prediction: "Error",
                confidence: 0,
                status: "Terjadi mismatch antara frontend - backend - model",
                message: "Coba ulangi ya 😊 sistem sedang menyesuaikan input"
            };
        }

        // Debug huruf level kata
        console.group(`%c GESTRA DEBUG: Huruf ${targetWord[currentLetterIndex]} `, 'background: #222; color: #bada55');
        console.log(`Target Terdaftar: ${data.target}`);
        console.log(`Tebakan Asli AI: ${data.prediction}`);
        console.log(`Confidence: ${data.confidence}%`);
        console.log(`Status Akhir: ${data.status}`);
        console.groupEnd();

        // Penalti nilai
        if (!data.correct) {
            letterScores[currentLetterIndex] = Math.max(0, letterScores[currentLetterIndex] - 10);
            
            let errorTitle = data.status || "Kurang Tepat";
            let speakMsg = data.message || (data.status === "Hampir Benar" ? "Hampir benar 👍" : `Coba lagi ya 😊`);
            speak(speakMsg);
            
            showRetryModal(errorTitle, targetWord[currentLetterIndex]);
            resetCanvas();
            btn.disabled = false;
            btn.innerText = "Kirim Huruf";
            
            return;
        }

        collectedPredictions += targetWord[currentLetterIndex]; 
        updateRibbon();

        currentLetterIndex++;

        if (currentLetterIndex < targetWord.length) {
            // Lanjut ke huruf berikutnya
            setTimeout(() => {
                speak(`Bagus! Sekarang tulis huruf ${targetWord[currentLetterIndex]}`);
                resetCanvas();
                initWordTraining();
                btn.disabled = false;
                btn.innerText = "Kirim Huruf";
            }, 500);
        } else {
            // Kata selesai
            setTimeout(() => {
                finalValidation();
            }, 800);
        }
    } catch (error) {
        console.error("Kesalahan kritis pada periksaTulisan:", error);
        speak("Coba ulangi ya 😊");
        showRetryModal("Sistem sedang sibuk", targetWord[currentLetterIndex]);
        resetCanvas();
        btn.disabled = false;
        btn.innerText = "Kirim Huruf";
    }
}

function showRetryModal(errorTitle, targetChar) {
    const modal = document.getElementById("modal-selesai");
    const title = document.getElementById("modal-title");
    const confidenceText = document.getElementById("modal-confidence");
    const btnSelesai = modal.querySelector(".btn-cek-nilai");

    title.innerText = errorTitle;
    title.style.color = "#dc2626";
    
    confidenceText.innerHTML = `Coba lagi, tulis ulang huruf: <span style="color: #3B82F6; font-size: 2.5rem; font-weight: 900; display: block; margin-top: 10px;">${targetChar}</span>`;
    
    if (btnSelesai) btnSelesai.style.display = "none";

    const imgContainer = document.getElementById("debug-images-container");
    if (imgContainer) imgContainer.innerHTML = "";

    modal.style.display = "flex";
}

function closeKuisSelesaiModal() {
    const modal = document.getElementById('modal-selesai');
    const btnSelesai = modal.querySelector(".btn-cek-nilai");
    
    modal.style.display = 'none';
    if (btnSelesai) btnSelesai.style.display = "inline-block"; // Munculkan kembali untuk modal akhir
    resetCanvas();
}

async function finalValidation() {
    try {
        const response = await fetch("/predict-word", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                target: targetWord,
                prediction: collectedPredictions,
                individual_scores: letterScores
            })
        });
        const data = await response.json();
        showModalResult(data);
    } catch (error) {
        alert("Gagal validasi akhir");
    }
}

function showModalResult(data) {
    const modal = document.getElementById("modal-selesai");
    const title = document.getElementById("modal-title");
    const confidenceText = document.getElementById("modal-confidence");
    
    const btnSelesai = modal.querySelector(".btn-cek-nilai");
    if (btnSelesai) btnSelesai.style.display = "inline-block";

    if (data.correct) {
        title.innerText = `Hebat! Kamu Menulis Tanpa Banyak Kesalahan!`;
        title.style.color = "#16a34a";
        speak(`Luar biasa! Kamu berhasil menulis kata ${targetWord}`);
    } else {
        title.innerText = `Coba Lagi!`;
        title.style.color = "#dc2626";
        speak(`Ayo coba lagi, tulis kata ${targetWord} dengan lebih rapi`);
    }

    const similarity = Math.round(data.score);
    confidenceText.innerText = `Nilai Kamu: ${similarity}`;
    
    modal.style.display = "flex";
}