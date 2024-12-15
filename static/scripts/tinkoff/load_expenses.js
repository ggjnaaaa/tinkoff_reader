let expenseManager = null;
let is_for_one_card = null;

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

    is_for_one_card = data.cards ? false : true;

    // Инициализация ExpenseManager
    expenseManager = new ExpenseManager(data.expenses, categories, is_for_one_card);
    expenseManager.render();
}

// Функция для получения значения параметра из текущего URL
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// Выбор эндпоинта на основе наличия токена
function getExpensesEndpoint() {
    const token = getQueryParam('token');
    return token ? `/bot/expenses/?token=${token}` : '/tinkoff/expenses/';
}

// Загрузка расходов с сервера с учетом выбранного дефолтного периода
async function loadExpensesByDefaultPeriod(period = 'month') {
    clearDateRange();
    showGlobalLoader();
    const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    let isRedirect = false;

    try {
        const endpoint = getExpensesEndpoint();
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
        const endpoint = getExpensesEndpoint();
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
