    /* ===================================================
    GESTRA — Canvas Latihan Kata (Identik Versi Huruf)
    =================================================== */

    function speak(text) {
        if (!window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        const utt = new SpeechSynthesisUtterance(text);
        utt.lang = 'id-ID';
        utt.rate = 0.9;
        window.speechSynthesis.speak(utt);
    }

    function initializeApp() {
        const targetChar = targetWord;
        const heading = document.querySelector('.info-header-text h2');

        if (heading) {
            heading.style.cursor = 'pointer';
            heading.addEventListener('click', () => speak(`Tulis kata ${targetChar}`));
        }

        initWordTraining();
    }

    document.addEventListener('DOMContentLoaded', initializeApp);

    // Logika Penulisan
    const video = document.getElementById('webcam');
    const paintCanvas = document.getElementById('paintCanvas');
    const pctx = paintCanvas.getContext('2d');
    const cameraOverlay = document.getElementById('cameraOverlay');
    const octx = cameraOverlay.getContext('2d');

    // Ambil parameter kata dari URL
    const config = window.QUIZ_CONFIG || {};
    console.log("GESTRA Quiz Config:", config);

    const urlParams = new URLSearchParams(window.location.search);
    const targetWord = config.target || urlParams.get('target') || '';
    const isQuiz = (config.isQuiz === true) || (urlParams.get('quiz') === 'true');

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

    function computeLetterScore(isCorrect, confidence) {
        const value = Number(confidence) || 0;

        if (isCorrect) {
            if (value >= 95) return 100;
            if (value >= 90) return 95;
            if (value >= 80) return 85;
            if (value >= 70) return 75;
            return 60;
        }

        if (value >= 90) return 20;
        if (value >= 70) return 10;
        return 0;
    }

    function calculateFinalScore() {
        if (!letterScores || letterScores.length === 0) return 0;
    
        // Debug: Cek isi array skor di console (F12)
        console.log("Isi Skor Per Huruf:", letterScores); 
        
        const sum = letterScores.reduce((total, score) => total + Number(score || 0), 0);
        const avg = sum / letterScores.length;
        
        return Math.round(avg);
    }

    function setButtonState(isBusy) {
        const btn = document.querySelector('.btn-primary');
        if (!btn) return;
        btn.disabled = isBusy;
        btn.innerText = isBusy ? "Mengecek" : "Kirim Huruf";
    }

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
    let letterPenalties = [];

    // Inisialisasi tampilan awal
    function initWordTraining() {
        if (letterScores.length === 0) {
            letterScores = new Array(targetWord.length).fill(0);
            letterPenalties = new Array(targetWord.length).fill(0); // <--- Inisialisasi penalti
        }

        const wordDisplay = document.getElementById('word-target-display');
        if (wordDisplay) wordDisplay.innerText = targetWord;

        const stepDisplay = document.getElementById('current-step-dash');
        if (stepDisplay) stepDisplay.innerText = currentLetterIndex + 1;

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

    async function periksaTulisan() {
        if (typeof window.stopTimer === 'function') {
            window.stopTimer();
        }
        const dataURL = paintCanvas.toDataURL('image/png');
        const btn = document.querySelector('.btn-primary');

        const currentTarget = targetWord[currentLetterIndex];
        let modeKirim = "lower";
        if (!isNaN(currentTarget) && currentTarget.trim() !== "") {
            modeKirim = "number";
        } else if (currentTarget === currentTarget.toUpperCase() && currentTarget !== currentTarget.toLowerCase()) {
            modeKirim = "upper";
        }

        setButtonState(true);

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

            console.group(`%c GESTRA DEBUG: Huruf ${currentTarget} `, 'background: #222; color: #bada55');
            console.log(`Target Terdaftar: ${data.target}`);
            console.log(`Tebakan Asli AI: ${data.prediction}`);
            console.log(`Confidence: ${data.confidence}%`);
            console.log(`Status Akhir: ${data.status}`);
            console.groupEnd();

           const currentScore = computeLetterScore(Boolean(data.correct), data.confidence);

            if (!data.correct) {
                letterPenalties[currentLetterIndex] += 10;
                console.log(`Salah! Penalti huruf ${currentLetterIndex + 1} sekarang: ${letterPenalties[currentLetterIndex]}`);
                const errorTitle = data.status || "Kurang Tepat";

                showRetryModal(errorTitle, currentTarget);
                resetCanvas();
                setButtonState(false);
                return;
            }
            let finalScoreThisLetter = currentScore - letterPenalties[currentLetterIndex];

            // Jangan sampai nilainya minus, minimal 0
            if (finalScoreThisLetter < 0) finalScoreThisLetter = 0;

            letterScores[currentLetterIndex] = finalScoreThisLetter;
            console.log(`Berhasil! Skor Akhir Huruf ${currentTarget}: ${finalScoreThisLetter}`);

            collectedPredictions += currentTarget;
            updateRibbon();
            currentLetterIndex += 1;

            if (currentLetterIndex < targetWord.length) {
                setTimeout(() => {
                    speak(`Bagus! Sekarang tulis huruf ${targetWord[currentLetterIndex]}`);
                    resetCanvas();
                    initWordTraining();
                    setButtonState(false);
                    if (typeof window.startTimer === 'function') {
                        window.startTimer();
                    }
                }, 500);
            } else {
                setTimeout(() => {
                    finalValidation();
                }, 800);
            }
        } catch (error) {
            console.error("Kesalahan kritis pada periksaTulisan:", error);
            speak("Coba ulangi ya 😊");
            showRetryModal("Sistem sedang sibuk", currentTarget);
            resetCanvas();
            setButtonState(false);
        }
    }

    function showRetryModal(errorTitle, targetChar) {
        const modal = document.getElementById("modal-selesai");
        if (!modal) return;

        const title = document.getElementById("modal-title");
        const confidenceText = document.getElementById("modal-confidence");
        const btnNext = document.getElementById('btn-next-quiz');
        const btnRetry = document.getElementById('btn-retry-quiz');
        const defaultActions = document.getElementById("modal-actions-default");

        if (title) {
            title.innerText = errorTitle;
            title.style.color = "#dc2626";
        }

        if (confidenceText) {
            confidenceText.innerHTML =
                `Coba lagi, tulis ulang huruf:
                <span style="color:#3B82F6;font-size:2.5rem;font-weight:900;display:block;margin-top:10px;">
                ${targetChar}</span>`;
        }

        if (isQuiz) {
            if (defaultActions) defaultActions.style.display = "none";
            if (btnNext) btnNext.style.display = "none"; // Belum selesai seluruh kata, jadi tidak ada next quiz
            if (btnRetry) {
                btnRetry.style.display = "inline-block";
                btnRetry.onclick = function() {
                    closeKuisSelesaiModal();
                };
            }
        } else {
            if (defaultActions) defaultActions.style.display = "flex";
            if (btnNext) btnNext.style.display = "none";
            if (btnRetry) btnRetry.style.display = "none";
            const checkBtn = document.getElementById("btn-default-check");
            if (checkBtn) {
                checkBtn.style.display = "none";
            }
        }

        const imgContainer = document.getElementById("debug-images-container");
        if (imgContainer) imgContainer.innerHTML = "";

        modal.style.display = "flex";
    }

    function closeKuisSelesaiModal() {
        // Bersihkan timer auto-advance jika ada
        if (window.quizAutoAdvanceTimeout) {
            clearTimeout(window.quizAutoAdvanceTimeout);
            window.quizAutoAdvanceTimeout = null;
        }

        const modal = document.getElementById('modal-selesai');
        const btnSelesai = modal.querySelector(".btn-cek-nilai");

        modal.style.display = 'none';
        if (btnSelesai) btnSelesai.style.display = "inline-block"; // Munculkan kembali untuk modal akhir
        resetCanvas();

        if (typeof window.startTimer === 'function') {
            window.startTimer();
        }
    }

    async function finalValidation() {
        const finalPrediction = collectedPredictions;
        const finalTarget = targetWord;
        const finalCorrect = finalPrediction.toLowerCase() === finalTarget.toLowerCase();
        const localScore = calculateFinalScore();

        const fallbackResult = {
            correct: finalCorrect,
            score: localScore,
            prediction: finalPrediction,
            target: finalTarget,
        };

        try {
            let endpoint = "/predict-word";
            let payload = {
                target: finalTarget,
                prediction: finalPrediction,
                individual_scores: letterScores
            };

            if (isQuiz && config.sessionId) {
                endpoint = `/murid/quiz/submit/${config.sessionId}`;
                payload = {
                    target: finalTarget,
                    prediction: finalPrediction,
                    confidence: localScore,
                    is_correct: finalCorrect,
                    question_no: config.questionNo || 1,
                    is_word: true
                };
            }

            const response = await fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            let data = fallbackResult;
            try {
                data = await response.json();
            } catch (parseErr) {
                console.error("Gagal parse JSON validasi akhir:", parseErr);
            }

            if (!response.ok) {
                console.warn("Validasi akhir HTTP non-OK, gunakan fallback lokal.", response.status);
                data = { ...fallbackResult, status: "http_error" };
            }

            showModalResult({
                correct: Boolean(data.correct),
                score: localScore,
                confidence: data.confidence,
                prediction: data.prediction ?? finalPrediction,
                target: data.target ?? finalTarget,
                next_url: data.next_url
            });
        } catch (error) {
            console.error("Gagal validasi akhir:", error);
            showModalResult(fallbackResult);
        }
    }

    function showModalResult(data) {
        const modal = document.getElementById("modal-selesai");
        const title = document.getElementById("modal-title");
        const confidenceText = document.getElementById("modal-confidence");
        const btnNext = document.getElementById('btn-next-quiz');
        const btnRetry = document.getElementById('btn-retry-quiz');

        const isCorrect = Boolean(data && data.correct);
        
        let finalDisplayScore = 0;
        if (data && typeof data.score !== 'undefined' && data.score !== null) {
            finalDisplayScore = Math.round(data.score);
        } else if (data && typeof data.confidence !== 'undefined' && data.confidence !== null) {
            finalDisplayScore = Math.round(data.confidence);
        } else {
            finalDisplayScore = isCorrect ? calculateFinalScore() : 0;
        }

        // === INJEKSI GAYA KHUSUS MODAL (Seperti di Huruf) ===
        const styleId = "gestra-modal-custom-styles-kata";
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

            const label = data.prediction && data.prediction !== "Kosong" ? data.prediction.toUpperCase() : "Kosong";

            if (isCorrect) {
                title.textContent = 'Luar Biasa!';
                title.style.color = '#16a34a';
                const iconContainer = document.getElementById('result-icon');
                if (iconContainer) iconContainer.innerHTML = '🌟';

                descEl.innerHTML = `Kamu berhasil menulis kata <span class="letter-badge-success">${label}</span>`;
                scoreEl.innerHTML = `Nilai Akhir: <span class="score-badge-success">${finalDisplayScore}</span>`;

                speak(`Luar biasa! Kamu berhasil menulis kata tanpa banyak kesalahan.`);
            } else {
                title.textContent = 'Coba lagi';
                title.style.color = '#dc2626';
                const iconContainer = document.getElementById('result-icon');
                if (iconContainer) iconContainer.innerHTML = '❌';

                descEl.innerHTML = `Kamu menulis kata <span class="letter-badge-fail">${label}</span>`;
                scoreEl.innerHTML = `Nilai Akhir: <span class="score-badge-fail">${finalDisplayScore}</span>`;

                speak(`Coba lagi ya, menulis kata masih ada beberapa kesalahan.`);
            }

            if (isCorrect) {
                confidenceText.innerHTML = `Tingkat Keyakinan: <strong>${finalDisplayScore}%</strong>`;
            } else {
                confidenceText.innerHTML = '';
            }
        }

        // === ATUR VISIBILITY TOMBOL ===
        const isQuizMode = isQuiz;
        const defaultActions = document.getElementById("modal-actions-default");

        if (isQuizMode) {
            if (defaultActions) defaultActions.style.display = "none";
            
            // Tampilkan tombol Coba Lagi jika jawaban salah
            if (btnRetry) {
                btnRetry.style.display = isCorrect ? "none" : "inline-block";
                btnRetry.onclick = function() {
                    // Reset kata states ke awal
                    currentLetterIndex = 0;
                    collectedPredictions = "";
                    letterScores = new Array(targetWord.length).fill(0);
                    letterPenalties = new Array(targetWord.length).fill(0);
                    
                    closeKuisSelesaiModal();
                    initWordTraining();
                    
                    // Reset timer kembali (KHUSUS speed quiz)
                    if (typeof window.startTimer === 'function') {
                        window.startTimer();
                    }
                };
            }
            
            if (btnNext) {
                btnNext.style.display = "inline-block";
                btnNext.disabled = false;
                btnNext.innerText = "Lanjut ke Soal Berikutnya";
                
                let nextUrl = data.next_url;
                if (!nextUrl) {
                    const isTimerVal = config.isTimer || (urlParams.get('timer') === 'true');
                    const levelVal = config.level || urlParams.get('level') || 'medium';
                    nextUrl = `/murid/quiz-kata/start?timer=${isTimerVal}&level=${levelVal}`;
                }
                
                const navigateToNext = () => {
                    btnNext.disabled = true;
                    btnNext.innerText = "Memuat...";
                    const separator = nextUrl.includes('?') ? '&' : '?';
                    window.location.href = nextUrl + separator + "q=" + Date.now();
                };
                
                btnNext.onclick = function (e) {
                    e.preventDefault();
                    navigateToNext();
                };
                
                // Bersihkan timer auto-advance sebelumnya jika ada
                if (window.quizAutoAdvanceTimeout) {
                    clearTimeout(window.quizAutoAdvanceTimeout);
                }
                
                // Auto-advance setelah 3 detik HANYA jika jawaban benar (isCorrect adalah true)
                if (isCorrect) {
                    window.quizAutoAdvanceTimeout = setTimeout(() => {
                        if (modal.style.display === "flex" && !btnNext.disabled) {
                            navigateToNext();
                        }
                    }, 3000);
                }
            }
        } else {
            if (defaultActions) defaultActions.style.display = "flex";
            if (btnNext) btnNext.style.display = "none";
            if (btnRetry) {
                btnRetry.style.display = isCorrect ? "none" : "inline-block";
                btnRetry.onclick = function() {
                    // Reset kata states ke awal
                    currentLetterIndex = 0;
                    collectedPredictions = "";
                    letterScores = new Array(targetWord.length).fill(0);
                    letterPenalties = new Array(targetWord.length).fill(0);
                    
                    closeKuisSelesaiModal();
                    initWordTraining();
                    
                    if (typeof window.startTimer === 'function') {
                        window.startTimer();
                    }
                };
            }
            const checkBtn = document.getElementById("btn-default-check");
            if (checkBtn) {
                checkBtn.style.display = isCorrect ? "inline-block" : "none";
            }
        }

        modal.style.display = "flex";
    }

    // Fungsi untuk Lewati Soal
    window.lewatiSoal = async function() {
        if (typeof window.stopTimer === 'function') window.stopTimer();
        
        const btnLewati = document.getElementById('btn-lewati');
        if (btnLewati) {
            btnLewati.innerText = "Memuat...";
            btnLewati.disabled = true;
        }
        
        if (!isQuiz || !config.sessionId) {
            window.location.reload();
            return;
        }
        
        try {
            const endpoint = `/murid/quiz/submit/${config.sessionId}`;
            const payload = {
                target: targetWord,
                mode: config.modeChar,
                prediction: "Skipped",
                confidence: 0,
                is_correct: false,
                question_no: config.questionNo || 1,
                is_word: true,
                timeout: true
            };

            const response = await fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (data && data.next_url) {
                const separator = data.next_url.includes('?') ? '&' : '?';
                window.location.href = data.next_url + separator + "q=" + Date.now();
            } else {
                window.location.reload();
            }
        } catch (e) {
            console.error("Error skipping:", e);
            window.location.reload();
        }
    };