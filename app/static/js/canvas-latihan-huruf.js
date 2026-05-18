    /* ===================================================
    GESTRA — Canvas Latihan JavaScript
    =================================================== */

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

            console.log("Loading MediaPipe scripts in parallel...");
            await Promise.all([
                loadScript("https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1646424915/hands.js"),
                loadScript("https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js")
            ]);
            console.log("MediaPipe scripts loaded successfully!");

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

            let response, data;
            try {
                response = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                data = await response.json();
            } catch (fetchErr) {
                console.error("Gagal terhubung ke server GESTRA:", fetchErr);
                data = {
                    correct: false,
                    prediction: "unknown",
                    confidence: 0,
                    status: "system_error",
                    message: "Coba ulangi ya 😊 sistem sedang menyesuaikan input"
                };
            }

            showModalResult(data);
        } catch (error) {
            console.error("Kesalahan kritis pada periksaTulisan:", error);
            showModalResult({
                correct: false,
                prediction: "unknown",
                confidence: 0,
                status: "system_error",
                message: "Coba ulangi ya 😊 sistem sedang menyesuaikan input"
            });
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerText = "Periksa Tulisan";
            }
        }
    }

    /**
     * showModalResult(data)
     *
     * Menampilkan hasil prediksi ML di modal dengan:
     * - SUCCESS: confidence >= 70 DAN huruf cocok dengan target → "Luar Biasa!" + nilai 100
     * - FAIL: confidence < 70 ATAU huruf tidak cocok → "Coba Lagi" + nilai 0
     *
     * @param {Object} data - Response dari backend
     * @param {string} data.label       - Huruf yang diprediksi (misal: "c")
     * @param {string} data.prediction  - Alternatif field huruf prediksi
     * @param {number} data.confidence  - Keyakinan prediksi (0-100)
     * @param {string} data.next_url    - URL untuk tombol next (opsional)
     */
    function showModalResult(data) {
        if (!data) {
            console.error('Data invalid:', data);
            return;
        }

        const modal = document.getElementById('modal-selesai');
        const modalTitle = document.getElementById('modal-title');
        const confidenceText = document.getElementById('modal-confidence');
        const iconContainer = document.getElementById('result-icon');
        const btnNext = document.getElementById('btn-next-quiz');
        const btnRetry = document.getElementById('btn-retry-quiz');

        if (!modal || !modalTitle || !confidenceText) {
            console.error('Modal elements tidak ditemukan');
            return;
        }

        // === TENTUKAN STATUS (SUCCESS / FAIL) ===
        const confidenceNum = typeof data.confidence === "number" ? data.confidence : parseFloat(data.confidence);
        const confidenceVal = isNaN(confidenceNum) ? 0 : confidenceNum;

        // ✅ FIX: isSuccess harus confidence >= 70 DAN huruf cocok dengan target
        const predictedLabel = (data.label || data.prediction || "").toLowerCase().trim();
        const target = (targetChar || "").toLowerCase().trim();
        const isSuccess = confidenceVal >= 70 && predictedLabel === target;

        const confidenceFormatted = confidenceVal.toFixed(2);
        const label = data.label || data.prediction || "?";

        // Setup Custom CSS
        const styleId = "gestra-modal-custom-styles";
        if (!document.getElementById(styleId)) {
            const style = document.createElement("style");
            style.id = styleId;
            style.textContent = `
                #modal-custom-desc {
                    font-size: 1.15rem;
                    color: #475569;
                    margin: 15px 0 10px 0;
                    line-height: 1.5;
                    font-weight: 500;
                }
                .letter-badge-success {
                    color: #16a34a;
                    font-weight: 800;
                    font-size: 1.35rem;
                    background: #f0fdf4;
                    border: 2px solid #bbf7d0;
                    padding: 3px 10px;
                    border-radius: 8px;
                    display: inline-block;
                    margin: 0 4px;
                }
                .letter-badge-fail {
                    color: #dc2626;
                    font-weight: 800;
                    font-size: 1.35rem;
                    background: #fef2f2;
                    border: 2px solid #fecaca;
                    padding: 3px 10px;
                    border-radius: 8px;
                    display: inline-block;
                    margin: 0 4px;
                }
                #modal-custom-score {
                    font-size: 1.25rem;
                    font-weight: 700;
                    margin: 10px 0 20px 0;
                }
                .score-badge-success {
                    background: #16a34a;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-weight: 800;
                    box-shadow: 0 4px 6px -1px rgba(22, 163, 74, 0.2);
                }
                .score-badge-fail {
                    background: #dc2626;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-weight: 800;
                    box-shadow: 0 4px 6px -1px rgba(220, 38, 38, 0.2);
                }
            `;
            document.head.appendChild(style);
        }

        const modalBox = modal.querySelector(".modal-box");
        if (modalBox) {
            let descEl = document.getElementById("modal-custom-desc");
            if (!descEl) {
                descEl = document.createElement("p");
                descEl.id = "modal-custom-desc";
                modalBox.insertBefore(descEl, confidenceText);
            }

            let scoreEl = document.getElementById("modal-custom-score");
            if (!scoreEl) {
                scoreEl = document.createElement("p");
                scoreEl.id = "modal-custom-score";
                modalBox.insertBefore(scoreEl, confidenceText);
            }

            const nilaiAkhir = isSuccess ? 100 : 0;

            if (isSuccess) {
                modalTitle.textContent = 'Luar Biasa!';
                modalTitle.style.color = '#16a34a';
                if (iconContainer) iconContainer.innerHTML = '🌟';

                descEl.innerHTML = `Kamu berhasil menulis huruf <span class="letter-badge-success">${label}</span>`;
                scoreEl.innerHTML = `Nilai Akhir: <span class="score-badge-success">${nilaiAkhir}</span>`;

                speak(`Luar biasa! Kamu berhasil menulis huruf ${label}.`);
            } else {
                modalTitle.textContent = 'Coba lagi';
                modalTitle.style.color = '#dc2626';
                if (iconContainer) iconContainer.innerHTML = '❌';

                descEl.innerHTML = `Kamu menulis huruf <span class="letter-badge-fail">${label}</span>`;
                scoreEl.innerHTML = `Nilai Akhir: <span class="score-badge-fail">${nilaiAkhir}</span>`;

                speak(`Coba lagi ya, tulisan huruf ${label} belum cukup jelas.`);
            }

            // confidenceText.innerHTML = `Tingkat Keyakinan: <strong>${confidenceFormatted}%</strong>`;
            // Tampilkan tingkat keyakinan hanya jika benar
            if (isSuccess) {
                confidenceText.innerHTML = `Tingkat Keyakinan: <strong>${confidenceFormatted}%</strong>`;
            } else {
                confidenceText.innerHTML = '';
            }
        }

        // === ATUR VISIBILITY TOMBOL ===
        if (btnNext) {
            btnNext.style.display = isSuccess ? 'inline-block' : 'none';
            btnNext.disabled = false;
            btnNext.innerText = "Lanjut ke Soal Berikutnya";
        }
        if (btnRetry) {
            btnRetry.style.display = isSuccess ? 'none' : 'inline-block';
            btnRetry.disabled = false;
            btnRetry.innerText = "Coba Lagi";
        }

        // === SET URL UNTUK NEXT BUTTON ===
        if (btnNext) {
            if (data.next_url) {
                btnNext.onclick = function (e) {
                    e.preventDefault();
                    this.disabled = true;
                    this.innerText = "Memuat...";
                    console.log("Navigating to next question:", data.next_url);
                    const separator = data.next_url.includes('?') ? '&' : '?';
                    const finalUrl = data.next_url + separator + "q=" + Date.now();
                    window.location.href = finalUrl;
                };
            } else {
                btnNext.onclick = function (e) {
                    e.preventDefault();
                    this.disabled = true;
                    this.innerText = "Memuat...";
                    window.location.href = '/murid/riwayat-nilai';
                };
            }
        }

        modal.style.display = "flex";
    }

    function closeKuisSelesaiModal() {
        document.getElementById("modal-selesai").style.display = "none";
        resetCanvas();

        // Jika dalam mode kuis timer, restart timernya
        if (window.QUIZ_CONFIG && window.QUIZ_CONFIG.mode === "timer" && typeof window.timeLeft !== 'undefined') {
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