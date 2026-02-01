import json
import os
from datetime import datetime

import pandas as pd
import requests

# Google Apps Script Web App URL (doGet returns JSON)
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwd-VHVeKsNKD4lWeJuP0cXPwALnjL2b6GN0QMQrygAgG95VYRDcs-Ca_swum9OiRWfgQ/exec"

OUTPUT_EXCEL = "recipients_data.xlsx"
SYNC_STATE_FILE = "last_sync.json"


def fetch_sheet_data():
    response = requests.get(APPS_SCRIPT_URL, timeout=30)
    response.raise_for_status()
    return response.json()


def get_last_updated_from_rows(headers, rows):
    if "Last Updated" not in headers:
        return None
    idx = headers.index("Last Updated")
    timestamps = []
    for row in rows:
        if idx < len(row) and row[idx]:
            timestamps.append(str(row[idx]))
    return max(timestamps) if timestamps else None


def load_last_sync():
    if not os.path.exists(SYNC_STATE_FILE):
        return None
    with open(SYNC_STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("last_updated")


def save_last_sync(value):
    with open(SYNC_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_updated": value, "synced_at": datetime.utcnow().isoformat()}, f, indent=2)


def main():
    data = fetch_sheet_data()
    headers = data.get("headers", [])
    rows = data.get("rows", [])

    last_updated_remote = get_last_updated_from_rows(headers, rows)
    last_updated_local = load_last_sync()

    if last_updated_remote and last_updated_remote == last_updated_local:
        print("No new updates. Excel not changed.")
        return

    df = pd.DataFrame(rows, columns=headers)
    df.to_excel(OUTPUT_EXCEL, index=False)

    if last_updated_remote:
        save_last_sync(last_updated_remote)
    else:
        save_last_sync(datetime.utcnow().isoformat())

    print("Excel updated from Google Sheet.")


if __name__ == "__main__":
    main()
