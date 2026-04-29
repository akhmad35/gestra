/* ===================================================
   GESTRA — Latihan Menulis Huruf JavaScript
   =================================================== */

/* ── Data sets ── */
const DATA = {
  angka:      ['1','2','3','4','5','6','7','8','9','0'],
  hurufBesar: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split(''),
  hurufKecil: 'abcdefghijklmnopqrstuvwxyz'.split(''),
};

let currentTab = 'angka';
let selectedChar = null;

/* ── Render characters grid ── */
function renderChars(tab) {
  const grid = document.getElementById('chars-grid');
  grid.innerHTML = '';

  DATA[tab].forEach((char, i) => {
    const btn = document.createElement('button');
    btn.className = 'char-btn';
    btn.id = `char-${char}-${i}`;
    btn.textContent = char;
    btn.setAttribute('aria-label', `Huruf ${char}`);
    btn.style.animationDelay = `${i * 0.03}s`;

    btn.addEventListener('click', () => selectChar(char, btn));
    grid.appendChild(btn);
  });
}

/* ── Select a character ── */
function selectChar(char, btn) {
  /* Deselect previous */
  document.querySelectorAll('.char-btn.selected').forEach(b => b.classList.remove('selected'));

  btn.classList.add('selected');
  selectedChar = char;

  /* Speak the character */
  speak(char);
}

/* ── Switch tab ── */
function switchTab(tab, btnEl) {
  currentTab   = tab;
  selectedChar = null;

  /* Update tab button states */
  document.querySelectorAll('.tab-btn').forEach(b => {
    b.classList.remove('active');
    b.setAttribute('aria-selected', 'false');
  });
  btnEl.classList.add('active');
  btnEl.setAttribute('aria-selected', 'true');

  /* Re-render grid */
  renderChars(tab);
}

/* ── Mulai button ── */
function mulaiLatihan() {
  if (!selectedChar) {
    speak('Pilih huruf atau angka terlebih dahulu!');
    showToast('Pilih huruf atau angka terlebih dahulu!');
    return;
  }
  speak(`Ayo tulis huruf ${selectedChar}`);
  showToast(`Ayo tulis: ${selectedChar} 🎉`);
}

/* ── Toast notification ── */
function showToast(msg) {
  let toast = document.getElementById('gestra-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'gestra-toast';
    toast.style.cssText = `
      position:fixed; bottom:32px; left:50%; transform:translateX(-50%) translateY(20px);
      background:#1D4ED8; color:#fff; padding:12px 28px; border-radius:50px;
      font-family:'Nunito',sans-serif; font-size:.92rem; font-weight:700;
      box-shadow:0 6px 24px rgba(37,99,235,.35); opacity:0;
      transition:all .3s ease; z-index:999; white-space:nowrap;
    `;
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.opacity = '1';
  toast.style.transform = 'translateX(-50%) translateY(0)';
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(-50%) translateY(20px)';
  }, 2500);
}

/* ── TTS helper ── */
function speak(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = 'id-ID';
  utt.rate = 0.85;
  window.speechSynthesis.speak(utt);
}

/* ── Init ── */
document.addEventListener('DOMContentLoaded', () => {
  renderChars('angka');

  /* TTS: info header */
  document.querySelectorAll('.info-header-text p').forEach(p => {
    p.style.cursor = 'pointer';
    p.title = 'Klik untuk mendengarkan';
    p.addEventListener('click', () => speak(p.textContent.trim()));
  });

  const heading = document.querySelector('.info-header-text h2');
  if (heading) {
    heading.style.cursor = 'pointer';
    heading.addEventListener('click', () => speak(heading.textContent.trim()));
  }
});
