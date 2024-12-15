# handlers.py

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import asyncio

from accounts_manager import get_updated_account_info, save_accounts, decrement_request
from test_functions import login_and_send_query

logger = logging.getLogger(__name__)

router = Router()

class Form(StatesGroup):
    entering_query = State()

# Глобальные словари
account_sessions = {}
account_locks = {}

def get_account_lock(email: str):
    if email not in account_locks:
        account_locks[email] = asyncio.Lock()
    return account_locks[email]


@router.message(F.text == "/start")
async def start_command(message: Message):
    # NEW: Обновляем инфо о аккаунтах перед показом
    accounts = get_updated_account_info()

    if not accounts:
        await message.answer("No available accounts. Please add accounts through the menu.")
        logger.warning(f"User {message.from_user.id} initiated /start but no accounts are available.")
        return

    # Показываем минимальный остаток из всех аккаунтов (для примера)
    # Но лучше просто не показывать глобальных счетчиков, а показать при выборе аккаунта
    min_requests = min(acc.get("remaining_requests", acc.get("max_requests", 80)) for acc in accounts.values())

    inline_btn1 = InlineKeyboardButton(text="ChatGPT-4o", callback_data="button_chatgpt")
    inline_btn2 = InlineKeyboardButton(text="AIstudio", callback_data="button_aistudio")
    inline_btn3 = InlineKeyboardButton(text="Manage Accounts", callback_data="manage_accounts")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[inline_btn1, inline_btn2], [inline_btn3]])

    await message.answer(
        "Choose a service to interact with:\n" +
        "!!!For exams, always use ChatGPT-4o, my advice!!!\n" +
        f"ChatGPT-4o - минимальный остаток: {min_requests} запросов\n",
        reply_markup=keyboard
    )
    logger.info(f"User {message.from_user.id} initiated /start.")


