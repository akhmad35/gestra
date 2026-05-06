/**
 * ============================================================
 *  GES-TTS: Text-to-Speech Aksesibilitas Disleksia
 *  Versi: 2.0 – Audio-Only, Zero Visual Impact
 * ============================================================
 *
 *  Cara kerja:
 *  1. Satu event listener di `document` (event delegation) menangkap
 *     semua interaksi hover & click pada elemen interaktif.
 *  2. Debounce 300ms pada hover mencegah spam suara saat kursor bergerak cepat.
 *  3. Guard `lastText` mencegah pengulangan suara teks yang sama berturut-turut.
 *  4. `speechSynthesis.cancel()` selalu dijalankan sebelum utterance baru.
 *  5. Semua efek visual dinonaktifkan — fitur ini murni audio feedback.
 *  6. Preferensi pengguna (aktif/nonaktif, rate, suara) disimpan di localStorage.
 */

(function () {
  'use strict';

  // ─── Fallback Browser Check ─────────────────────────────────────────────────
  if (!window.speechSynthesis) {
    console.warn('[GES-TTS] Browser tidak mendukung Web Speech API. Fitur TTS dinonaktifkan.');
    return;
  }

  // ─── Konstanta ───────────────────────────────────────────────────────────────
  const STORAGE_KEY = {
    ENABLED: 'gestra-tts-enabled',
    RATE:    'gestra-tts-rate',
    VOICE:   'gestra-tts-voice',
  };

  // Selector elemen interaktif yang menjadi target TTS
  const INTERACTIVE_SELECTOR = [
    'a[href]',
    'button',
    '[role="button"]',
    '[onclick]',
    'input[type="submit"]',
    'input[type="button"]',
    'input[type="reset"]',
    'label[for]',
    '.card',
    '.menu-item',
    '.nav-btn',
    '[data-tts]',
  ].join(', ');

  const DEBOUNCE_DELAY = 300; // ms
  const DEFAULT_RATE   = 0.9; // ramah disleksia (0.8–1.0)

  // ─── State ───────────────────────────────────────────────────────────────────
  const state = {
    enabled:  localStorage.getItem(STORAGE_KEY.ENABLED) !== 'false', // default ON
    rate:     parseFloat(localStorage.getItem(STORAGE_KEY.RATE)) || DEFAULT_RATE,
    voice:    localStorage.getItem(STORAGE_KEY.VOICE) || '',
    voices:   [],
    lastText: '',             // guard anti-pengulangan teks
    debTimer: null,           // referensi debounce timer
  };

  // ─── Utilitas ─────────────────────────────────────────────────────────────────

  /**
   * Ambil teks label dari sebuah elemen.
   * Prioritas: aria-label → innerText → textContent
   */
  function getElementText(el) {
    const ariaLabel = el.getAttribute('aria-label');
    if (ariaLabel && ariaLabel.trim()) return ariaLabel.trim();

    const inner = (el.innerText || el.textContent || '').trim();
    // Ambil hanya baris pertama / teks pendek agar tidak membaca paragraf panjang
    return inner.split('\n')[0].trim().substring(0, 120);
  }

  /** Debounce wrapper */
  function debounce(fn, delay) {
    return function (...args) {
      clearTimeout(state.debTimer);
      state.debTimer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  // ─── Speech Engine ────────────────────────────────────────────────────────────

  function speak(text) {
    if (!state.enabled || !text) return;

    // Guard: jangan ulangi teks yang baru saja dibaca
    if (text === state.lastText && window.speechSynthesis.speaking) return;

    state.lastText = text;

    // Hentikan ucapan sebelumnya
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = state.rate;
    utterance.lang = 'id-ID'; // fallback bahasa Indonesia

    // Pasang voice pilihan jika tersedia
    if (state.voice && state.voices.length) {
      const matched = state.voices.find(v => v.name === state.voice);
      if (matched) utterance.voice = matched;
    }

    window.speechSynthesis.speak(utterance);
  }

  // ─── Event Delegation ─────────────────────────────────────────────────────────

  // Hover dengan debounce
  const onHover = debounce(function (e) {
    const target = e.target.closest(INTERACTIVE_SELECTOR);
    if (!target) return;

    const text = getElementText(target);
    if (text) speak(text);
  }, DEBOUNCE_DELAY);

  // Click langsung (tidak di-debounce agar responsif)
  function onClick(e) {
    const target = e.target.closest(INTERACTIVE_SELECTOR);
    if (!target) return;

    // Kecualikan klik pada widget TTS sendiri agar tidak tumpang-tindih
    if (target.closest('#gestra-tts-widget')) return;

    const text = getElementText(target);
    if (text) speak(text);
  }

  // Pasang listener di document — otomatis support dynamic content
  document.addEventListener('mouseover', onHover, { passive: true });
  document.addEventListener('click',     onClick,  { passive: false });

  // Hentikan suara saat kursor meninggalkan elemen
  document.addEventListener('mouseout', function (e) {
    const leaving = e.target.closest(INTERACTIVE_SELECTOR);
    if (leaving) {
      // Reset lastText agar teks yang sama bisa dibaca lagi saat re-hover
      state.lastText = '';
    }
  }, { passive: true });

  // ─── Muat Daftar Voice ────────────────────────────────────────────────────────

  function loadVoices() {
    state.voices = window.speechSynthesis.getVoices();
    const sel = document.getElementById('gestra-tts-voice');
    if (!sel || !state.voices.length) return;

    sel.innerHTML = '<option value="">Default (sistem)</option>';
    state.voices.forEach(v => {
      const opt = document.createElement('option');
      opt.value       = v.name;
      opt.textContent = `${v.name} (${v.lang})`;
      opt.selected    = v.name === state.voice;
      sel.appendChild(opt);
    });
  }

  // Chrome memuat voices async
  window.speechSynthesis.onvoiceschanged = loadVoices;
  loadVoices();

  // ─── UI Widget ────────────────────────────────────────────────────────────────

  function injectWidget() {
    const widget = document.createElement('div');
    widget.id = 'gestra-tts-widget';
    widget.setAttribute('aria-label', 'Panel Pengaturan Suara TTS');

    widget.innerHTML = /* html */ `
      <button id="gestra-tts-fab" title="Pengaturan Suara Aksesibilitas" aria-label="Buka Pengaturan Suara">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M11 5L6 9H2V15H6L11 19V5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M15.54 8.46a5 5 0 0 1 0 7.07" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span id="gestra-tts-status-dot" class="${state.enabled ? 'active' : ''}"></span>
      </button>

      <div id="gestra-tts-panel" role="dialog" aria-modal="false" aria-label="Pengaturan TTS" hidden>
        <div class="gestra-tts-panel-header">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M11 5L6 9H2V15H6L11 19V5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Suara Aksesibilitas</span>
        </div>

        <div class="gestra-tts-row">
          <label class="gestra-tts-label" for="gestra-tts-toggle">Aktifkan Suara</label>
          <button
            id="gestra-tts-toggle"
            role="switch"
            aria-checked="${state.enabled}"
            class="gestra-tts-switch ${state.enabled ? 'on' : ''}"
            aria-label="Toggle TTS ${state.enabled ? 'aktif' : 'nonaktif'}"
          >
            <span class="gestra-tts-thumb"></span>
            <span class="gestra-tts-switch-label">${state.enabled ? 'ON' : 'OFF'}</span>
          </button>
        </div>

        <div class="gestra-tts-row gestra-tts-col">
          <label class="gestra-tts-label" for="gestra-tts-rate">
            Kecepatan Bicara
            <strong id="gestra-tts-rate-display">${state.rate.toFixed(1)}×</strong>
          </label>
          <input
            type="range"
            id="gestra-tts-rate"
            min="0.5" max="1.5" step="0.1"
            value="${state.rate}"
            aria-label="Atur kecepatan bicara"
          />
          <div class="gestra-tts-range-labels">
            <span>Lambat</span><span>Cepat</span>
          </div>
        </div>

        <div class="gestra-tts-row gestra-tts-col">
          <label class="gestra-tts-label" for="gestra-tts-voice">Pilih Suara</label>
          <select id="gestra-tts-voice" aria-label="Pilih jenis suara">
            <option value="">Default (sistem)</option>
          </select>
        </div>

        <button id="gestra-tts-test" class="gestra-tts-test-btn" aria-label="Coba suara">
          ▶ Coba Suara
        </button>
      </div>
    `;

    document.body.appendChild(widget);
    loadVoices();
    bindWidgetEvents(widget);
  }

  function bindWidgetEvents(widget) {
    const fab    = widget.querySelector('#gestra-tts-fab');
    const panel  = widget.querySelector('#gestra-tts-panel');
    const toggle = widget.querySelector('#gestra-tts-toggle');
    const dot    = widget.querySelector('#gestra-tts-status-dot');
    const rate   = widget.querySelector('#gestra-tts-rate');
    const rateDisplay = widget.querySelector('#gestra-tts-rate-display');
    const voice  = widget.querySelector('#gestra-tts-voice');
    const testBtn = widget.querySelector('#gestra-tts-test');

    // Buka / tutup panel
    fab.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = !panel.hidden;
      panel.hidden = isOpen;
      fab.setAttribute('aria-expanded', !isOpen);
    });

    // Tutup saat klik di luar
    document.addEventListener('click', (e) => {
      if (!panel.hidden && !widget.contains(e.target)) {
        panel.hidden = true;
        fab.setAttribute('aria-expanded', false);
      }
    });

    // Toggle ON/OFF
    toggle.addEventListener('click', () => {
      state.enabled = !state.enabled;
      localStorage.setItem(STORAGE_KEY.ENABLED, state.enabled);

      toggle.setAttribute('aria-checked', state.enabled);
      toggle.setAttribute('aria-label', `Toggle TTS ${state.enabled ? 'aktif' : 'nonaktif'}`);
      toggle.classList.toggle('on', state.enabled);
      toggle.querySelector('.gestra-tts-switch-label').textContent = state.enabled ? 'ON' : 'OFF';
      dot.classList.toggle('active', state.enabled);

      if (!state.enabled) window.speechSynthesis.cancel();
      else speak('Suara aksesibilitas diaktifkan.');
    });

    // Rate slider
    rate.addEventListener('input', () => {
      state.rate = parseFloat(rate.value);
      rateDisplay.textContent = state.rate.toFixed(1) + '×';
      localStorage.setItem(STORAGE_KEY.RATE, state.rate);
    });

    // Voice selector
    voice.addEventListener('change', () => {
      state.voice = voice.value;
      localStorage.setItem(STORAGE_KEY.VOICE, state.voice);
    });

    // Test button
    testBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      state.lastText = ''; // paksa baca ulang
      speak('Halo! Ini adalah contoh suara untuk pengguna GESTRA.');
    });

    // Tombol Escape menutup panel
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        panel.hidden = true;
        window.speechSynthesis.cancel();
      }
    });
  }

  // ─── Bootstrap ────────────────────────────────────────────────────────────────

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectWidget);
  } else {
    injectWidget();
  }

})();
