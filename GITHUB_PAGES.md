# GitHub Pages Deployment Guide

## Your Site is Ready! 🎉

The payment receipt verification system is deployed at:
**https://Sir0Exclusive.github.io/payment-receipts/**

## How to Enable GitHub Pages (if not working)

1. Go to: https://github.com/Sir0Exclusive/payment-receipts/settings
2. Scroll to "Pages" section (left sidebar)
3. Under "Source", select: **Branch: main, Folder: / (root)**
4. Click "Save"
5. Wait 1-2 minutes for deployment
6. Your site will be live at: https://Sir0Exclusive.github.io/payment-receipts/

## What's Deployed

- **Main Portal**: `/web-portal/index.html` - User login and receipt dashboard
- **Verification Page**: `/web-portal/verify.html` - QR code scanning and verification
- **Home Page**: `/index.html` - Welcome page with links

## Features

✅ User authentication (email/password)
✅ Receipt verification with tamper detection
✅ QR code scanning
✅ SHA-256 hash validation
✅ Google Sheets integration
✅ Recipient email capture

## QR Code Links

Each receipt's QR code points to:
```
https://Sir0Exclusive.github.io/payment-receipts/verify.html?id={receipt_id}
```

## Testing

1. Generate a receipt locally:
   ```
   python export_receipt.py
   ```

2. Open the QR code from the PDF and scan it, OR
3. Visit: https://Sir0Exclusive.github.io/payment-receipts/verify.html
4. Enter receipt ID to verify

## Notes

- All data is stored locally in Google Sheets
- QR codes include tamper-proof hashing
- User accounts are stored in browser localStorage
- No backend database needed - fully static site
