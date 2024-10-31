document.addEventListener("click", function (event) {
    const periodOptions = document.getElementById("periodOptions");
    const periodButton = document.getElementById("periodButton");
    if (periodOptions && !periodOptions.contains(event.target) && event.target !== periodButton) {
        periodOptions.style.display = 'none';
    }
});

flatpickr("#dateRange", {
    mode: "range",
    dateFormat: "d.m.Y",
    locale: "ru",
    maxDate: "today",
    onChange: function(selectedDates) {
        if (selectedDates.length === 2) {
            const startUnixDate = toUnixTimestamp(formatDate(selectedDates[0]) + " 00:00:00:000");
            const endUnixDate = toUnixTimestamp(formatDate(selectedDates[1]) + " 23:59:59:999");
            loadExpensesByPeriod(startUnixDate, endUnixDate);
            setPeriodLabel(`${formatDate(selectedDates[0])} - ${formatDate(selectedDates[1])}`);
        }
    }
});

function togglePeriodOptions() {
    const options = document.getElementById('periodOptions');
    options.style.display = options.style.display === 'block' ? 'none' : 'block';
}

function setPeriodLabel(label) {
    document.getElementById("periodButton").innerText = label;
}

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