document.addEventListener("DOMContentLoaded", function () {
    loadExpensesByDefaultPeriod('month')
});

// Инициализация Flatpickr с выбором периода и русским языком
flatpickr("#dateRange", {
    mode: "range",
    dateFormat: "d.m.Y",
    locale: "ru", // Устанавливаем русский язык
    maxDate: "today", // Ограничиваем выбор по текущий день
    onChange: function(selectedDates, dateStr, instance) {
        // Обработка выбранного периода
        if (selectedDates.length === 2) {
            const startUnixDate = toUnixTimestamp(formatDate(selectedDates[0]) + " 00:00:00:000");
            const endUnixDate = toUnixTimestamp(formatDate(selectedDates[1]) + " 23:59:59:999");
            loadExpensesByPeriod(startUnixDate, endUnixDate)
        }
    }
});

// Функция для форматирования даты в нужный вид
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
}

function toUnixTimestamp(dateString) {
    // Создаем объект Date из переданной строки даты и времени
    const date = new Date(dateString);

    // Проверяем корректность даты
    if (isNaN(date.getTime())) {
        throw new Error("Некорректная дата. Пожалуйста, используйте формат YYYY-MM-DD HH:mm:ss:msms.");
    }

    // Переводим в миллисекунды
    return date.getTime();
}

function getTodayDate() {
    const today = new Date();

    // Форматируем в YYYY-MM-DD
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0'); // Месяц с 0 по 11
    const day = String(today.getDate()).padStart(2, '0');

    const formattedDate = `${month}.${day}.${year}`;
    return formattedDate;
}

// Функция для показа опций периода
function showPeriodOptions() {
    document.getElementById('periodOptions').style.display = 'block';
}

// Устанавливаем период и делаем запрос
function setPeriod(period) {
    loadExpenses(period);
    document.getElementById('periodOptions').style.display = 'none';
}

function customDatePicker() {
    // Показываем календарь для выбора периода
    // Добавить календарь для выбора периода
}

function loadExpenses(data) {
    document.getElementById('totalExpenses').textContent = `Общая сумма расходов: ${data.total_expense} ₽`;
    document.getElementById('totalIncome').textContent = `Общая сумма доходов: ${data.total_income} ₽`;
    const tableBody = document.getElementById('expensesTable').querySelector('tbody');
    tableBody.innerHTML = '';
    data.expenses.forEach(expense => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${expense.date_time}</td>
            <td>${expense.card_number}</td>
            <td>${expense.transaction_type}</td>
            <td>${expense.amount} ₽</td>
            <td>${expense.description}</td>
            <td>
                <select onchange="handleCategorySelect(this)">
                    <option value="">Выберите категорию</option>
                </select>
            </td>
        `;
        tableBody.appendChild(row);
    });
    loadCategories();
}

// Загрузка расходов с сервера с учетом выбранного периода
function loadExpensesByDefaultPeriod(period = 'month') {
    fetch(`http://127.0.0.1:8000/tinkoff/expenses/?period=${period}`)
        .then(response => response.json())
        .then(data => loadExpenses(data))
        .catch(error => console.error('Ошибка при загрузке расходов:', error));
}

// Загрузка расходов с сервера с учетом выбранного периода
function loadDayExpenses() {
    const todayDate = getTodayDate();
    loadExpensesByPeriod(toUnixTimestamp(todayDate + " 00:00:00:000"), toUnixTimestamp(todayDate + " 23:59:59:999"));
}

function loadExpensesByPeriod(startUnixDate, endUnixDate) {
    fetch(`http://127.0.0.1:8000/tinkoff/expenses/?rangeStart=${startUnixDate}&rangeEnd=${endUnixDate}`)
        .then(response => response.json())
        .then(data => loadExpenses(data))
        .catch(error => console.error('Ошибка при загрузке расходов:', error));
}

// Добавляем категории в список
function loadCategories() {
    fetch('http://127.0.0.1:8000/tinkoff/expenses/categories/')
        .then(response => response.json())
        .then(categories => {
            const selects = document.querySelectorAll('select');
            selects.forEach(select => {
                select.innerHTML = '';
                categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = category.category_name;
                    select.appendChild(option);
                });
                const addOption = document.createElement('option');
                addOption.value = "add";
                addOption.textContent = "Добавить категорию";
                select.appendChild(addOption);
            });
        })
        .catch(error => console.error('Ошибка при загрузке категорий:', error));
}

// Обработчик выбора категории
function handleCategorySelect(selectElement) {
    if (selectElement.value === "add") {
        document.getElementById("addCategorySection").style.display = "block";
    }
}

// Обработка формы добавления категории
document.getElementById("addCategoryForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const categoryName = document.getElementById("categoryName").value;
    const keywords = document.getElementById("keywords").value.split(',').map(word => word.trim());
    await fetch("http://127.0.0.1:8000/tinkoff/expenses/categories/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category_name: categoryName, keywords })
    });
    loadCategories();
    document.getElementById("addCategorySection").style.display = "none";
    document.getElementById("addCategoryForm").reset();
});