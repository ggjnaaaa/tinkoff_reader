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
            <p id="countdown">Отправим код повторно через <span id="timer">${this.timeLeft}</span> секунд</p>
            <button id="resendButton">Отправить еще раз</button>
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

    fetchTimer() {
        const countdown = this.shadowRoot.getElementById('countdown');
        countdown.style.display = 'block';

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