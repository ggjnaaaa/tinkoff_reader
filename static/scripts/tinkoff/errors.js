// Эмуляция истечения сессии и вызов окна
function showSessionExpiredModal(message) {
    document.getElementById('session-expired-modal').style.display = 'flex';
    document.getElementById('redirect-error-text').innerText = message;
}

// Обработчики для кнопок в модальном окне
document.getElementById('retry-login').addEventListener('click', async function() {
    window.location.href = '/tinkoff/';
});

document.getElementById('go-to-expenses').addEventListener('click', async function() {
    await fetch('/tinkoff/disconnect/', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        window.location.href = '/tinkoff/expenses/page';  // Перенаправляем на главную после disconnect
    })
    .catch(error => {
        console.error('Ошибка при disconnect:', error);
    });
});

// Всплывающая ошибка
function showErrorToast(message) {
    const toast = document.getElementById('error-toast');
    toast.querySelector('span').textContent = message; // Устанавливаем текст ошибки
    toast.classList.add('show');
    
    // Скрываем уведомление через 5 секунд
    setTimeout(() => {
        toast.classList.remove('show');
    }, 5000);
}

// Всплывающее оповещение
function showNotificationToast(message) {
    const toast = document.getElementById('notification-toast');
    toast.querySelector('span').textContent = message; // Устанавливаем текст ошибки
    toast.classList.add('show');
    
    // Скрываем уведомление через 5 секунд
    setTimeout(() => {
        toast.classList.remove('show');
    }, 5000);
}