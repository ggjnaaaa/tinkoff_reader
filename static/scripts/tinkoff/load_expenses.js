let expenseManager = null;

// Общая функция для обработки возвращенной таблицы расходов с бэка
async function loadExpenses(data) {
    // Настройка фильтра по уникальным картам
    const uniqueCards = data.cards || [];
    $('#cardFilter').select2({
        data: uniqueCards.map(card => ({ id: card, text: card })),
        placeholder: "Выберите карту",
        allowClear: true
    }).on('change', function () {
        const selectedCard = $(this).val();
        if (selectedCard) {
            expenseManager.filterByCard(selectedCard);
        } else {
            expenseManager.resetFilter();
        }
    });

    // Отображение уведомления
    showNotificationToast(data.message);

    // Получение категорий
    const categories = await fetchCategories();

    // Инициализация ExpenseManager
    if (data.expenses) {
        expenseManager = new ExpenseManager(data.expenses, categories, isMiniApp);
        expenseManager.render();
    }
    
}

// Функция для получения значения параметра из текущего URL
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// Достает токен из запроса
function getToken() {
    const token = getQueryParam('token');
    return token;
}

// Загрузка расходов с сервера с учетом выбранного дефолтного периода
async function loadExpensesByDefaultPeriod(period = 'month') {
    clearDateRange();
    showGlobalLoader();
    const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    let isRedirect = false;

    try {
        const token = getToken();
        const endpoint = token ? `/tinkoff/expenses/?token=${token}` : '/tinkoff/expenses/';
        const url = new URL(endpoint, window.location.origin);
        url.searchParams.append('period', period);
        url.searchParams.append('time_zone', userTimeZone);
        url.searchParams.append('source', currentDataSource);

        const response = await fetch(url.toString(), {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" }
        });

        history.pushState(null, null, url.toString());

        if (!response.ok) {
            hideGlobalLoader();
            const errorData = await response.json();

            if (response.status === 307) {
                showSessionExpiredModal(errorData.detail);
            } else {
                showErrorToast(errorData.detail || "Неизвестная ошибка. Повторите попытку позже.");
                console.error('Ошибка при загрузке расходов:', errorData.detail);
            }
            return;
        }

        const data = await response.json();

        if (data.redirect_url) {
            window.location.href = data.redirect_url;
            isRedirect = true;
            return;
        }

        if (data.error_message) {
            showErrorToast(data.error_message);
            return;
        }

        if (data.expenses.length === 0) {
            showErrorToast("Нет данных за выбранный период.");
            return;
        }

        await loadExpenses(data);
    } catch (error) {
        console.error('Ошибка при загрузке расходов:', error);
    } finally {
        if (!isRedirect) {
            hideGlobalLoader();
        }
    }
}

// Загрузка расходов с сервера за период
async function loadExpensesByPeriod(startDate, endDate) {
    showGlobalLoader();
    const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    let isRedirect = false;

    try {
        const token = getToken();
        const endpoint = token ? `/tinkoff/expenses/?token=${token}` : '/tinkoff/expenses/';
        const url = new URL(endpoint, window.location.origin);
        url.searchParams.append('rangeStart', startDate);
        url.searchParams.append('rangeEnd', endDate);
        url.searchParams.append('time_zone', userTimeZone);
        url.searchParams.append('source', currentDataSource);

        const response = await fetch(url.toString(), {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" }
        });

        history.pushState(null, null, url.toString());

        if (!response.ok) {
            hideGlobalLoader();
            const errorData = await response.json();

            if (response.status === 307) {
                showSessionExpiredModal(errorData.detail);
            } else {
                showErrorToast(errorData.detail || "Неизвестная ошибка. Повторите попытку позже.");
                console.error('Ошибка при загрузке расходов:', errorData.detail);
            }
            return;
        }

        const data = await response.json();

        if (data.message === "Необходима авторизация") {
            window.location.href = data.redirect_url;
            isRedirect = true;
            return;
        }

        if (data.error_message) {
            showErrorToast(data.error_message);
            return;
        }

        if (data.expenses.length === 0) {
            showInfoToast("Нет данных за выбранный период.");
            return;
        }

        await loadExpenses(data);
    } catch (error) {
        console.error('Ошибка при загрузке расходов:', error);
    } finally {
        if (!isRedirect) {
            hideGlobalLoader();
        }
    }
}

// Находим чекбокс по id
const checkbox = document.getElementById('getAllCards');

// Добавляем обработчик события на изменение состояния чекбокса
checkbox.addEventListener('change', async () => {
    showGlobalLoader();
    const showAllExpenses = checkbox.checked;
    const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const urlParams = new URLSearchParams(window.location.search);
    const rangeStart = urlParams.get("rangeStart");
    const rangeEnd = urlParams.get("rangeEnd");

    try {
        const token = getToken();
        const endpoint = `/tinkoff/expenses/?token=${token}`;
        const url = new URL(endpoint, window.location.origin);
        url.searchParams.append('rangeStart', rangeStart);
        url.searchParams.append('rangeEnd', rangeEnd);
        url.searchParams.append('time_zone', userTimeZone);
        url.searchParams.append('show_all_expenses', showAllExpenses);

        const response = await fetch(url.toString(), {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" }
        });

        history.pushState(null, null, url.toString());

        if (!response.ok) {
            hideGlobalLoader();
            const errorData = await response.json();

            if (response.status === 307) {
                showSessionExpiredModal(errorData.detail);
            } else {
                showErrorToast(errorData.detail || "Неизвестная ошибка. Повторите попытку позже.");
                console.error('Ошибка при загрузке расходов:', errorData.detail);
            }
            return;
        }

        const data = await response.json();

        if (data.error_message) {
            showErrorToast(data.error_message);
            return;
        }

        if (data.expenses.length === 0) {
            showInfoToast("Нет данных за выбранный период.");
            return;
        }

        await loadExpenses(data);
    } catch (error) {
        console.error('Ошибка при загрузке расходов:', error);
    } finally {
        hideGlobalLoader();
    }
});