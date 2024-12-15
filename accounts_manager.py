# accounts_manager.py

import json
import os
import logging

logger = logging.getLogger(__name__)

ACCOUNTS_FILE = "accounts.json"

def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as file:
            try:
                accounts = json.load(file)
                logger.info("Accounts loaded successfully.")
                return accounts
            except json.JSONDecodeError:
                logger.error("Cannot decode accounts.json. Overwriting the file.")
    else:
        logger.info("accounts.json does not exist. Starting with an empty accounts list.")
    return {}

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as file:
        json.dump(accounts, file, indent=4)
    logger.info("Accounts saved successfully.")
