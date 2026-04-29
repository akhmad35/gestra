/* ===================================================
   GESTRA — Beranda Page JavaScript
   =================================================== */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Animate progress circles on scroll ── */
  const circles = document.querySelectorAll('.progress-bar');
  const circumference = 2 * Math.PI * 20; // r=20

  function animateCircle(el, percent) {
    const offset = circumference - (percent / 100) * circumference;
    el.style.strokeDasharray  = circumference;
    el.style.strokeDashoffset = circumference; // start at 0%
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        el.style.transition = 'stroke-dashoffset 1s ease';
        el.style.strokeDashoffset = offset;
      });
    });
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const bar     = entry.target.querySelector('.progress-bar');
        const textEl  = entry.target.querySelector('.progress-text');
        const percent = parseInt(textEl.textContent) || 75;
        animateCircle(bar, percent);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.progress-circle').forEach(c => observer.observe(c));

  /* ── TTS: Sound badge ── */
  const soundBadge = document.querySelector('.sound-badge');
  if (soundBadge) {
    soundBadge.style.cursor = 'pointer';
    soundBadge.title = 'Klik untuk mendengarkan';
    soundBadge.addEventListener('click', () => {
      speak('Website ini dibuat agar semua bagiannya bisa bersuara');
    });
  }

  /* ── TTS: Level card titles ── */
  document.querySelectorAll('.level-card-title').forEach(el => {
    el.style.cursor = 'pointer';
    el.addEventListener('click', (e) => {
      e.preventDefault();
      speak(el.textContent.trim());
    });
  });

  /* ── TTS: Quiz CTA ── */
  const quizTitle = document.querySelector('.quiz-cta-content h3');
  if (quizTitle) {
    quizTitle.style.cursor = 'pointer';
    quizTitle.addEventListener('click', () => speak(quizTitle.textContent));
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
