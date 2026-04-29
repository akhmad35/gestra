/* ===================================================
   GESTRA — Canvas Latihan JavaScript
   =================================================== */

function showKuisSelesaiModal() {
  const modal = document.getElementById('modal-selesai');
  modal.style.display = 'flex';
  speak('Horee! Kuis Selesai!');
}

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

/* ── TTS helper ── */
function speak(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = 'id-ID';
  utt.rate = 0.9;
  window.speechSynthesis.speak(utt);
}
