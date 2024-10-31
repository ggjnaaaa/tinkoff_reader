// disconnect-button.js
class DisconnectButton extends HTMLElement {
    constructor() {
        super();

        // Создаем Shadow DOM
        const shadowRoot = this.attachShadow({ mode: 'open' });

        // Добавление стилей
        const link = document.createElement('link');
        link.setAttribute('rel', 'stylesheet');
        link.setAttribute('href', '/static/tinkoff_style.css');
        shadowRoot.appendChild(link);

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