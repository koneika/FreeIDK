# handlers.py

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from accounts_manager import load_accounts, save_accounts
from test_functions import login_and_send_query

import asyncio

logger = logging.getLogger(__name__)

router = Router()

digit = 1000
tokens = 100000

@router.message(F.text == "/start")
async def start_command(message: Message):
    inline_btn1 = InlineKeyboardButton(text="ChatGPT-4o", callback_data="button_chatgpt")
    inline_btn2 = InlineKeyboardButton(text="AIstudio", callback_data="button_aistudio")
    inline_btn3 = InlineKeyboardButton(text="Manage Accounts", callback_data="manage_accounts")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[inline_btn1, inline_btn2], [inline_btn3]])

    await message.answer(
        "Choose a service to interact with:\n" +
        "!!!For exams, always use ChatGPT-4o, my advice!!!\n" +
        f"ChatGPT-4o - {digit}/1000 requests\n"
        f"AIstudio - {tokens}/100000 tokens",
        reply_markup=keyboard
    )
    logger.info(f"User {message.from_user.id} initiated /start.")

@router.callback_query(F.data == "button_chatgpt")
async def chatgpt_callback(call: CallbackQuery):
    accounts = load_accounts()
    if not accounts:
        await call.message.edit_text("No available accounts. Please add accounts through the menu.")
        await call.answer()
        logger.warning("No accounts available when trying to use ChatGPT-4o.")
        return

    buttons = []
    for i, email in enumerate(accounts.keys(), start=1):
        buttons.append([InlineKeyboardButton(text=f"Account {i}: {email}", callback_data=f"account_{i}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("Choose an account for ChatGPT-4o:", reply_markup=keyboard)
    await call.answer()
    logger.info("User selected ChatGPT-4o and was presented with account buttons.")

@router.callback_query(F.data == "button_aistudio")
async def aistudio_callback(call: CallbackQuery):
    # Similarly, implement AIstudio functionality if needed
    await call.message.edit_text("AIstudio functionality is not implemented yet.")
    await call.answer()
    logger.info("User selected AIstudio, which is not implemented.")

@router.callback_query(F.data.startswith("account_"))
async def handle_account_selection(call: CallbackQuery):
    account_index = call.data.split("account_")[1].strip()
    accounts = load_accounts()
    emails = list(accounts.keys())

    if not account_index.isdigit() or not (1 <= int(account_index) <= len(emails)):
        await call.message.edit_text("Invalid account selection.")
        await call.answer()
        logger.error(f"Invalid account selection: {account_index}")
        return

    index = int(account_index) - 1
    email = emails[index]
    password = accounts[email]['password']

    # For demonstration, using a fixed query. You can extend this to ask user for input.
    query = "Hello, how are you?"

    await call.message.edit_text(f"Sending query from account: {email}...")
    await call.answer()

    # Execute the login_and_send_query function in a separate thread to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, login_and_send_query, email, password, query)
        logger.info(f"Received response for {email}: {response}")
    except Exception as e:
        response = "An error occurred while processing your request."
        logger.error(f"Error during processing request for {email}: {e}")

    await call.message.answer(f"Response from ChatGPT-4o ({email}):\n{response}")

@router.callback_query(F.data == "manage_accounts")
async def manage_accounts_callback(call: CallbackQuery):
    buttons = [
        [InlineKeyboardButton(text="Add Account", callback_data="add_account")],
        [InlineKeyboardButton(text="Delete Account", callback_data="delete_account")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("Manage Accounts:", reply_markup=keyboard)
    await call.answer()
    logger.info("User selected Manage Accounts.")

@router.callback_query(F.data == "add_account")
async def add_account_callback(call: CallbackQuery):
    await call.message.edit_text("Please enter email and password separated by a comma (e.g., email@example.com, password):")
    await call.answer()
    logger.info("User selected to add an account.")

@router.message(F.reply_to_message & F.text.contains(","))
async def process_add_account(message: Message):
    try:
        email, password = map(str.strip, message.text.split(",", 1))
        accounts = load_accounts()
        if email in accounts:
            await message.answer("An account with this email already exists.")
            logger.warning(f"Attempted to add duplicate account: {email}")
        else:
            accounts[email] = {"email": email, "password": password}
            save_accounts(accounts)
            await message.answer(f"Account {email} added successfully.")
            logger.info(f"Account added: {email}")
    except Exception as e:
        await message.answer("Invalid format. Please use the format: email@example.com, password")
        logger.error(f"Error processing add account: {e}")

@router.callback_query(F.data == "delete_account")
async def delete_account_callback(call: CallbackQuery):
    accounts = load_accounts()
    if not accounts:
        await call.message.edit_text("No accounts to delete.")
        await call.answer()
        logger.warning("User attempted to delete account but no accounts exist.")
        return

    buttons = []
    for i, email in enumerate(accounts.keys(), start=1):
        buttons.append([InlineKeyboardButton(text=f"Delete {email}", callback_data=f"delete_{i}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("Select an account to delete:", reply_markup=keyboard)
    await call.answer()
    logger.info("User selected to delete an account.")

@router.callback_query(F.data.startswith("delete_"))
async def handle_delete_account(call: CallbackQuery):
    account_index = call.data.split("delete_")[1].strip()
    accounts = load_accounts()
    emails = list(accounts.keys())

    if not account_index.isdigit() or not (1 <= int(account_index) <= len(emails)):
        await call.message.edit_text("Invalid account selection for deletion.")
        await call.answer()
        logger.error(f"Invalid account deletion selection: {account_index}")
        return

    index = int(account_index) - 1
    email = emails[index]
    del accounts[email]
    save_accounts(accounts)

    await call.message.edit_text(f"Account {email} has been deleted.")
    await call.answer()
    logger.info(f"Account deleted: {email}")
