function toggleSheetVisibility(sheetName, isHidden) {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(sheetName);
    
    if (!sheet) {
      throw new Error(`Лист "${sheetName}" не найден`);
    }
    
    if (isHidden) {
      sheet.hideSheet();
    } else {
      sheet.showSheet();
    }
  }
  

function hideExampleSheet() {
  toggleSheetVisibility("HiddenChanges", true);
}

function showExampleSheet() {
  toggleSheetVisibility("HiddenChanges", false);
}