// disconnect-button.js
class DisconnectButton extends HTMLElement {
    constructor() {
        super();

        // Создаем Shadow DOM
        const shadowRoot = this.attachShadow({ mode: 'open' });

        // Создаем и стилизуем кнопку
        const button = document.createElement('button');
        button.setAttribute('part', 'button');
        button.style.position = 'fixed';
        button.style.top = '15px';
        button.style.right = '8%';
        button.style.height = '31px'

        // Добавляем SVG для крестика
        button.innerHTML = `
            <svg width="15" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M6 6L18 18" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;

        // Добавляем кнопку в Shadow DOM
        this.shadowRoot.appendChild(button);

        // Добавляем обработчик события
        button.addEventListener('click', async () => {
            showGlobalLoader();

            await fetch('/tinkoff/disconnect/', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                window.location.href = '/';  // Перенаправляем на главную после disconnect
            })
            .catch(error => {
                hideGlobalLoader();
                console.error('Ошибка при disconnect:', error);
            });

            hideGlobalLoader();
        });
    }
}

// Регистрируем новый элемент
customElements.define('disconnect-button', DisconnectButton);