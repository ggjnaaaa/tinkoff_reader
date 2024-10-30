class SmsTimer extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: "open" });
        this.timeLeft = 30;  // Можно задать начальное значение
    }

    connectedCallback() {
        this.render();
        this.fetchTimer();
        this.shadowRoot.getElementById('resendButton').addEventListener('click', () => this.resendCode());
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                #countdown {
                    font-size: 16px;
                    margin-bottom: 10px;
                }
                #resendButton {
                    display: none;
                    padding: 8px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    cursor: pointer;
                }
            </style>
            <p id="countdown">Отправим код повторно через <span id="timer">${this.timeLeft}</span> секунд</p>
            <button id="resendButton">Отправить еще раз</button>
        `;
    }

    updateTimer(timeLeft) {
        const timerDisplay = this.shadowRoot.getElementById('timer');
        const resendButton = this.shadowRoot.getElementById('resendButton');
        
        timerDisplay.textContent = timeLeft;
        if (timeLeft <= 0) {
            timerDisplay.textContent = 0;
            resendButton.style.display = 'block';
        } else {
            resendButton.style.display = 'none';
        }
    }

    fetchTimer() {
        fetch('http://127.0.0.1:8000/tinkoff/get_sms_timer/')
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

    resendCode() {
        fetch('http://127.0.0.1:8000/tinkoff/resend_sms/', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.timeLeft = 30;
                    this.shadowRoot.getElementById('resendButton').style.display = 'none';
                    this.fetchTimer();
                } else {
                    alert('Не удалось отправить код заново.');
                }
            })
            .catch(error => console.error('Ошибка при повторной отправке:', error));
    }
}

customElements.define('sms-timer', SmsTimer);
