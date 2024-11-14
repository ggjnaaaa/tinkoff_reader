// Код jQuery для настройки столбцов с изменяемой шириной
$(window).on('load', function() {
    $('#expensesTable').resizableColumns();
    
    $('#itemsPerPageSelect').select2({
        width: 'auto',  // Подгонка под размер текста
        minimumResultsForSearch: Infinity  // Убираем поле поиска
    });
});

// Вызов отображения расходов за месяц
document.addEventListener("DOMContentLoaded", function () {
    showGlobalLoader();

    const urlParams = new URLSearchParams(window.location.search);
    const period = urlParams.get("period");
    const rangeStart = urlParams.get("rangeStart");
    const rangeEnd = urlParams.get("rangeEnd");

    if (rangeStart && rangeEnd) {
        // Если есть диапазон, вызываем loadExpensesByPeriod
        //loadExpensesByPeriod(rangeStart, rangeEnd);
        const formatRangeStart = formatDate(new Date(rangeStart));
        const formatRangeEnd = formatDate(new Date(rangeEnd));
        
        dateRangePicker.setDate([formatRangeStart, formatRangeEnd], true); // Устанавливаем диапазон в календаре без вызова onChange
        setPeriodLabel(`${formatRangeStart} - ${formatRangeEnd}`);
        loadExpensesByPeriod(rangeStart, rangeEnd);
    } else if (period) {
        // Если указан период (например, "month"), используем его
        loadExpensesByDefaultPeriod(period);
        setPeriodLabel(getPeriodLabel(period));
    } else {
        // Если ничего не указано, загружаем по умолчанию за месяц
        loadExpensesByDefaultPeriod('month');
    }

    getLastError();
});

async function loadTinkoffExpenses() {
    showGlobalLoader();

    try {
        window.location.href = '/tinkoff/';
    } catch (error) {
        console.error("Ошибка при попытке входа в Тинькофф:", error);
        showErrorToast("Ошибка при попытке входа в Тинькофф");
    } finally {
        hideGlobalLoader();
    }
}

async function getLastError() {
    try {
        const response = await fetch('/tinkoff/expenses/last_error/');

        const error = await response.json();

        if (error.last_error) {
            showSessionExpiredModal(error.last_error);
            console.log(error.last_error)
        }
    } catch (error) {
        console.error("Ошибка при получении последней ошибки:", error);
    }
}

async function fetchCategories() {
    showGlobalLoader();
    
    try {
        const response = await fetch('/tinkoff/expenses/categories/');

        if (!response.ok) {
            hideGlobalLoader();
            const errorData = await response.json();

            if (response.status === 307) {
                showSessionExpiredModal(errorData.detail);
            }
            else {
                showErrorToast(errorData.detail);
                console.error('Ошибка загрузки категорий:', error);
            }
            return;
        }

        const categories = await response.json();

        console.log("Ответ сервера:", categories); // Выводим, чтобы проверить формат данных
        if (!Array.isArray(categories)) {
            throw new Error("Ответ не является массивом");
        }

        const categoryOptions = categories.map(category => ({
            id: category.id,
            text: category.category_name
        }));

        return categories.map(category => category.category_name);
    } catch (error) {
        console.error('Ошибка загрузки категорий:', error);
    } finally {
        hideGlobalLoader();
    }
}

// Сохранение ключевых слов
async function saveKeywords() {
    showGlobalLoader();
    const keywords = [];

    document.querySelectorAll('.category-select').forEach(select => {
        const categoryName = select.options[select.selectedIndex].textContent;
        const description = select.closest('tr').querySelector('td:nth-child(4)').textContent;

        // Исключаем записи с категорией "без категории"
        if (description) {
            keywords.push({ description, category_name: categoryName });
            console.log(description, categoryName);
        }
    });

    try {
        const response = await fetch('/tinkoff/expenses/keywords/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keywords })
        });

        if (!response.ok) {
            hideGlobalLoader();
            const errorData = await response.json();
            if (response.status === 307) {
                showSessionExpiredModal(errorData.detail);
            }
            else {
                showErrorToast(errorData.detail);
                console.error('Ошибка при сохранении ключевых слов:', errorData.detail);
            }
            return;
        }

        const data = await response.json();
        console.log(data.message);
        showNotificationToast(data.message);
        // Перезагрузка или обновление страницы, если нужно
    } catch (error) {
        console.error('Ошибка при сохранении ключевых слов:', error);
    } finally {
        hideGlobalLoader();
    }
}



