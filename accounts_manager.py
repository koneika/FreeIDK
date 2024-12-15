# accounts_manager.py

from datetime import datetime, timedelta
import json
import os

ACCOUNTS_FILE = "accounts.json"

def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as file:
        json.dump(accounts, file, indent=4, ensure_ascii=False)

def restore_requests(accounts):
    now = datetime.utcnow()
    for email, account in accounts.items():
        max_requests = account.get("max_requests", 80)  # По умолчанию 80, если не задано
        # Определим период восстановления на основе max_requests
        # Если max_requests == 80 -> период 3 часа, иначе 5 часов
        if max_requests == 80:
            restore_period = timedelta(hours=3)
        else:
            restore_period = timedelta(hours=5)

        last_restored_str = account.get("last_restored")
        if not last_restored_str:
            # Если не было сохранено время - инициализируем
            account["last_restored"] = now.isoformat()
            continue

        last_restored = datetime.fromisoformat(last_restored_str)
        if now > last_restored:
            elapsed_periods = int((now - last_restored) // restore_period)
            if elapsed_periods > 0:
                new_remaining = min(max_requests, account.get("remaining_requests", max_requests) + elapsed_periods)
                account["remaining_requests"] = new_remaining
                account["last_restored"] = (last_restored + elapsed_periods * restore_period).isoformat()

def decrement_request(accounts, email):
    if email in accounts and accounts[email]["remaining_requests"] > 0:
        accounts[email]["remaining_requests"] -= 1
        save_accounts(accounts)

def get_updated_account_info():
    accounts = load_accounts()
    restore_requests(accounts)
    save_accounts(accounts)
    return accounts
