/* ===================================================
   GESTRA — Profil Page JavaScript
   =================================================== */

function updateVolume(val) {
  document.getElementById('volume-val').innerText = val + '%';
  // Here you can set the volume for window.speechSynthesis or audio tags
  // Since speech synthesis doesn't have a direct global volume control across all browsers perfectly, 
  // we would pass this volume to the utterance rate/volume when needed.
}

document.addEventListener('DOMContentLoaded', () => {
  /* Animate progress bars */
  setTimeout(() => {
    document.querySelectorAll('.progress-bar-fill').forEach(bar => {
      const targetWidth = bar.getAttribute('data-width');
      bar.style.width = targetWidth;
    });
  }, 300);

  /* Set input range fill based on value */
  const slider = document.getElementById('volume-slider');
  slider.addEventListener('input', function() {
    const value = (this.value-this.min)/(this.max-this.min)*100;
    this.style.background = `linear-gradient(to right, var(--blue-600) 0%, var(--blue-600) ${value}%, var(--gray-200) ${value}%, var(--gray-200) 100%)`;
  });
  // Init slider background
  slider.dispatchEvent(new Event('input'));
});