@router.callback_query(F.data == "button_chatgpt")
async def chatgpt_callback(call: CallbackQuery, state: FSMContext):
    # NEW: обновляем инфо о аккаунтах перед показом
    accounts = get_updated_account_info()
    if not accounts:
        await call.message.edit_text("No available accounts. Please add accounts through the menu.")
        await call.answer()
        logger.warning("No accounts available when trying to use ChatGPT-4o.")
        return

    buttons = []
    for i, email in enumerate(accounts.keys(), start=1):
        rem = accounts[email].get("remaining_requests", accounts[email].get("max_requests", 80))
        mx = accounts[email].get("max_requests", 80)
        buttons.append([InlineKeyboardButton(text=f"Account {i}: {email} ({rem}/{mx})", callback_data=f"account_{i}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("Choose an account for ChatGPT-4o:", reply_markup=keyboard)
    await call.answer()
    logger.info("User selected ChatGPT-4o and was presented with account buttons.")


@router.callback_query(F.data.startswith("account_"))
async def handle_account_selection(call: CallbackQuery, state: FSMContext):
    # NEW: перед выбором тоже обновляем
    accounts = get_updated_account_info()
    emails = list(accounts.keys())

    account_index = call.data.split("account_")[1].strip()

    if not account_index.isdigit() or not (1 <= int(account_index) <= len(emails)):
        await call.message.edit_text("Invalid account selection.")
        await call.answer()
        logger.error(f"Invalid account selection: {account_index}")
        return

    index = int(account_index) - 1
    email = emails[index]
    password = accounts[email]['password']

    await state.set_state(Form.entering_query)
    await state.update_data(email=email, password=password)

    await call.message.edit_text(f"Account {email} selected. Please enter your query:")
    await call.answer()
    logger.info(f"User selected account {email} and is prompted to enter a query.")


@router.message(Form.entering_query)
async def enter_query(message: Message, state: FSMContext):
    user_query = message.text.strip().replace("\n", " ")
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

    user_id = message.from_user.id

    # NEW: Перед отправкой запроса обновляем инфу о аккаунтах и проверяем лимиты
    accounts = get_updated_account_info()
    if email not in accounts:
        await message.answer("Selected account does not exist.")
        logger.error(f"Selected account {email} does not exist.")
        return

    remaining_requests = accounts[email].get("remaining_requests", accounts[email].get("max_requests", 80))
    if remaining_requests <= 0:
        await message.answer("No remaining requests for this account.")
        logger.warning(f"No remaining requests for account {email}.")
        return

    # Инициализируем сессию для пользователя, если её нет
    if user_id not in account_sessions:
        account_sessions[user_id] = {}
    if email not in account_sessions[user_id]:
        account_sessions[user_id][email] = {"browser": None, "logged_in": False}

    session = account_sessions[user_id][email]
    browser = session.get("browser")
    logged_in = session.get("logged_in", False)

    await message.answer("Обрабатываю ваш запрос...")
    logger.info(f"Пользователь {user_id} отправляет запрос: {user_query} от аккаунта {email}.")

    # Отправляем запрос к ChatGPT
    # Используем лок для логина при необходимости
    lock = get_account_lock(email)
    response = "Произошла ошибка при обработке вашего запроса."
    try:
        if not logged_in:
            if lock.locked():
                await message.answer("Этот аккаунт сейчас занят обработкой логина другого пользователя. Попробуйте позже.")
                logger.info(f"Account {email} is currently being logged in by another user.")
                return
            async with lock:
                response, browser, logged_in = await asyncio.get_running_loop().run_in_executor(
                    None,
                    login_and_send_query,
                    email,
                    password,
                    user_query,
                    browser,
                    logged_in
                )
        else:
            # Аккаунт залогинен - просто отправляем запрос
            response, browser, logged_in = await asyncio.get_running_loop().run_in_executor(
                None,
                login_and_send_query,
                email,
                password,
                user_query,
                browser,
                logged_in
            )
        # Обновляем сессию
        account_sessions[user_id][email] = {"browser": browser, "logged_in": logged_in}

        # Декремент запроса
        accounts = get_updated_account_info()  # обновим перед декрементом на всякий случай
        decrement_request(accounts, email)

    except Exception as e:
        response = "Произошла ошибка при обработке вашего запроса."
        logger.error(f"Ошибка во время обработки запроса для {email}: {e}")

    # NEW: после получения ответа снова обновим инфу о счетчиках и покажем пользователю
    accounts = get_updated_account_info()
    rem = accounts[email].get("remaining_requests", 0)
    mx = accounts[email].get("max_requests", 80)

    # Подготовка ответа с кнопкой "Назад"
    buttons = [[InlineKeyboardButton(text="Назад", callback_data="back_to_accounts")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(f"Ответ от ChatGPT-4o ({email}):\n{response}", reply_markup=keyboard)
    # Отправим следом обновлённый счётчик
    await message.answer(f"Оставшиеся запросы для {email}: {rem}/{mx}")
    logger.info(f"Ответ отправлен пользователю {user_id} от аккаунта {email} с остатком {rem}/{mx}.")


@router.callback_query(F.data == "back_to_accounts", F.state == Form.entering_query)
async def back_to_accounts_callback(call: CallbackQuery, state: FSMContext):
    # Очистка состояния и возврат к выбору аккаунта
    await state.clear()

    accounts = get_updated_account_info()
    if not accounts:
        await call.message.edit_text("No available accounts. Please add accounts through the menu.")
        await call.answer()
        logger.warning("No accounts available when trying to go back to accounts.")
        return

    buttons = []
    for i, email in enumerate(accounts.keys(), start=1):
        lock = get_account_lock(email)
        rem = accounts[email].get("remaining_requests", accounts[email].get("max_requests", 80))
        mx = accounts[email].get("max_requests", 80)
        if lock.locked():
            button_text = f"Account {i}: {email} ({rem}/{mx}) (busy)"
            callback_data = "none"
        else:
            button_text = f"Account {i}: {email} ({rem}/{mx})"
            callback_data = f"account_{i}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("Choose an account:", reply_markup=keyboard)
    await call.answer()
    logger.info(f"User {call.from_user.id} returned to account selection.")


@router.callback_query(F.data == "button_aistudio")
async def aistudio_callback(call: CallbackQuery):
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
    accounts = get_updated_account_info()

    # Покажем минимальные остатки
    if accounts:
        min_requests = min(acc.get("remaining_requests", acc.get("max_requests", 80)) for acc in accounts.values())
    else:
        min_requests = 0

    inline_btn1 = InlineKeyboardButton(text="ChatGPT-4o", callback_data="button_chatgpt")
    inline_btn2 = InlineKeyboardButton(text="AIstudio", callback_data="button_aistudio")
    inline_btn3 = InlineKeyboardButton(text="Manage Accounts", callback_data="manage_accounts")
    keyboard_buttons = [
        [inline_btn1, inline_btn2],
        [inline_btn3]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await call.message.edit_text(
        "Choose a service to interact with:\n" +
        "!!!For exams, always use ChatGPT-4o, my advice!!!\n" +
        f"ChatGPT-4o - минимальный остаток: {min_requests} запросов\n",
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
    from accounts_manager import load_accounts, save_accounts
    try:
        email, password = map(str.strip, message.text.split(",", 1))
        accounts = load_accounts()
        if email in accounts:
            await message.answer("An account with this email already exists.")
            logger.warning(f"Attempted to add duplicate account: {email}")
        else:
            # По умолчанию первый аккаунт 80 запросов, остальные 10, но можно настроить вручную.
            # Здесь можно добавить логику определения max_requests по порядку или другой критерий.
            # Для примера просто по количеству уже существующих аккаунтов:
            idx = len(accounts) + 1
            if idx == 1:
                max_requests = 80
            else:
                max_requests = 10

            accounts[email] = {
                "email": email,
                "password": password,
                "max_requests": max_requests,
                "remaining_requests": max_requests,
                "last_restored": "2024-12-15T00:00:00"
            }
            save_accounts(accounts)
            await message.answer(f"Account {email} added successfully with {max_requests} max requests.")
            logger.info(f"Account added: {email}")
    except Exception as e:
        await message.answer("Invalid format. Please use the format: email@example.com, password")
        logger.error(f"Error processing add account: {e}")


@router.callback_query(F.data == "delete_account")
async def delete_account_callback(call: CallbackQuery):
    from accounts_manager import load_accounts, save_accounts
    accounts = load_accounts()
    if not accounts:
        await call.message.edit_text("No accounts to delete.")
        await call.answer()
        logger.warning("User attempted to delete account but no accounts exist.")
        return

    buttons = []
    emails = list(accounts.keys())
    for i, email in enumerate(emails, start=1):
        buttons.append([InlineKeyboardButton(text=f"Delete {email}", callback_data=f"delete_{i}")])

    buttons.append([InlineKeyboardButton(text="Back to Manage Accounts", callback_data="manage_accounts")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("Select an account to delete:", reply_markup=keyboard)
    await call.answer()
    logger.info("User selected to delete an account.")


@router.callback_query(F.data.startswith("delete_"))
async def handle_delete_account(call: CallbackQuery):
    from accounts_manager import load_accounts, save_accounts
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

    # Показать обновленный список или сообщение, если аккаунтов больше нет
    if accounts:
        buttons = []
        for i, email in enumerate(accounts.keys(), start=1):
            buttons.append([InlineKeyboardButton(text=f"Delete {email}", callback_data=f"delete_{i}")])
        buttons.append([InlineKeyboardButton(text="Back to Manage Accounts", callback_data="manage_accounts")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await call.message.answer("Select another account to delete:", reply_markup=keyboard)
    else:
        await call.message.answer("No more accounts to delete.")
