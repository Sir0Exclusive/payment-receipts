// Google Apps Script for updating Google Sheet with recipient email
// 1) Create a Google Sheet with columns: Receipt No, Name, Amount, Due Amount, Date, Description, Recipient Email
// 2) Copy your Spreadsheet ID and set SPREADSHEET_ID
// 3) Deploy as Web App (Execute as: Me, Who has access: Anyone)

const SPREADSHEET_ID = '1Pelzk18wzP4ZjDbe8nV602UNiGIe45n3TOInrmxyr0M';
const SHEET_NAME = 'Receipts';

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const receiptId = String(data.receiptId || '').trim();
    const email = String(data.email || '').trim();

    if (!receiptId || !email) {
      return ContentService.createTextOutput('Missing receiptId or email');
    }

    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);

    // Find row by Receipt No (assumed in column 1)
    const dataRange = sheet.getDataRange().getValues();
    let targetRow = -1;
    for (let i = 1; i < dataRange.length; i++) {
      if (String(dataRange[i][0]) === receiptId) {
        targetRow = i + 1;
        break;
      }
    }

    // If not found, append new row with only Receipt No + Email
    if (targetRow === -1) {
      sheet.appendRow([receiptId, '', '', '', '', '', email]);
    } else {
      // Recipient Email in column 7
      sheet.getRange(targetRow, 7).setValue(email);
    }

    // Create a separate sheet per recipient email (optional)
    const recipientSheetName = email.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 90);
    let recipientSheet = ss.getSheetByName(recipientSheetName);
    if (!recipientSheet) {
      recipientSheet = ss.insertSheet(recipientSheetName);
      recipientSheet.appendRow(['Receipt No', 'Recipient Email', 'Timestamp']);
    }
    recipientSheet.appendRow([receiptId, email, new Date().toISOString()]);

    return ContentService.createTextOutput('OK');
  } catch (err) {
    return ContentService.createTextOutput('Error: ' + err.message);
  }
}
