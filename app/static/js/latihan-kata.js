/* ===================================================
   GESTRA — Latihan Kata (Category Selection)
   =================================================== */

// Database kata per kategori
const KATEGORI_KATA = {
    'Buah': ['apel', 'mangga', 'pisang', 'jeruk', 'nanas', 'melon'],
    'Hewan': ['kucing', 'anjing', 'gajah', 'singa', 'kuda', 'zebra'],
    'Benda': ['meja', 'kursi', 'buku', 'lampu', 'tas', 'botol'],
    'Hari': ['senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu'],
    'Warna': ['merah', 'biru', 'hijau', 'kuning', 'ungu', 'putih'],
    'Negara': ['jepang', 'korea', 'rusia', 'china', 'mesir', 'india']
};

let selectedCategory = null;

function selectCategory(category, element) {
    // Hapus seleksi sebelumnya
    document.querySelectorAll('.category-card').forEach(card => {
        card.classList.remove('selected');
        card.style.borderColor = '#E2E8F0';
        card.style.background = 'white';
    });

    // Tandai kategori yang dipilih
    selectedCategory = category;
    element.classList.add('selected');
    element.style.borderColor = '#3B82F6';
    element.style.background = '#EFF6FF';

    speak(`Kategori ${category} dipilih`);
}

function mulaiLatihanKata() {
    if (!selectedCategory) {
        speak('Pilih kategori terlebih dahulu ya!');
        return;
    }

    // Ambil kata acak dari kategori tersebut
    const daftarKata = KATEGORI_KATA[selectedCategory];
    const kataAcak = daftarKata[Math.floor(Math.random() * daftarKata.length)];

    speak(`Mari menulis kata ${kataAcak}`);

    // Pindah ke halaman kanvas dengan membawa parameter kata target
    setTimeout(() => {
        window.location.href = `canvas-latihan-kata.html?target=${kataAcak}`;
    }, 800);
}

function speak(text) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = 'id-ID';
    utt.rate = 0.9;
    window.speechSynthesis.speak(utt);
}

// Di dalam canvas-latihan-kata.js kamu:
async function periksaTulisan() {
    const dataURL = paintCanvas.toDataURL('image/png');
    
    try {
        const response = await fetch("/predict-word", { // <--- Pastikan ini predict-word
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                target: targetWord,
                image: dataURL
            })
        });
        
        const data = await response.json();
        showModalResult(data);
    } catch (error) {
        alert("Server GESTRA tidak merespon");
    }
}