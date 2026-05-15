function handleBackButton() {
  if (window.history.length > 1) {
    window.history.back();
  } else {
    window.location.href = '/beranda';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  const hidePaths = ['/', '/login', '/register', '/pilih-peran', '/beranda'];
  
  if (hidePaths.includes(path)) {
    document.body.classList.add('hide-back-btn');
  }
});


