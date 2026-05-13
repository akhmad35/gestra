/* ===================================================
   GESTRA — Canvas Latihan Kata (Identik Versi Huruf)
   =================================================== */

function closeKuisSelesaiModal() {
    document.getElementById('modal-selesai').style.display = 'none';
    resetCanvas();
}

document.addEventListener('DOMContentLoaded', () => {
    const heading = document.querySelector('.info-header-text h2');
    if (heading) {
        heading.style.cursor = 'pointer';
        heading.addEventListener('click', () => speak('Tulis kata dibawah ini'));
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
const targetWord = urlParams.get('target') || 'mangga';

// Update Tampilan Target di UI
const targetDisplay = document.querySelector('.target-char');
if(targetDisplay) {
    targetDisplay.innerText = targetWord.toUpperCase();
    targetDisplay.style.fontSize = "3.5rem"; 
    targetDisplay.style.letterSpacing = "8px";
}

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

// --- Logika Fetch ke Endpoint Kata ---
async function periksaTulisan() {
    const dataURL = paintCanvas.toDataURL('image/png');
    
    try {
        const response = await fetch("/predict-word", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                target: targetWord,
                image: dataURL
            })
        });
        
        const data = await response.json();
        showModalResult(data);
    } catch (error) {
        alert("Gagal terhubung ke server FastAPI");
    }
}

function showModalResult(data) {
    const modal = document.getElementById("modal-selesai");
    const title = document.getElementById("modal-title");
    const confidenceText = document.getElementById("modal-confidence");

    // --- TAMBAHKAN LOGIKA UNTUK MENAMPILKAN GAMBAR ---
    // Buat kontainer untuk gambar jika belum ada di modal
    let imgContainer = document.getElementById("debug-images-container");
    if (!imgContainer) {
        imgContainer = document.createElement("div");
        imgContainer.id = "debug-images-container";
        imgContainer.style.display = "flex";
        imgContainer.style.gap = "10px";
        imgContainer.style.justifyContent = "center";
        imgContainer.style.margin = "15px 0";
        // Masukkan sebelum modal-actions
        const actions = document.querySelector(".modal-actions");
        actions.parentNode.insertBefore(imgContainer, actions);
    }
    
    // Kosongkan dan isi dengan gambar baru (ditambah timestamp agar tidak kena cache browser)
    imgContainer.innerHTML = "";
    if (data.debug_images) {
        data.debug_images.forEach(path => {
            const img = document.createElement("img");
            img.src = `${path}?t=${new Date().getTime()}`; 
            img.style.width = "50px";
            img.style.border = "1px solid #ddd";
            img.style.borderRadius = "5px";
            imgContainer.appendChild(img);
        });
    }

    if (data.correct) {
        title.innerText = `Hebat! Kamu menulis: ${data.prediction}`;
        title.style.color = "#16a34a";
        speak(`Luar biasa! Kamu berhasil menulis kata ${targetWord}`);
    } else {
        title.innerText = `Hampir! Sistem membaca: ${data.prediction}`;
        title.style.color = "#dc2626";
        speak(`Ayo coba lagi, tulis kata ${targetWord} dengan lebih rapi`);
    }

    const similarity = Math.round(data.score * 100);
    confidenceText.innerText = `Skor Kemiripan: ${similarity}% | Terdeteksi ${data.total_letters} huruf`;
    
    modal.style.display = "flex";
}