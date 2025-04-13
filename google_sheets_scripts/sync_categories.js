// Конфигурация
const INACTIVITY_DELAY = 3 * 60 * 1000; // 3 минуты в миллисекундах
const CACHE_KEY = "last_edit_time";
const HIDDEN_SHEET_NAME = "HiddenChanges";

// Накопление изменений + запуск таймера
function onEdit(e) {
  const range = e.range;
  const sheet = range.getSheet();
  if (range.getColumn() !== 6) return;

  const row = range.getRow();
  const idCell = sheet.getRange(row, 9); // Столбец I
  const idValue = idCell.getValue();
  if (!idValue || !Number.isInteger(Number(idValue))) {
    console.log(`ID ${idValue} на строке ${row} отсутсвует либо не является числом.`);
    return;
  }

  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const hiddenSheet = spreadsheet.getSheetByName(HIDDEN_SHEET_NAME) || createHiddenSheet(spreadsheet);
  const scriptLock = LockService.getScriptLock();

  try {
    scriptLock.waitLock(5000);

    const newChange = {
      sheet: sheet.getName(),
      cell: range.getA1Notation(),
      oldValue: e.oldValue || "",
      newValue: e.value || "",
      id: idValue,
      timestamp: new Date().toISOString()
    };

    const data = hiddenSheet.getDataRange().getValues(); // Получаем все данные на скрытом листе
    let existingChangeIndex = -1;

    // Ищем существующее изменение
    for (let i = 0; i < data.length; i++) {
      if (data[i][0] === newChange.sheet && data[i][1] === newChange.cell && data[i][4] === newChange.id) {
        existingChangeIndex = i;
        break;
      }
    }

    if (existingChangeIndex !== -1) {
      hiddenSheet.getRange(existingChangeIndex + 1, 1, 1, 6).setValues([[newChange.sheet, newChange.cell, newChange.oldValue, newChange.newValue, newChange.id, newChange.timestamp]]);
    } else {
      hiddenSheet.appendRow([newChange.sheet, newChange.cell, newChange.oldValue, newChange.newValue, newChange.id, newChange.timestamp]);
    }

    const cache = CacheService.getScriptCache();
    cache.put(CACHE_KEY, Date.now().toString(), INACTIVITY_DELAY / 1000);
  } catch (err) {
    console.error("Ошибка в onEdit:", err);
  } finally {
    scriptLock.releaseLock();
  }
}

// Создание скрытого листа, если он не существует
function createHiddenSheet(spreadsheet) {
  const hiddenSheet = spreadsheet.insertSheet(HIDDEN_SHEET_NAME);
  hiddenSheet.hideSheet();  // Скрываем лист
  hiddenSheet.appendRow(['Sheet', 'Cell', 'OldValue', 'NewValue', 'ID', 'Timestamp', 'Retries']);
  return hiddenSheet;
}

function doGet() {
  const hiddenSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("HiddenChanges");
  if (!hiddenSheet) {
    return ContentService.createTextOutput("error: hidden sheet not found")
      .setMimeType(ContentService.MimeType.TEXT);
  }

  const changes = hiddenSheet.getDataRange().getValues();
  const isEmpty = changes.every(row => row.every(cell => cell === "" || cell === null));
  if (isEmpty) {
    return ContentService.createTextOutput("false: no changes detected")
      .setMimeType(ContentService.MimeType.TEXT);
  }

  const cache = CacheService.getScriptCache();
  const lastEditTime = parseInt(cache.get(CACHE_KEY) || "0");
  const now = Date.now();

  if (now - lastEditTime <= INACTIVITY_DELAY) {
    return ContentService.createTextOutput("false: waiting period not passed")
      .setMimeType(ContentService.MimeType.TEXT);
  }

  return ContentService.createTextOutput("true: ready to process")
    .setMimeType(ContentService.MimeType.TEXT);
}
