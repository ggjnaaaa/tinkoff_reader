console.log("sms_code.js загружен");
alert("sms_code.js подключен");

// Функция для обновления таймера
function updateTimer(timeLeft) {
    document.getElementById('timer').textContent = timeLeft;
    if (timeLeft <= 0) {
        document.getElementById('timer').textContent = 0;
        document.getElementById('resendButton').style.display = 'block';  // Показать кнопку
    } else {
        document.getElementById('resendButton').style.display = 'none';   // Скрыть кнопку до истечения таймера
    }
}

// Получаем таймер с бэкенда, чтобы синхронизироваться с таймером на сайте Тинькофф
function fetchTimer() {
    fetch('http://127.0.0.1:8000/process/get_sms_timer/')  // Запрос на получение оставшегося времени до повторной отправки
        .then(response => response.json())
        .then(data => {
            let timeLeft = data.time_left;
            updateTimer(timeLeft);

            // Обновляем таймер каждую секунду
            const timerInterval = setInterval(() => {
                timeLeft--;
                updateTimer(timeLeft);

                if (timeLeft <= 0) {
                    clearInterval(timerInterval);  // Остановить таймер
                }
            }, 1000);
        })
        .catch(error => {
            console.error('Ошибка при получении таймера:', error);
        });
}

// Загружаем таймер при загрузке страницы
window.onload = fetchTimer;

// Нажатие на кнопку "Отправить еще раз"
document.getElementById('resendButton').addEventListener('click', function() {
    fetch('http://127.0.0.1:8000/process/resend_sms/', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        // Очистка инпута
        document.getElementById('sms_code').value = '';
        errorMessage.style.display = 'none'; // Скрываем ошибку

        if (data.status === 'success') {
            // Скрыть кнопку и перезапустить отсчет
            document.getElementById('resendButton').style.display = 'none';
            document.getElementById('countdown').style.display = 'block';
            fetchTimer();
        } else {
            alert('Не удалось отправить код заново.');
        }
    })
    .catch(error => {
        console.error('Ошибка при повторной отправке:', error);
    });
});