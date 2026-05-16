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

// Ambil parameter dari URL
const urlParams = new URLSearchParams(window.location.search);
const targetChar = urlParams.get('target') || 'A';
const currentMode = urlParams.get('mode') || 'upper';

// Update Tampilan Target di UI
document.querySelector('.target-char').innerText = targetChar;

// Set ukuran canvas (sesuaikan dengan workspace)
paintCanvas.width = 640; paintCanvas.height = 480;
cameraOverlay.width = 640; cameraOverlay.height = 480;

let prevPoint = null;
let smoothPoint = null;
const alpha = 0.6;
let letterScores = [];

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

const hands = new Hands({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1646424915/${file}`
});

hands.setOptions({ maxNumHands: 1, modelComplexity: 1, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
hands.onResults(onResults);

const camera = new Camera(video, {
    onFrame: async () => { 
        await hands.send({ image: video }); 
    },
    width: 640,
    height: 480
});

camera.start();

let currentScore = 100;

async function periksaTulisan() {
    const dataURL = paintCanvas.toDataURL('image/png');
    const btn = document.querySelector(".btn-primary");

    btn.disabled = true;
    btn.innerText = "Mengecek Huruf";
    
    console.log("MENGIRIM KE BACKEND -> Mode:", currentMode, "| Target:", targetChar);
    
    try {
        const response = await fetch("/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                mode: currentMode,
                target: targetChar,
                image: dataURL
            })
        });
        
        const data = await response.json();
        const errorStates = ["Kamu salah menulis huruf", "Tidak Jelas", "Kosong", "Error"];

        // Penalti Nilai
        if (!data.correct || errorStates.includes(data.prediction)) {
            // Kurangi 10 poin
            currentScore = Math.max(0, currentScore - 10);
            console.log(`Penalty! Skor huruf: ${currentScore}`);
            
            // Tampilkan pesan suara
            let msg = (data.prediction === "Kosong") ? "Kanvas kosong!" : "Tulisan kurang tepat.";
            speak(`${msg} Coba lagi ya, nilai kamu sekarang ${currentScore}`);
            
            // Tampilkan modal hasil sementara
            showModalResult(data, false); 
            
            resetCanvas();
            btn.disabled = false;
            btn.innerText = "Periksa Tulisan";
        } else {
            showModalResult(data, true);
        }

    } catch (error) {
        alert("Gagal terhubung ke server FastAPI");
        btn.disabled = false;
        btn.innerText = "Periksa Tulisan";
    }
}

function showModalResult(data, isFinal) {
    // console.log("Data diterima dari server:", data);
    const modal = document.getElementById("modal-selesai");
    const title = document.getElementById("modal-title");
    const confidenceText = document.getElementById("modal-confidence");
    const btnCek = modal.querySelector("btn-cek-nilai");

    if (isFinal) {
        // Tampilan jika BENAR
        title.innerText = `Luar Biasa!`;
        title.style.color = "#16a34a";
        confidenceText.innerHTML = `Kamu berhasil menulis huruf <b>${targetChar}</b><br>Nilai Akhir: <span style="font-size: 1.5rem; color: #3B82F6;">${currentScore}</span>`;
        if (btnCek) btnCek.style.display = "inline-block";
        speak(`Hebat! Kamu berhasil. Nilai kamu ${currentScore}`);
    } else {
        // Tampilan jika SALAH (Coba Lagi)
        title.innerText = `Ayo Coba Lagi!`;
        title.style.color = "#dc2626";
        confidenceText.innerHTML = `Sistem melihat: <b>${data.prediction}</b><br>Skor berkurang jadi: <b>${currentScore}</b>`;
        if (btnCek) btnCek.style.display = "none"; // Sembunyikan tombol cek nilai jika belum berhasil
    }

    modal.style.display = "flex";
}

function closeKuisSelesaiModal() {
    document.getElementById("modal-selesai").style.display = "none";
    resetCanvas();
}
