/**
 * ============================================================
 *  GES-TTS: Text-to-Speech Aksesibilitas Disleksia
 *  Versi: 3.0 – Production-Ready, All Bugs Fixed
 * ============================================================
 *
 *  Perbaikan v3.0:
 *  [FIX-1]  Nested element spam: guard lastTarget mencegah re-trigger
 *           pada elemen yang sama saat kursor pindah ke child.
 *  [FIX-2]  Debounce kini closure murni, tidak lagi berbagi state.debTimer.
 *  [FIX-3]  Chromium cancel() race condition: speak() dibungkus setTimeout(50ms).
 *  [FIX-4]  loadVoices() tidak lagi dipanggil sebelum widget dirender.
 *  [FIX-5]  Memory leak: listener "klik di luar" & keydown menggunakan
 *           AbortController agar bisa di-cleanup.
 *  [FIX-6]  Panel toggle stabil: listener "klik di luar" dipasang dengan
 *           setTimeout(0) agar bubble dari klik FAB selesai lebih dulu.
 *  [FIX-7]  getElementText: prioritaskan [data-tts], lalu aria-label,
 *           lalu heading child (h1–h4), baru fallback innerText.
 *  [FIX-8]  Slider range background update via CSS custom property --val.
 *  [FIX-9]  aria-expanded selalu menggunakan string eksplisit 'true'/'false'.
 *  [FIX-10] Panel [hidden] vs display:flex — dikelola via CSS class .is-open,
 *           bukan atribut hidden bawaan HTML.
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
    RATE: 'gestra-tts-rate',
    VOICE: 'gestra-tts-voice',
  };

  /** Selector elemen interaktif target TTS */
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

  const DEBOUNCE_DELAY = 300; // ms — hover debounce
  const SPEAK_DELAY = 50;  // ms — Chromium cancel() race condition fix [FIX-3]
  const DEFAULT_RATE = 0.9; // ramah disleksia (0.8–1.0)

  // ─── State ───────────────────────────────────────────────────────────────────
  const state = {
    enabled: localStorage.getItem(STORAGE_KEY.ENABLED) !== 'false', // default ON
    rate: parseFloat(localStorage.getItem(STORAGE_KEY.RATE)) || DEFAULT_RATE,
    voice: localStorage.getItem(STORAGE_KEY.VOICE) || '',
    voices: [],
    lastText: '',   // guard anti-pengulangan teks
    lastTarget: null, // [FIX-1] guard anti-spam nested element
  };

  // AbortController untuk lifecycle listener [FIX-5]
  let outsideClickController = null;

  // ─── Utilitas ─────────────────────────────────────────────────────────────────

  /**
   * [FIX-2] Debounce murni via closure — tidak berbagi state global.
   */
  function createDebounce(fn, delay) {
    let timer = null;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  /**
   * [FIX-7] Ambil teks label dari elemen dengan prioritas yang lebih cerdas.
   * Prioritas: [data-tts] → aria-label → heading child (h1–h4) → innerText line pertama
   */
  function getElementText(el) {
    // 1. Atribut data-tts sebagai override manual
    const dataTts = el.getAttribute('data-tts');
    if (dataTts && dataTts.trim()) return dataTts.trim();

    // 2. aria-label
    const ariaLabel = el.getAttribute('aria-label');
    if (ariaLabel && ariaLabel.trim()) return ariaLabel.trim();

    // 3. Heading child — representatif untuk card/section
    const heading = el.querySelector('h1, h2, h3, h4');
    if (heading) {
      const headingText = (heading.innerText || heading.textContent || '').trim();
      if (headingText) return headingText.substring(0, 100);
    }

    // 4. Fallback: baris pertama innerText, maks 100 karakter
    const inner = (el.innerText || el.textContent || '').trim();
    return inner.split('\n')[0].trim().substring(0, 100);
  }

  // ─── Speech Engine ────────────────────────────────────────────────────────────

  function speak(text) {
    if (!state.enabled || !text) return;

    // Guard: jangan ulangi teks yang sedang/baru dibaca
    if (text === state.lastText && window.speechSynthesis.speaking) return;

    state.lastText = text;

    // [FIX-3] Chromium: cancel() + jeda 50ms sebelum speak() baru
    window.speechSynthesis.cancel();
    setTimeout(() => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = state.rate;
      utterance.lang = 'id-ID';

      // Pasang voice pilihan jika tersedia
      if (state.voice && state.voices.length) {
        const matched = state.voices.find(v => v.name === state.voice);
        if (matched) utterance.voice = matched;
      }

      window.speechSynthesis.speak(utterance);
    }, SPEAK_DELAY);
  }

  // ─── Event Delegation ─────────────────────────────────────────────────────────

  /**
   * [FIX-1] Hover handler: cegah spam saat kursor pindah ke child element
   * dalam elemen yang sama — bandingkan target hasil closest() dengan lastTarget.
   */
  const onHover = createDebounce(function (e) { // [FIX-2] closure debounce
    const el = e.target instanceof Element
      ? e.target
      : e.target?.parentElement;

    if (!el) return;

    const target = (e.target instanceof Element) ? e.target.closest(INTERACTIVE_SELECTOR) : null;

    if (!target) return;

    // Abaikan jika masih di elemen yang sama
    if (target === state.lastTarget) return;
    state.lastTarget = target;

    // Abaikan elemen dalam widget TTS sendiri
    if (target.closest('#gestra-tts-widget')) return;

    const text = getElementText(target);
    if (text) speak(text);
  }, DEBOUNCE_DELAY);
  /** Click handler — tidak di-debounce agar responsif */
  function onClick(e) {
    const el = e.target instanceof Element
      ? e.target
      : e.target?.parentElement;

    if (!el) return;

    const target = el.closest(INTERACTIVE_SELECTOR);

    if (!target) return;
    if (target.closest('#gestra-tts-widget')) return;

    const text = getElementText(target);
    if (text) speak(text);
  }
  // Pasang listener di document — otomatis support dynamic content
  document.addEventListener('mouseover', onHover, { passive: true });
  document.addEventListener('click', onClick, { passive: false });

  // Reset lastTarget & lastText saat kursor keluar dari elemen
  document.addEventListener('mouseleave', function (e) {
    const leaving = e.target.closest(INTERACTIVE_SELECTOR);
    if (leaving && leaving === state.lastTarget) {
      state.lastTarget = null;
      state.lastText = '';
    }
  }, { passive: true, capture: true }); // capture agar dapat mouseleave pada semua child

  // Escape: hentikan suara
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') window.speechSynthesis.cancel();
  }, { passive: true });

  // ─── Muat Daftar Voice ────────────────────────────────────────────────────────

  /**
   * [FIX-4] loadVoices() aman dipanggil kapan saja.
   * Akan mencari elemen select hanya jika sudah ada di DOM.
   */
  function loadVoices() {
    const available = window.speechSynthesis.getVoices();
    if (!available.length) return; // belum siap, tunggu onvoiceschanged

    state.voices = available;

    const sel = document.getElementById('gestra-tts-voice');
    if (!sel) return; // widget belum dirender — normal, akan dipanggil lagi setelah render

    sel.innerHTML = '<option value="">Default (sistem)</option>';
    state.voices.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.name;
      opt.textContent = `${v.name} (${v.lang})`;
      opt.selected = v.name === state.voice;
      sel.appendChild(opt);
    });
  }

  // Chrome memuat voices secara async
  window.speechSynthesis.onvoiceschanged = loadVoices;
  // Tidak dipanggil di sini — dipanggil setelah widget dirender [FIX-4]

  // ─── UI Widget ────────────────────────────────────────────────────────────────

  function injectWidget() {
    // Cegah duplikasi jika dipanggil dua kali
    if (document.getElementById('gestra-tts-widget')) return;

    const widget = document.createElement('div');
    widget.id = 'gestra-tts-widget';
    widget.setAttribute('aria-label', 'Panel Pengaturan Suara TTS');

    widget.innerHTML = /* html */ `
      <button
        id="gestra-tts-fab"
        title="Pengaturan Suara Aksesibilitas"
        aria-label="Buka Pengaturan Suara"
        aria-expanded="false"
        aria-controls="gestra-tts-panel"
      >
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M11 5L6 9H2V15H6L11 19V5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M15.54 8.46a5 5 0 0 1 0 7.07" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span id="gestra-tts-status-dot" class="${state.enabled ? 'active' : ''}" aria-hidden="true"></span>
      </button>

      <div
        id="gestra-tts-panel"
        role="dialog"
        aria-modal="false"
        aria-label="Pengaturan Suara Aksesibilitas"
      >
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
            aria-checked="${state.enabled ? 'true' : 'false'}"
            class="gestra-tts-switch ${state.enabled ? 'on' : ''}"
            aria-label="Suara aksesibilitas ${state.enabled ? 'aktif' : 'nonaktif'}"
          >
            <span class="gestra-tts-thumb" aria-hidden="true"></span>
            <span class="gestra-tts-switch-label" aria-hidden="true">${state.enabled ? 'ON' : 'OFF'}</span>
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
            style="--val: ${state.rate}"
            aria-label="Atur kecepatan bicara, saat ini ${state.rate.toFixed(1)} kali"
            aria-valuemin="0.5"
            aria-valuemax="1.5"
            aria-valuenow="${state.rate}"
          />
          <div class="gestra-tts-range-labels" aria-hidden="true">
            <span>Lambat</span><span>Cepat</span>
          </div>
        </div>

        <div class="gestra-tts-row gestra-tts-col">
          <label class="gestra-tts-label" for="gestra-tts-voice">Pilih Suara</label>
          <select id="gestra-tts-voice" aria-label="Pilih jenis suara">
            <option value="">Default (sistem)</option>
          </select>
        </div>

        <button id="gestra-tts-test" class="gestra-tts-test-btn" aria-label="Coba contoh suara">
          ▶ Coba Suara
        </button>
      </div>
    `;

    document.body.appendChild(widget);

    // [FIX-4] Muat voice setelah widget ada di DOM
    loadVoices();

    bindWidgetEvents(widget);
  }

  function setPanelOpen(fab, panel, isOpen) {
    // [FIX-10] Kelola visibility via CSS class .is-open, bukan atribut [hidden]
    panel.classList.toggle('is-open', isOpen);
    // [FIX-9] aria-expanded selalu string eksplisit
    fab.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  }

  function bindWidgetEvents(widget) {
    const fab = widget.querySelector('#gestra-tts-fab');
    const panel = widget.querySelector('#gestra-tts-panel');
    const toggle = widget.querySelector('#gestra-tts-toggle');
    const dot = widget.querySelector('#gestra-tts-status-dot');
    const rateEl = widget.querySelector('#gestra-tts-rate');
    const rateDisplay = widget.querySelector('#gestra-tts-rate-display');
    const voiceSel = widget.querySelector('#gestra-tts-voice');
    const testBtn = widget.querySelector('#gestra-tts-test');

    // ── Buka / Tutup Panel ─────────────────────────────────────────────────────
    fab.addEventListener('click', (e) => {
      e.stopPropagation();
      const willOpen = !panel.classList.contains('is-open');
      setPanelOpen(fab, panel, willOpen);

      if (willOpen) {
        // [FIX-6] Pasang listener "klik di luar" SETELAH event bubble selesai
        attachOutsideClickListener(fab, panel, widget);
      } else {
        detachOutsideClickListener();
      }
    });

    // ── Toggle ON/OFF ──────────────────────────────────────────────────────────
    toggle.addEventListener('click', () => {
      state.enabled = !state.enabled;
      localStorage.setItem(STORAGE_KEY.ENABLED, String(state.enabled));

      // [FIX-9] String eksplisit untuk aria-checked
      toggle.setAttribute('aria-checked', state.enabled ? 'true' : 'false');
      toggle.setAttribute('aria-label', `Suara aksesibilitas ${state.enabled ? 'aktif' : 'nonaktif'}`);
      toggle.classList.toggle('on', state.enabled);
      toggle.querySelector('.gestra-tts-switch-label').textContent = state.enabled ? 'ON' : 'OFF';
      dot.classList.toggle('active', state.enabled);

      if (!state.enabled) {
        window.speechSynthesis.cancel();
      } else {
        state.lastText = ''; // izinkan speak() berjalan
        speak('Suara aksesibilitas diaktifkan.');
      }
    });

    // ── Rate Slider ────────────────────────────────────────────────────────────
    rateEl.addEventListener('input', () => {
      state.rate = parseFloat(rateEl.value);

      // [FIX-8] Update CSS custom property agar track slider berubah warna
      rateEl.style.setProperty('--val', state.rate);
      rateEl.setAttribute('aria-valuenow', state.rate);

      rateDisplay.textContent = state.rate.toFixed(1) + '×';
      localStorage.setItem(STORAGE_KEY.RATE, String(state.rate));
    });

    // ── Voice Selector ─────────────────────────────────────────────────────────
    voiceSel.addEventListener('change', () => {
      state.voice = voiceSel.value;
      localStorage.setItem(STORAGE_KEY.VOICE, state.voice);
    });

    // ── Test Button ────────────────────────────────────────────────────────────
    testBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      state.lastText = ''; // paksa baca ulang meski teks sama
      speak('Halo! Ini adalah contoh suara untuk pengguna GESTRA.');
    });
  }

  // ─── Outside Click — dengan AbortController [FIX-5][FIX-6] ──────────────────

  function attachOutsideClickListener(fab, panel, widget) {
    // Bersihkan controller lama jika ada
    detachOutsideClickListener();

    outsideClickController = new AbortController();
    const { signal } = outsideClickController;

    // [FIX-6] setTimeout(0) agar event bubble dari klik FAB selesai dulu
    setTimeout(() => {
      if (signal.aborted) return;

      document.addEventListener('click', (e) => {
        if (!widget.contains(e.target)) {
          setPanelOpen(fab, panel, false);
          detachOutsideClickListener();
        }
      }, { signal, passive: false });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          setPanelOpen(fab, panel, false);
          window.speechSynthesis.cancel();
          detachOutsideClickListener();
        }
      }, { signal, passive: true });
    }, 0);
  }

  function detachOutsideClickListener() {
    if (outsideClickController) {
      outsideClickController.abort();
      outsideClickController = null;
    }
  }

  // ─── Bootstrap ────────────────────────────────────────────────────────────────

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectWidget);
  } else {
    injectWidget();
  }

})();
