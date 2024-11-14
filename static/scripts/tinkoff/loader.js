const loader_overlay = document.getElementById("global-loader")

function showGlobalLoader() {
    if (loader_overlay) {
        loader_overlay.style.display = 'flex';
    } else {
        console.error('Глобальный лоадер не найден');
    }
}

function hideGlobalLoader() {
    if (loader_overlay) {
        loader_overlay.style.display = 'none';
    } else {
        console.error('Глобальный лоадер не найден');
    }
}
