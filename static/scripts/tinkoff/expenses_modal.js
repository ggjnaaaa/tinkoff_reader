// Функция для открытия модального окна
function openModal(modalId) {
    document.getElementById(modalId).style.display = "block";
}

// Функция для закрытия модального окна
function closeModal(modalId) {
    document.getElementById(modalId).style.display = "none";
}

// Модальное окно для удаления категории
let categoryToDelete = null;
function deleteCategory(categoryId, categoryName) {
    alert("LNLIJBL")
    categoryToDelete = categoryId;
    document.getElementById('deleteCategoryText').textContent = `Удалить статью "${categoryName}"?`;
    openModal('deleteCategoryModal');
}

function confirmDeleteCategory() {
    if (categoryToDelete) {
        fetch(`/tinkoff/expenses/categories/${categoryToDelete}`, { method: 'DELETE' })
            .then(() => {
                closeModal('deleteCategoryModal');
                fetchCategories(); // Перезагрузить категории
            })
            .catch(error => console.error('Ошибка при удалении категории:', error));
    }
}

// Модальное окно для добавления категории
function addNewCategory() {
    openModal('addCategoryModal');
}

function submitNewCategory() {
    const newCategoryName = document.getElementById('newCategoryInput').value;
    fetch('/tinkoff/expenses/categories/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category_name: newCategoryName })
    })
    .then(() => {
        closeModal('addCategoryModal');
        fetchCategories();
    })
    .catch(error => console.error('Ошибка при добавлении категории:', error));
}