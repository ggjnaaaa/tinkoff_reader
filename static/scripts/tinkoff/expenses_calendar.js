document.addEventListener("click", function (event) {
    if (!isMiniApp) {
        const periodOptions = document.getElementById("periodOptions");
        const periodButton = document.getElementById("periodButton");
        if (periodOptions && !periodOptions.contains(event.target) && event.target !== periodButton) {
            periodOptions.style.display = 'none';
        }
    } 
});

const dateRangePicker = isMiniApp ? null : flatpickr("#dateRange", {
    mode: "range",
    dateFormat: "d.m.Y",
    locale: "ru",
    maxDate: "today",
    onChange: function(selectedDates) {
        if (!isInitialLoad && selectedDates.length === 2) {
            const startDate = selectedDates[0];
            const endDate = selectedDates[1];

            // Форматируем даты в строку "YYYY-MM-DD" без изменения временной зоны
            const startDateString = startDate.getFullYear() + '-' +
                                    String(startDate.getMonth() + 1).padStart(2, '0') + '-' +
                                    String(startDate.getDate()).padStart(2, '0');
            const endDateString = endDate.getFullYear() + '-' +
                                  String(endDate.getMonth() + 1).padStart(2, '0') + '-' +
                                  String(endDate.getDate()).padStart(2, '0');

            loadExpensesByPeriod(startDateString, endDateString);
            setPeriodLabel(selectedDates);
        }
    }
});

function togglePeriodOptions() {
    const options = document.getElementById('periodOptions');
    options.style.display = options.style.display === 'block' ? 'none' : 'block';

    // Закрыть список после выбора
    options.addEventListener('change', () => {
        options.style.display = options.style.display === 'block' ? 'none' : 'block';
    });
}

function setPeriodLabel(dates) {
    if (isMiniApp)
        document.getElementById("date").innerText = formatMiniDate(dates[0]);
    else
        document.getElementById("periodButton").innerText = `${formatFullDate(dates[0])} - ${formatFullDate(dates[1])}`;
}

function setPeriodLabelByDefault(period) {
    if (isMiniApp)
        document.getElementById("date").innerText = period;
    else
        document.getElementById("periodButton").innerText = period;
}

// Функция для форматирования даты в нужный вид
function formatFullDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${day}.${month}.${year}`;
}

function formatMiniDate(date) {    
    return new Intl.DateTimeFormat('ru-RU', {
                                day: '2-digit', // Двузначный день
                                month: 'long',  // Полное название месяца
                            }).format(date);
}

function getTodayDate() {
    const today = new Date();

    // Форматируем в YYYY-MM-DD
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0'); // Месяц с 0 по 11
    const day = String(today.getDate()).padStart(2, '0');

    const formattedDate = `${year}-${month}-${day}`;
    return formattedDate;
}

// Функция для получения метки периода
function getPeriodLabel(period) {
    switch (period) {
        case 'day': return 'Сегодня';
        case 'week': return 'Текущая неделя';
        case 'month': return 'Этот месяц';
        case '3month': return '3 месяца';
        case 'year': return 'Этот год';
        default: return 'Этот месяц';
    }
}

// Функция для очистки даты
function clearDateRange() {
    if (dateRangePicker)
        dateRangePicker.clear();
}