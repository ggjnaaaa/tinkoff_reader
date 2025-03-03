// Код jQuery для настройки столбцов с изменяемой шириной
$(window).on('load', function() {
    $('#expensesTable').resizableColumns();
    
    $('#itemsPerPageSelect').select2({
        width: 'auto',  // Подгонка под размер текста
        minimumResultsForSearch: Infinity  // Убираем поле поиска
    });
});

window.isMiniApp = document.getElementById("app").dataset.miniapp === "true";

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
        const dateRangeStart = new Date(rangeStart);
        const dateRangeEnd = new Date(rangeEnd);

        const formatRangeStart = formatFullDate(dateRangeStart);
        const formatRangeEnd = formatFullDate(dateRangeEnd);
        
        if (document.getElementById("dateRange"))
            dateRangePicker.setDate([formatRangeStart, formatRangeEnd], true);
        setPeriodLabel([dateRangeStart, dateRangeEnd]);
    } else if (period) {
        setPeriodLabelByDefault(getPeriodLabel(period));
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
        if (isMiniApp) {
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
        const token = getToken();
        const endpoint = token ? `/tinkoff/expenses/keywords/?token=${token}` : '/tinkoff/expenses/keywords/';
        const response = await fetch(endpoint, {
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
    } catch (error) {
        console.error('Ошибка при сохранении ключевых слов:', error);
    } finally {
        hideGlobalLoader();
    }
}


function toggleMenu() {
    const menu = document.getElementById('sideMenu');
    const burger = document.querySelector('.menu-toggle');
    const overlay = document.getElementById('overlay');
    
    // Переключаем класс "active" для меню и оверлея
    menu.classList.toggle('active');
    overlay.classList.toggle('active');

    // Прячем/показываем кнопку-бургер
    burger.classList.toggle('hidden');
}

function closeMenu() {
    const menu = document.getElementById('sideMenu');
    const burger = document.querySelector('.menu-toggle');
    const overlay = document.getElementById('overlay');

    menu.classList.remove('active');
    overlay.classList.remove('active');
    burger.classList.remove('hidden');
}

// Закрыть меню при нажатии вне области меню
document.getElementById('overlay').addEventListener('click', closeMenu);

function loginToTinkoff() {
    window.location.href = '/tinkoff/';
}

function resetTinkoffSession() {
    fetch('/tinkoff/reset_session/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotificationToast(data.message);
        } else {
            showErrorToast(`Ошибка: ${data.message}`);
        }
    })
    .catch(error => {
        alert(`Произошла ошибка: ${error}`);
    });
}

function saveSchedule() {
    const scheduler1 = document.getElementById('scheduler1').value;
    const scheduler2 = document.getElementById('scheduler2').value;

    const scheduleData = {
        expenses: scheduler1,  // первая автовыгрузка
        full: scheduler2       // вторая автовыгрузка
    };

    fetch('/tinkoff/schedular/', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(scheduleData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotificationToast(data.message);
        } else {
            showErrorToast(`Ошибка: ${data.message}`);
        }
    })
    .catch((error) => {
        console.log(error)
    });
}

function saveCache() {
    fetch('/tinkoff/save_session/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotificationToast(data.message);
        } else {
            showErrorToast(`Ошибка: ${data.message}`);
        }
    })
    .catch((error) => {
        console.log(error)
    });
}