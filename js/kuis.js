/* ===================================================
   GESTRA — Kuis Page JavaScript
   =================================================== */

/* ── Modal functions ── */
function showKodeModal() {
  const modal = document.getElementById('kode-modal');
  modal.style.display = 'flex';
  document.getElementById('input-kode').focus();
}

function closeKodeModal() {
  document.getElementById('kode-modal').style.display = 'none';
  document.getElementById('input-kode').value = '';
}

function submitKode() {
  const kode = document.getElementById('input-kode').value.trim();
  if (!kode) {
    alert('Masukkan kode kuis terlebih dahulu!');
    return;
  }
  /* Redirect ke halaman kuis soal dengan kode */
  window.location.href = `kuis-soal.html?kode=${encodeURIComponent(kode)}`;
}

document.addEventListener('DOMContentLoaded', () => {

  /* ── Close modal on overlay click ── */
  const modal = document.getElementById('kode-modal');
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeKodeModal();
  });

  /* ── Close modal on Escape ── */
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeKodeModal();
  });

  /* ── Enter key in kode input ── */
  document.getElementById('input-kode').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') submitKode();
  });

  /* ── TTS: heading & subtitle ── */
  const heading  = document.querySelector('.kuis-content h2');
  const subtitle = document.querySelector('.kuis-content p');

  if (heading) {
    heading.style.cursor = 'pointer';
    heading.title = 'Klik untuk mendengarkan';
    heading.addEventListener('click', () => speak(heading.textContent.trim()));
  }
  if (subtitle) {
    subtitle.style.cursor = 'pointer';
    subtitle.addEventListener('click', () => speak(subtitle.textContent.trim()));
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
