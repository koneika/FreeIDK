# handlers.py

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from accounts_manager import load_accounts, save_accounts
from test_functions import login_and_send_query

import asyncio

logger = logging.getLogger(__name__)

router = Router()

# Define FSM states
class Form(StatesGroup):
    entering_query = State()

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
async def chatgpt_callback(call: CallbackQuery, state: FSMContext):
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

@router.callback_query(F.data.startswith("account_"))
async def handle_account_selection(call: CallbackQuery, state: FSMContext):
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

    # Set state for entering query
    await state.set_state(Form.entering_query)
    await state.update_data(email=email, password=password)

    await call.message.edit_text(f"Account {email} selected. Please enter your query:")
    await call.answer()
    logger.info(f"User selected account {email} and is prompted to enter a query.")

@router.message(Form.entering_query)
async def enter_query(message: Message, state: FSMContext):
    user_query = message.text.strip().replace("\n", " ")  # Удаляем переносы строк
    if not user_query:
        await message.answer("Пожалуйста, введите валидный запрос (без пустых строк).")
        return

    data = await state.get_data()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        await message.answer("Информация об аккаунте отсутствует. Выберите аккаунт заново.")
        logger.error("Информация об аккаунте отсутствует в состоянии.")
        await state.clear()
        return

    await message.answer("Обрабатываю ваш запрос...")
    logger.info(f"Пользователь {message.from_user.id} отправляет запрос: {user_query} от аккаунта {email}.")

    # Выполнение login_and_send_query в отдельном потоке
    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, login_and_send_query, email, password, user_query)
        logger.info(f"Получен ответ для {email}: {response}")
    except Exception as e:
        response = "Произошла ошибка при обработке вашего запроса."
        logger.error(f"Ошибка во время обработки запроса для {email}: {e}")

    # Подготовка ответа с кнопкой "Назад"
    buttons = [[InlineKeyboardButton(text="Назад", callback_data="back_to_accounts")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(f"Ответ от ChatGPT-4o ({email}):\n{response}", reply_markup=keyboard)
    logger.info(f"Ответ отправлен пользователю {message.from_user.id} от аккаунта {email}.")


@router.callback_query(F.data == "back_to_accounts", F.state == Form.entering_query)
async def back_to_accounts_callback(call: CallbackQuery, state: FSMContext):
    # Clear state and return to account selection
    await state.clear()

    accounts = load_accounts()
    if not accounts:
        await call.message.edit_text("No available accounts. Please add accounts through the menu.")
        await call.answer()
        logger.warning("No accounts available when trying to go back to accounts.")
        return

    buttons = []
    for i, email in enumerate(accounts.keys(), start=1):
        buttons.append([InlineKeyboardButton(text=f"Account {i}: {email}", callback_data=f"account_{i}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("Choose an account:", reply_markup=keyboard)
    await call.answer()
    logger.info(f"User {call.from_user.id} returned to account selection.")

@router.callback_query(F.data == "button_aistudio")
async def aistudio_callback(call: CallbackQuery):
    # Similarly, implement AIstudio functionality if needed
    await call.message.edit_text("AIstudio functionality is not implemented yet.")
    await call.answer()
    logger.info("User selected AIstudio, which is not implemented.")

@router.callback_query(F.data == "manage_accounts")
async def manage_accounts_callback(call: CallbackQuery):
    buttons = [
        [InlineKeyboardButton(text="Add Account", callback_data="add_account")],
        [InlineKeyboardButton(text="Delete Account", callback_data="delete_account")],
        [InlineKeyboardButton(text="Back to Main Menu", callback_data="back_to_menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("Manage Accounts:", reply_markup=keyboard)
    await call.answer()
    logger.info("User selected Manage Accounts.")

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(call: CallbackQuery):
    inline_btn1 = InlineKeyboardButton(text="ChatGPT-4o", callback_data="button_chatgpt")
    inline_btn2 = InlineKeyboardButton(text="AIstudio", callback_data="button_aistudio")
    inline_btn3 = InlineKeyboardButton(text="Manage Accounts", callback_data="manage_accounts")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[inline_btn1, inline_btn2], [inline_btn3]])

    await call.message.edit_text(
        "Choose a service to interact with:\n" +
        "!!!For exams, always use ChatGPT-4o, my advice!!!\n" +
        f"ChatGPT-4o - {digit}/1000 requests\n"
        f"AIstudio - {tokens}/100000 tokens",
        reply_markup=keyboard
    )
    await call.answer()
    logger.info("User returned to main menu.")

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

    buttons.append([InlineKeyboardButton(text="Back to Manage Accounts", callback_data="manage_accounts")])

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

    # Show updated list or message if no accounts left
    if accounts:
        buttons = []
        for i, email in enumerate(accounts.keys(), start=1):
            buttons.append([InlineKeyboardButton(text=f"Delete {email}", callback_data=f"delete_{i}")])
        buttons.append([InlineKeyboardButton(text="Back to Manage Accounts", callback_data="manage_accounts")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await call.message.answer("Select another account to delete:", reply_markup=keyboard)
    else:
        await call.message.answer("No more accounts to delete.")
