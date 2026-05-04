/* ===================================================
   GESTRA — Materi Page JavaScript
   =================================================== */

document.addEventListener('DOMContentLoaded', () => {

  /* ── TTS: Info header ── */
  const infoTitle = document.querySelector('.info-header-text h2');
  const infoDesc  = document.querySelector('.info-header-text p');

  if (infoTitle) {
    infoTitle.style.cursor = 'pointer';
    infoTitle.title = 'Klik untuk mendengarkan';
    infoTitle.addEventListener('click', () => speak(infoTitle.textContent.trim()));
  }
  if (infoDesc) {
    infoDesc.style.cursor = 'pointer';
    infoDesc.addEventListener('click', () => speak(infoDesc.textContent.trim()));
  }

  /* ── TTS: Each card title ── */
  document.querySelectorAll('.materi-card-info h4').forEach(el => {
    el.style.cursor = 'pointer';
    el.addEventListener('click', (e) => {
      e.preventDefault();
      speak(el.textContent.trim());
    });
  });

  /* ── Hover ripple effect on cards ── */
  document.querySelectorAll('.materi-card').forEach(card => {
    card.addEventListener('mouseenter', () => {
      card.style.borderColor = 'var(--blue-300)';
    });
    card.addEventListener('mouseleave', () => {
      card.style.borderColor = '';
    });
  });
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
