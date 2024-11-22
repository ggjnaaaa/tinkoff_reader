let expenseManager = null;

// Общая функция для обработки возвращенной таблицы расходов с бэка
async function loadExpenses(data) {
    // Настройка уникальных карт для фильтрации
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

    // Проверка источника и периода
    showNotificationToast(data.message);

    const categories = await fetchCategories();

    expenseManager = new ExpenseManager(data.expenses, categories);
    expenseManager.render();
}

// Загрузка расходов с сервера с учетом выбранного дефолтного периода
async function loadExpensesByDefaultPeriod(period = 'month') {
    clearDateRange();
    showGlobalLoader();
    const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    let isRedirect = false;

    try {
        const response = await fetch(`/tinkoff/expenses/?period=${period}&time_zone=${userTimeZone}&source=${currentDataSource}`, {
            method: "GET",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        });
        history.pushState(null, null, `/tinkoff/expenses/?period=${period}&time_zone=${userTimeZone}`);

        if (!response.ok) {
            hideGlobalLoader();
            const errorData = await response.json();

            if (response.status === 307) {
                showSessionExpiredModal(errorData.detail);
            }
            else {
                showErrorToast(errorData.detail || "Неизвестная ошибка. Повторите попытку позже.");
                console.error('Ошибка при загрузке расходов:', error);
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
        const response = await fetch(`/tinkoff/expenses/?rangeStart=${startDate}&rangeEnd=${endDate}&time_zone=${userTimeZone}&source=${currentDataSource}`, {
            method: "GET",
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        });
        history.pushState(null, null, `/tinkoff/expenses/?rangeStart=${startDate}&rangeEnd=${endDate}&time_zone=${userTimeZone}`);

        if (!response.ok) {
            hideGlobalLoader();
            const errorData = await response.json();

            if (response.status === 307) {
                showSessionExpiredModal(errorData.detail);
            }
            else {
                showErrorToast(errorData.detail || "Неизвестная ошибка. Повторите попытку позже.");
                console.error('Ошибка при загрузке расходов:', error);
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