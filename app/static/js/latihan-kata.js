/* ===================================================
   GESTRA — Latihan Kata JavaScript
   =================================================== */

let selectedCategory = null;

function selectCategory(category, el) {
  // Deselect others
  document.querySelectorAll('.category-card').forEach(card => {
    card.classList.remove('selected');
  });

  // Select this
  el.classList.add('selected');
  selectedCategory = category;

  // Speak category
  speak(`Kategori ${category}`);
}

function mulaiLatihanKata() {
  if (!selectedCategory) {
    speak('Pilih kategori kata terlebih dahulu!');
    alert('Pilih kategori kata terlebih dahulu!');
    return;
  }
  
  speak(`Mulai latihan menulis kata kategori ${selectedCategory}`);
  
  // Redirect to canvas practice page
  setTimeout(() => {
    window.location.href = `canvas-latihan.html?kategori=${selectedCategory}`;
  }, 1000);
}

/* ── TTS helper ── */
function speak(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = 'id-ID';
  utt.rate = 0.9;
  window.speechSynthesis.speak(utt);
}

document.addEventListener('DOMContentLoaded', () => {
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
