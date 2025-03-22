class ExpenseManager {
    constructor(expenses, categories, isMiniApp) {
        if (!expenses) throw new Error("Расходы не должны быть пустыми!");
        this.originalExpenses = expenses;
        this.filteredExpenses = [...expenses];
        this.categories = categories;
        this.isMiniApp = isMiniApp;

        // Журнал изменений
        this.changesJournal = {};

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
        this.applyChangesToExpenses();
        const tableBody = $('#expensesTable tbody');
        tableBody.empty();
    
        const startIndex = this.isMiniApp ? 0 : (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = this.isMiniApp ? this.filteredExpenses.length : startIndex + this.itemsPerPage;
        const expensesToRender = this.filteredExpenses.slice(startIndex, endIndex);

        expensesToRender.forEach(expense => {
            let row;
            const selectedCategory = this.categories.find(cat => cat.category_name === expense.category);
            const categoryColor = selectedCategory ? selectedCategory.color : 'transparent'; 
            const categoryId = selectedCategory ? selectedCategory.id : null; 

            if (this.isMiniApp) {
                row = $(`<tr>
                            <td>${expense.amount} ₽</td>
                            <td>${expense.description}</td>
                            <td>
                                <div class="custom-select" data-id="${expense.id}">
                                    <div class="selected">
                                        <div style="background-color: ${categoryColor}" data-category-id="${categoryId}" class="category-text circle-selection">${expense.category}</div>
                                        <div class="icons">
                                            <div class="close-icon">
                                                <svg xmlns="http://www.w3.org/2000/svg" width="9" height="9" viewBox="0 0 100 100">
                                                    <path d="M10 10L90 90M90 10L10 90" stroke="black" stroke-width="20"/>
                                                </svg>
                                            </div>
                                            <div class="dropdown-icon">▼</div>
                                        </div>
                                    </div>
                                </div>
                            </td>
                        </tr>`);
            }
            else {
                row = $(`<tr>
                            <td>${expense.date_time}</td>
                            <td>${expense.card_number}</td>
                            <td>${expense.amount} ₽</td>
                            <td>${expense.description}</td>
                            <td>
                                <div class="custom-select" data-id="${expense.id}">
                                    <div class="selected">
                                        <div style="background-color: ${categoryColor}" data-category-id="${categoryId}" class="category-text circle-selection">${expense.category}</div>
                                        <div class="icons">
                                            <div class="close-icon">
                                                <svg xmlns="http://www.w3.org/2000/svg" width="9" height="9" viewBox="0 0 100 100">
                                                    <path d="M10 10L90 90M90 10L10 90" stroke="black" stroke-width="20"/>
                                                </svg>
                                            </div>
                                            <div class="dropdown-icon">▼</div>
                                        </div>
                                    </div>
                                </div>
                            </td>
                        </tr>`);
            }

            row.find('.custom-select').click((e) => {
                const target = $(e.target).closest('.custom-select');
                const existingWrapper = $('.select-wrapper');

                if (existingWrapper.length && existingWrapper.is(':visible')) {
                    existingWrapper.remove();
                    return;
                }
                this.showDropdown(target);
            });

            row.find('.close-icon').click(() => {
                this.clickCategoryReset(row);
            });
            
            tableBody.append(row);
        });
 
        // Отображаем общую сумму
        const totalExpense = this.calculateTotalExpense();
        $('#totalExpenses').text(`Общая сумма расходов: ${totalExpense} ₽`);

        this.renderPaginationControls();
    }

    showDropdown(target) {
        // Удаляем старый dropdown
        $('.custom-dropdown').remove();
    
        // Создаём новый dropdown
        const wrapper = $('<div class="select-wrapper"></div>');
        const dropdown = $('<div class="custom-dropdown"></div>');
        this.categories.forEach(category => {
            const option = $(`<div>
                                <div class="circle-selection" style="background-color: ${category.color || 'transparent'}">
                                    ${category.category_name}
                                </div>
                            </div>`);
            option.click(() => {
                if (this.isMiniApp) {
                    $('#footer-save').show();
                }
    
                // Обновляем текст и ID в элементе .category-text
                const selectedCategory = target.find('.category-text');
                const expenseId = target.attr('data-id'); // Получаем ID расхода
                const previousCategoryId = selectedCategory.attr('data-category-id');

                // Получаем исходную категорию из originalExpenses
                const originalExpense = this.originalExpenses.find(expense => expense.id == expenseId);
                const originalCategoryId = originalExpense ? originalExpense.id : null;

                if (category.id == originalCategoryId) {
                    delete this.changesJournal[expenseId]; // Удаляем изменение, если оно вернулось к исходному
                } 
                else if (previousCategoryId != category.id) {
                    // Обновляем журнал изменений
                    this.changesJournal[expenseId] = {
                        category_id: category.id.toString(),
                        category_name: category.category_name
                    };
                }

                selectedCategory.text(category.category_name);
                selectedCategory.attr('data-category-id', category.id);
                const circleSelection = target.find('.circle-selection');
                circleSelection.css('background-color', category.color || 'transparent');

                // Закрываем dropdown
                wrapper.remove();

            });
            dropdown.append(option);
        });

        wrapper.append(dropdown);
    
        // Добавляем dropdown в конец body
        $('body').append(wrapper);
    
        // Вычисляем координаты
        const offset = $(target).offset();
        const targetHeight = $(target).outerHeight();
        const dropdownHeight = dropdown.outerHeight();
        const windowHeight = $(window).height();
        const scrollTop = $(window).scrollTop(); // Получаем текущую прокрутку страницы
        
        // Вычисляем нижний угол элемента с учетом прокрутки
        const elementBottomPosition = offset.top + targetHeight - scrollTop;

        // Вычисляем доступное место ниже и выше
        const availableSpaceBelow = windowHeight - elementBottomPosition; // Место под элементом
        const availableSpaceAbove = offset.top - scrollTop; // Место выше, до верхней границы окна

        // Определяем высоту dropdown: если места достаточно, то по высоте контента, иначе ограничиваем до доступного места
        let dropdownMaxHeight = dropdownHeight; 

        if (availableSpaceBelow < 100) {
            // Если снизу мало места и сверху достаточно, показываем вверх
            let dropdownTopPosition = offset.top - scrollTop - dropdownHeight;
            if (dropdownTopPosition < 0) dropdownTopPosition = 0;

            if (availableSpaceAbove < dropdownHeight) {
                dropdownMaxHeight = availableSpaceAbove; // Ограничиваем до доступного места снизу
            }
            dropdown.css('max-height', dropdownMaxHeight);

            wrapper.css({
                position: 'fixed',
                top: dropdownTopPosition, // Показываем dropdown либо вниз, либо вверх
                left: offset.left,
                minWidth: $(target).outerWidth(),
                // height: dropdownHeight
            });
        }
        else {
            let dropdownTopPosition = offset.top - scrollTop + targetHeight; // по умолчанию вниз

            if (availableSpaceBelow < dropdownHeight) {
                dropdownMaxHeight = availableSpaceBelow - 10; // Ограничиваем до доступного места снизу
            }
            dropdown.css('max-height', dropdownMaxHeight);

            wrapper.css({
                position: 'fixed',
                top: dropdownTopPosition, // Показываем dropdown либо вниз, либо вверх
                left: offset.left,
                minWidth: $(target).outerWidth(),
            });
        }

        // Закрытие при клике вне (с задержкой)
        setTimeout(() => {
            $(document).on('click.hideDropdown', (e) => {
                if (!wrapper.is(e.target) && wrapper.has(e.target).length === 0) {
                    wrapper.remove();
                    $(document).off('click.hideDropdown');
                }
            });
        }, 0);
    }

    // Применяем изменения из журнала к данным
    applyChangesToExpenses() {
        this.filteredExpenses = this.filteredExpenses.map(expense => {
            if (this.changesJournal[expense.id]) {
                return {
                    ...expense,
                    category: this.changesJournal[expense.id].category_name,
                };
            }
            return expense;
        });
    }

    clickCategoryReset(row) {
        if (this.isMiniApp) {
            $('#footer-save').show();
        }
        
        const categoryTextElement = row.find('.category-text');
        const expenseId = row.find('.custom-select').attr('data-id'); // Получаем ID расхода
    
        // Получаем исходную категорию из originalExpenses
        const originalExpense = this.originalExpenses.find(expense => expense.id.toString() == expenseId);
        const originalCategoryId = originalExpense ? originalExpense.id : null;
    
        // Если исходная категория уже "Не указана", удаляем запись из журнала
        if (originalCategoryId == null) {
            delete this.changesJournal[expenseId]; // Удаляем изменение, если оно совпадает с исходным
        } else {
            // Иначе добавляем изменение в журнал
            this.changesJournal[expenseId] = {
                category_id: null,
                category_name: 'Не указана',
            };
        }
    
        // Очищаем текст и меняем на "Не указана"
        categoryTextElement.text('Не указана');
        categoryTextElement.attr('data-category-id', null);
    
        // Также можем изменить цвет на прозрачный
        categoryTextElement.css('background-color', 'transparent');
    }

    clearChanges() {
        // Применяем изменения из журнала к оригинальным расходам
        for (const expenseId in this.changesJournal) {
            const change = this.changesJournal[expenseId];
            const originalExpense = this.originalExpenses.find(expense => expense.id.toString() === expenseId);
            if (originalExpense) {
                originalExpense.category = change.category_name;
            }
        }

        // Очищаем журнал изменений
        this.changesJournal = [];
    }
    
}

// Добавляем обработчики на элементы управления
$(document).ready(function() {
    $('#itemsPerPageSelect').on('change', function() {
        const itemsPerPage = parseInt($(this).val());
        expenseManager.setItemsPerPage(itemsPerPage);
    });
});