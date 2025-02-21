class ExpenseManager {
    constructor(expenses, categories, isMiniApp) {
        if (!expenses) throw new Error("Расходы не должны быть пустыми!");
        this.originalExpenses = expenses;
        this.filteredExpenses = [...expenses];
        this.categories = categories;
        this.isMiniApp = isMiniApp;

        // Параметры пагинации
        this.currentPage = 1;
        if (!isMiniApp)
            this.itemsPerPage = parseInt(localStorage.getItem("itemsPerPage")) || 10; // Загружаем itemsPerPage из локального хранилища или ставим 10

        this.render();
    }

    // Метод для фильтрации по карте
    filterByCard(card) {
        this.filteredExpenses = this.originalExpenses.filter(expense => expense.card_number === card);
        this.currentPage = 1; // Сбрасываем на первую страницу
        this.render();
    }

    // Метод для сброса фильтра
    resetFilter() {
        this.filteredExpenses = [...this.originalExpenses];
        this.render();
    }

    // Метод для обновления категории статьи
    updateCategory(description, category) {
        // Обновляем категорию в оригинальном списке расходов
        this.originalExpenses.forEach(expense => {
            if (expense.description === description) {
                expense.category = category;
            }
        });
    
        this.filteredExpenses.forEach(expense => {
            if (expense.description === description) {
                expense.category = category;
            }
        });
    
        // Найдем строку таблицы по описанию и обновим только ее
        const row = $(`#expensesTable .category-select[data-description="${description}"]`).closest('tr');
        const select = row.find('.category-select');
    
        // Обновим `<select>` и его значение без полного рендеринга
        select.val(category).trigger('change.select2');
    }

    calculateTotalExpense() {
        const total = this.filteredExpenses.reduce((total, expense) => {
            return total + parseFloat(expense.amount); // Преобразуем строку в число
        }, 0);
    
        return total.toFixed(2); // Округляем до двух знаков
    }

    setItemsPerPage(count) {
        this.itemsPerPage = count;
        localStorage.setItem("itemsPerPage", count); // Сохраняем значение в локальное хранилище
        this.currentPage = 1; // Переходим на первую страницу
        this.render();
    }

    goToPage(page) {
        if (page > 0 && page <= this.totalPages()) {
            this.currentPage = page;
            this.render();
        }
    }

    nextPage() {
        if (this.currentPage < this.totalPages()) {
            this.currentPage++;
            this.render();
        }
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.render();
        }
    }

    totalPages() {
        return Math.ceil(this.filteredExpenses.length / this.itemsPerPage);
    }

    renderPaginationControls() {
        if (this.isMiniApp) return;

        const paginationContainer = $('#paginationControls');
        paginationContainer.empty();

        paginationContainer.append(`
            <button onclick="expenseManager.previousPage()" ${this.currentPage === 1 ? 'disabled' : ''} class="previous-button">
                <svg width="15" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M15 6L9 12L15 18" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
            
            <span id="paginationLabel">Страница 
                <input type="number" id="pageInput" min="1" max="${this.totalPages()}" value="${this.currentPage}" 
                    onchange="expenseManager.goToPage(parseInt(this.value))" style="width: 40px; text-align: center;">
                из ${this.totalPages()}
            </span>
            
            <button onclick="expenseManager.nextPage()" ${this.currentPage === this.totalPages() ? 'disabled' : ''} class="next-button">
                <svg width="15" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 6L15 12L9 18" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
        `);

        $('#itemsPerPageSelect').val(this.itemsPerPage);
    }

    // Отображение данных в таблице
    render() {
        const tableBody = $('#expensesTable tbody');
        tableBody.empty();
    
        const startIndex = this.isMiniApp ? 0 : (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = this.isMiniApp ? this.filteredExpenses.length : startIndex + this.itemsPerPage;
        const expensesToRender = this.filteredExpenses.slice(startIndex, endIndex);

        expensesToRender.forEach(expense => {
            const options = this.categories.map(cat => {
                const selected = expense.category === cat ? 'selected' : '';
                return `<option value="${cat}" ${selected}>${cat}</option>`;
            }).join('');

            let row;
            if (this.isMiniApp) {
                row = `<tr>
                            <td>${expense.amount} ₽</td>
                            <td>${expense.description}</td>
                            <td>
                                <select class="category-select" 
                                        data-description="${expense.description}">
                                    <option></option> <!-- Пустая опция для "без категории" -->
                                    ${options}
                                </select>
                            </td>
                        </tr>`;
            }
            else {
                row = `<tr>
                            <td>${expense.date_time}</td>
                            <td>${expense.card_number}</td>
                            <td>${expense.amount} ₽</td>
                            <td>${expense.description}</td>
                            <td>
                                <select class="category-select" 
                                        data-description="${expense.description}">
                                    <option></option> <!-- Пустая опция для "без категории" -->
                                    ${options}
                                </select>
                            </td>
                        </tr>`;
            }
            
            tableBody.append(row);
        });
    
        $('.category-select').select2({
            placeholder: "Выберите категорию",
            allowClear: true 
        });
    
        // Отображаем общую сумму
        const totalExpense = this.calculateTotalExpense();
        $('#totalExpenses').text(`Общая сумма расходов: ${totalExpense} ₽`);

        this.renderPaginationControls();
    
        // Переназначение обработчика для обновления категории
        this.attachCategoryChangeEvent();
    }

    // Привязка события к изменению категории
    attachCategoryChangeEvent() {
        $('#expensesTable').on('change', '.category-select', (event) => {
            const selectedCategory = $(event.target).val();
            const description = $(event.target).data('description');
            this.updateCategory(description, selectedCategory);

            if (this.isMiniApp) {
                $('#footer-save').show();
            }
        });
    }
}

// Добавляем обработчики на элементы управления
$(document).ready(function() {
    $('#itemsPerPageSelect').on('change', function() {
        const itemsPerPage = parseInt($(this).val());
        expenseManager.setItemsPerPage(itemsPerPage);
    });
});