// Открытие и закрытие модальных окон
function openModal(modalId) {
    document.getElementById(modalId).style.display = "block";
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = "none";
}

// Добавление нового поля для ввода категории
function addCategoryInput() {
    const newInput = document.createElement('input');
    newInput.type = 'text';
    newInput.className = 'category-input';
    newInput.placeholder = 'Название новой статьи';
    document.getElementById('categoryInputs').appendChild(newInput);
}

// Сохранение новых категорий на сервере
function submitNewCategories() {
    const categoryInputs = document.querySelectorAll('.category-input');
    const categories = Array.from(categoryInputs).map(input => input.value).filter(Boolean);

    fetch('/tinkoff/expenses/categories/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ categories })
    })
    .then(() => {
        closeModal('addCategoryModal');
        fetchCategories(); // Перезагрузить категории после добавления
    })
    .catch(error => console.error('Ошибка при добавлении категории:', error));
}

// Загрузка списка категорий для удаления с чекбоксами
function loadDeleteCategoryList() {
    fetch('/tinkoff/expenses/categories/')
        .then(response => response.json())
        .then(categories => {
            const deleteList = document.getElementById('deleteCategoryList');
            deleteList.innerHTML = ''; // Очищаем список перед добавлением

            categories.forEach(category => {
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.value = category.id;
                checkbox.id = `category-${category.id}`;

                const label = document.createElement('label');
                label.htmlFor = `category-${category.id}`;
                label.textContent = category.category_name;

                const div = document.createElement('div');
                div.appendChild(checkbox);
                div.appendChild(label);

                deleteList.appendChild(div);
            });
        })
        .catch(error => console.error('Ошибка загрузки категорий:', error));
}

// Удаление выбранных категорий
function confirmDeleteCategories() {
    const checkboxes = document.querySelectorAll('#deleteCategoryList input[type="checkbox"]:checked');
    const categoryIds = Array.from(checkboxes).map(checkbox => checkbox.value);

    Promise.all(categoryIds.map(id => fetch(`/tinkoff/expenses/categories/${id}`, { method: 'DELETE' })))
        .then(() => {
            closeModal('deleteCategoryModal');
            fetchCategories(); // Перезагрузить категории после удаления
        })
        .catch(error => console.error('Ошибка при удалении категорий:', error));
}

// Сохранение ключевых слов
function saveKeywords() {
    const keywords = []; // Массив для хранения ключевых слов и связанных id статей

    // Собираем значения ключевых слов и id категории для отправки
    document.querySelectorAll('.keyword-input').forEach(input => {
        const categoryId = input.getAttribute('data-category-id'); // Получаем id категории
        const description = input.value;

        if (description && categoryId) {
            keywords.push({ description, category_id: parseInt(categoryId) });
        }
    });

    fetch('/tinkoff/expenses/keywords/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keywords })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
        // Перезагрузка или обновление страницы, если нужно
    })
    .catch(error => console.error('Ошибка при сохранении ключевых слов:', error));
}

// Обработчик открытия модального окна удаления
document.querySelector('button[onclick="openModal(\'deleteCategoryModal\')"]').addEventListener('click', loadDeleteCategoryList);