class SmsTimer extends HTMLElement {
    constructor() {
        super();
        const shadowRoot = this.attachShadow({ mode: 'open' });

        // Создаём ссылку на экземпляр InputControl
        this.inputControl = document.querySelector('input-control');

        // Добавление стилей напрямую
        const style = document.createElement('style');
        style.textContent = `
            .timer-text {
                font-size: 1rem;
                color: #333;
                margin-top: 10px;
                text-align: center;
                background-color: #f9f9f9;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 3px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            #timer {
                font-weight: bold;
                color: #39D488;
            }
            button {
                display: none;
                background-color: #39D488;
                color: #000;
                padding: 8px 16px;
                font-size: 0.9rem;
                border: none;
                cursor: pointer;
                border-radius: 5px;
                margin-top: 8px;
            }
            button:hover {
                background-color: #15947a;
            }
        `;
        shadowRoot.appendChild(style);

        this.timeLeft = 45; // Начальное значение таймера
    }

    connectedCallback() {
        this.render();
        this.fetchTimer();
        this.shadowRoot
            .getElementById('resendButton')
            .addEventListener('click', () => this.resendCode());
    }

    render() {
        this.shadowRoot.innerHTML += `
            <p id="countdown" class="timer-text">Отправим код повторно через <span id="timer">${this.timeLeft}</span> сек</p>
            <button id="resendButton" type="button">Отправить еще раз</button>
        `;
    }

    updateTimer(timeLeft) {
        const timerDisplay = this.shadowRoot.getElementById('timer');
        const resendButton = this.shadowRoot.getElementById('resendButton');
        const countdown = this.shadowRoot.getElementById('countdown');
        
        timerDisplay.textContent = timeLeft;
        if (timeLeft <= 0) {
            timerDisplay.textContent = 0;
            resendButton.style.display = 'block';
            countdown.style.display = 'none';
        } else {
            resendButton.style.display = 'none';
        }
    }

    async fetchTimer() {
        const countdown = this.shadowRoot.getElementById('countdown');
        countdown.style.display = 'block';

        await fetch('/tinkoff/get_sms_timer/')
            .then(response => response.json())
            .then(data => {
                let timeLeft = data.time_left;
                this.updateTimer(timeLeft);

                const timerInterval = setInterval(() => {
                    timeLeft--;
                    this.updateTimer(timeLeft);
                    if (timeLeft <= 0) clearInterval(timerInterval);
                }, 1000);
            })
            .catch(error => console.error('Ошибка при получении таймера:', error));
    }

    async resendCode() {
        showGlobalLoader();
        
        try {
            const response = await fetch('/tinkoff/resend_sms/', { method: 'POST' });

            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 307) {
                    showSessionExpiredModal(errorData.detail);
                }
                else {
                    showError(errorData.detail);
                    console.error('Ошибка:', error);
                }
                return;
            }

            const data = await response.json();
            
            if (data.status === 'success') {
                this.timeLeft = 30;
                this.shadowRoot.getElementById('resendButton').style.display = 'none';
                
                // Здесь вызываем методы hideError и cleanInput
                if (this.inputControl) {
                    this.inputControl.hideError();
                    this.inputControl.cleanInput();
                }

                this.fetchTimer();
            }
        } catch (error) {
            this.showError('Ошибка сети. Попробуйте снова.');
            console.error('Ошибка:', error);
        } finally {
            hideGlobalLoader();
        }
    }
}

customElements.define('sms-timer', SmsTimer);
