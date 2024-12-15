// Код jQuery для настройки столбцов с изменяемой шириной
$(window).on('load', function() {
    $('#expensesTable').resizableColumns();
    
    $('#itemsPerPageSelect').select2({
        width: 'auto',  // Подгонка под размер текста
        minimumResultsForSearch: Infinity  // Убираем поле поиска
    });
});

// Вызов отображения расходов за месяц
document.addEventListener("DOMContentLoaded", async function () {
    showGlobalLoader();

    const urlParams = new URLSearchParams(window.location.search);
    const period = urlParams.get("period");
    const rangeStart = urlParams.get("rangeStart");
    const rangeEnd = urlParams.get("rangeEnd");
    const source = urlParams.get("source");

    if (source) {
        const radioButton = document.querySelector(`input[name="dataSource"][value="${source}"]`);
        if (radioButton) {
            radioButton.checked = true;
            setDataSource(source);
        }
    }

    if (rangeStart && rangeEnd) {
        // Если есть диапазон, вызываем loadExpensesByPeriod
        const formatRangeStart = formatDate(new Date(rangeStart));
        const formatRangeEnd = formatDate(new Date(rangeEnd));
        
        dateRangePicker.setDate([formatRangeStart, formatRangeEnd], true);
        setPeriodLabel(`${formatRangeStart} - ${formatRangeEnd}`);
    } else if (period) {
        setPeriodLabel(getPeriodLabel(period));
    } else {
        loadExpensesByDefaultPeriod('month');
    }

    const errorElement = document.querySelector('#error-message');
    if (errorElement) {
        const errorMessage = errorElement.textContent.trim();
        if (errorMessage) {
            showErrorToast(errorMessage);
        }
    }

    const expensesElement = document.querySelector('#expenses');
    if (expensesElement) {
        const textContent = expensesElement.textContent.trim();
        if (textContent) {
            try {
                const expensesData = JSON.parse(textContent);
                loadExpenses(expensesData);
            } catch (error) {
                console.error("Ошибка при разборе JSON:", error);
            }
        } else {
            console.warn("Элемент #expenses пуст.");
        }
    } else {
        console.warn("Элемент #expenses не найден.");
    }
    
    const redirectUrlElement = document.querySelector('#redirect_url');
    if (redirectUrlElement) {
        const textContent = redirectUrlElement.textContent.trim();
        if (textContent) {
            window.location.href = textContent;
            return;
        }
    }
    
    hideGlobalLoader();
    getLastError();
});

let currentDataSource = 'db'; // По умолчанию из базы

function setDataSource(source) {
    currentDataSource = source;
    showNotificationToast(`Источник данных: ${source === 'db' ? 'База данных' : 'Тинькофф'}`);
}

async function getLastError() {
    try {
        const response = await fetch('/tinkoff/expenses/last_error/');

        const error = await response.json();

        if (error.last_error) {
            showSessionExpiredModal(error.last_error);
            console.error(error.last_error)
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
        let description = null;
        if (is_for_one_card) {
            description = select.closest('tr').querySelector('td:nth-child(2)').textContent;
        } else {
            description = select.closest('tr').querySelector('td:nth-child(4)').textContent;
        }

        // Исключаем записи с категорией "без категории"
        if (description && !keywords.some(keyword => keyword.description === description && keyword.category_name === categoryName)) {
            keywords.push({ description, category_name: categoryName });
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
        showNotificationToast(data.message);
        // Перезагрузка или обновление страницы, если нужно
    } catch (error) {
        console.error('Ошибка при сохранении ключевых слов:', error);
    } finally {
        hideGlobalLoader();
    }
}



