from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

router = Router()

@router.message(F.text == "/start")
async def start_command(message: Message):
    # Кнопки стартового меню
    inline_btn1 = InlineKeyboardButton(text="Первая кнопка", callback_data="button_pressed")
    inline_btn2 = InlineKeyboardButton(text="Вторая кнопка", callback_data="second_button_pressed")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[inline_btn1, inline_btn2]])

    await message.answer("Привет! Выберите одну из кнопок:", reply_markup=keyboard)


@router.callback_query(F.data == "button_pressed")
async def button_pressed_callback(call: CallbackQuery):
    # Обновляем текст сообщения и показываем новые кнопки
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Кнопка 1.1", callback_data="button_1_1")],
            [InlineKeyboardButton(text="Кнопка 1.2", callback_data="button_1_2")],
            [InlineKeyboardButton(text="Кнопка 1.3", callback_data="button_1_3")],
            [InlineKeyboardButton(text="Кнопка 1.4", callback_data="button_1_4")],
            [InlineKeyboardButton(text="Кнопка 1.5", callback_data="button_1_5")],
        ]
    )
    await call.message.edit_text("Вы выбрали первую кнопку. Теперь выберите одну из этих кнопок:", reply_markup=keyboard)
    await call.answer()


@router.callback_query(F.data == "second_button_pressed")
async def second_button_pressed_callback(call: CallbackQuery):
    # Обновляем текст сообщения и показываем новые кнопки
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Кнопка 2.1", callback_data="button_2_1")],
            [InlineKeyboardButton(text="Кнопка 2.2", callback_data="button_2_2")],
            [InlineKeyboardButton(text="Кнопка 2.3", callback_data="button_2_3")],
            [InlineKeyboardButton(text="Кнопка 2.4", callback_data="button_2_4")],
            [InlineKeyboardButton(text="Кнопка 2.5", callback_data="button_2_5")],
        ]
    )
    await call.message.edit_text("Вы выбрали вторую кнопку. Теперь выберите одну из этих кнопок:", reply_markup=keyboard)
    await call.answer()


@router.callback_query(F.data.startswith("button_1_"))
async def handle_first_button_submenu(call: CallbackQuery):
    # Обновляем текст после выбора из подменю первой кнопки
    await call.message.edit_text(f"Вы нажали на {call.data.replace('_', ' ')}. Логика для этой кнопки может быть здесь.")
    await call.answer()


@router.callback_query(F.data.startswith("button_2_"))
async def handle_second_button_submenu(call: CallbackQuery):
    # Обновляем текст после выбора из подменю второй кнопки
    await call.message.edit_text(f"Вы нажали на {call.data.replace('_', ' ')}. Логика для этой кнопки может быть здесь.")
    await call.answer()


def register_handlers(dp):
    dp.include_router(router)


