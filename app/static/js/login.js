/* ===================================================
   GESTRA — Login Page JavaScript
   =================================================== */

document.addEventListener('DOMContentLoaded', () => {

  const form      = document.getElementById('login-form');
  const emailEl   = document.getElementById('email');
  const passEl    = document.getElementById('password');
  const btnMasuk  = document.getElementById('btn-masuk');
  const btnGoogle = document.getElementById('btn-google');

  /* ── Simple form validation ── */
  function showError(input, msg) {
    clearError(input);
    input.style.borderColor = '#EF4444';
    const err = document.createElement('p');
    err.className = 'field-error';
    err.style.cssText = 'color:#EF4444;font-size:.78rem;margin-top:5px;font-weight:600;';
    err.textContent = msg;
    input.parentNode.appendChild(err);
  }

  function clearError(input) {
    input.style.borderColor = '';
    const prev = input.parentNode.querySelector('.field-error');
    if (prev) prev.remove();
  }

  function isValidEmail(v) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
  }

  /* ── Submit handler ── */
  form.addEventListener('submit', (e) => {
    let valid = true;

    clearError(emailEl);
    clearError(passEl);

    if (!emailEl.value.trim()) {
      showError(emailEl, 'Email tidak boleh kosong.'); valid = false;
    } else if (!isValidEmail(emailEl.value.trim())) {
      showError(emailEl, 'Format email tidak valid.'); valid = false;
    }

    if (!passEl.value) {
      showError(passEl, 'Password tidak boleh kosong.'); valid = false;
    } else if (passEl.value.length < 6) {
      showError(passEl, 'Password minimal 6 karakter.'); valid = false;
    }

    if (!valid) {
      e.preventDefault(); // Stop submission only if invalid
      return;
    }

    /* ── Loading state ── */
    btnMasuk.disabled = true;
    btnMasuk.textContent = 'Sedang masuk...';
    // Form will now submit naturally to the backend via POST /login
  });

  /* ── Google login placeholder ── */
  btnGoogle.addEventListener('click', () => {
    alert('Fitur login dengan Google akan segera tersedia!');
  });

  /* ── Clear errors on input ── */
  emailEl.addEventListener('input', () => clearError(emailEl));
  passEl.addEventListener('input',  () => clearError(passEl));

  /* ── Text-to-speech for sound badge ── */
  const soundBadge = document.querySelector('.sound-badge');
  if (soundBadge) {
    soundBadge.style.cursor = 'pointer';
    soundBadge.title = 'Klik untuk mendengarkan';
    soundBadge.addEventListener('click', () => {
      speak('Website ini dibuat agar semua bagiannya bisa bersuara');
    });
  }
});

/* ── TTS helper ── */
function speak(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = 'id-ID';
  utt.rate = 0.95;
  window.speechSynthesis.speak(utt);
}
