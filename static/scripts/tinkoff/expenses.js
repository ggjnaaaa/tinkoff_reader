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

// Загрузка расходов с сервера с учетом выбранного периода
function loadExpenses(period = 'month') {
    fetch(`http://127.0.0.1:8000/tinkoff/expenses/?period=${period}`)
        .then(response => response.json())
        .then(data => {
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
        })
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