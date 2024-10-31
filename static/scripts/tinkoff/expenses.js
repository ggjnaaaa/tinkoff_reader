// Код jQuery для настройки столбцов с изменяемой шириной
$(document).ready(function () {
    $('#expensesTable').resizableColumns();
});

// Вызов отображения расходов за месяц
document.addEventListener("DOMContentLoaded", function () {
    loadExpensesByDefaultPeriod('month');
});

// Общая функция для обработки возвращенной таблицы расходов с бэка
function loadExpenses(data) {
    $('#totalExpenses').text(`Общая сумма расходов: ${data.total_expense} ₽`);
    $('#totalIncome').text(`Общая сумма доходов: ${data.total_income} ₽`);

    const tableBody = $('#expensesTable tbody');
    tableBody.empty();

    data.expenses.forEach(expense => {
        const row = $(`
            <tr>
                <td>${expense.date_time}</td>
                <td>${expense.card_number}</td>
                <td>${expense.transaction_type}</td>
                <td>${expense.amount} ₽</td>
                <td>${expense.description}</td>
                <td>
                    <select class="category-select" data-description="${expense.description}">
                        <option>${expense.category || 'Выберите категорию'}</option>
                    </select>
                </td>
            </tr>
        `);
        tableBody.append(row);
    });

    // Применяем Select2
    $('.category-select').select2({
        placeholder: "Выберите категорию",
        allowClear: true
    });

    fetchCategories()
}

// Обработчик клика по значку удаления с делегированием
$(document).on('click', '.delete-icon', function () {
    const categoryId = $(this).data('id');
    const categoryName = $(this).data('name');
    deleteCategory(categoryId, categoryName); // Вызываем функцию удаления
});

// Загрузка расходов с сервера с учетом выбранного дефолтного периода
function loadExpensesByDefaultPeriod(period = 'month') {
    fetch(`http://127.0.0.1:8000/tinkoff/expenses/?period=${period}`)
        .then(response => response.json())
        .then(data => loadExpenses(data))
        .catch(error => console.error('Ошибка при загрузке расходов:', error));
}

// Загрузка расходов с сервера за сегодня
function loadDayExpenses() {
    const todayDate = getTodayDate();
    loadExpensesByPeriod(toUnixTimestamp(todayDate + " 00:00:00:000"), toUnixTimestamp(todayDate + " 23:59:59:999"));
}

// Загрузка расходов с сервера за период
function loadExpensesByPeriod(startUnixDate, endUnixDate) {
    fetch(`http://127.0.0.1:8000/tinkoff/expenses/?rangeStart=${startUnixDate}&rangeEnd=${endUnixDate}`)
        .then(response => response.json())
        .then(data => loadExpenses(data))
        .catch(error => console.error('Ошибка при загрузке расходов:', error));
}

function fetchCategories() {
    fetch('/tinkoff/expenses/categories/')
        .then(response => response.json())
        .then(categories => {
            console.log("Ответ сервера:", categories); // Выводим, чтобы проверить формат данных
            if (!Array.isArray(categories)) {
                throw new Error("Ответ не является массивом");
            }

            const categoryOptions = categories.map(category => ({
                id: category.id,
                text: category.category_name
            }));

            $('.category-select').select2({
                data: categoryOptions,
                placeholder: "Выберите категорию",
                allowClear: true
            });
        })
        .catch(error => console.error('Ошибка загрузки категорий:', error));
}

// Обработчик выбора категории
function handleCategorySelect(selectElement) {
    if (selectElement.value === "add") {
        document.getElementById("addCategorySection").style.display = "block";
    }   
}
