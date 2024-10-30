// disconnect-button.js
class DisconnectButton extends HTMLElement {
    constructor() {
        super();

        // Создаем Shadow DOM
        this.attachShadow({ mode: 'open' });

        // Создаем и стилизуем кнопку
        const button = document.createElement('button');
        button.innerHTML = '&#10006;';
        button.style.position = 'fixed';
        button.style.top = '10px';
        button.style.right = '10px';

        // Добавляем кнопку в Shadow DOM
        this.shadowRoot.appendChild(button);

        // Добавляем обработчик события
        button.addEventListener('click', () => {
            fetch('/tinkoff/disconnect/', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                window.location.href = '/';  // Перенаправляем на главную после disconnect
            })
            .catch(error => {
                console.error('Ошибка при disconnect:', error);
            });
        });
    }
}

// Регистрируем новый элемент
customElements.define('disconnect-button', DisconnectButton);