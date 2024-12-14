from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import os

router = Router()

@router.message(F.text == "/start")
async def start_command(message: Message):
    # Создаём две кнопки
    inline_btn1 = InlineKeyboardButton(text="Нажми меня!", callback_data="button_pressed")
    inline_btn2 = InlineKeyboardButton(text="Вторая кнопка", callback_data="second_button_pressed")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[inline_btn1, inline_btn2]])

    # Отправляем сообщение с кнопками
    await message.answer("Привет! Нажми на одну из кнопок ниже:", reply_markup=keyboard)

@router.callback_query(F.data == "button_pressed")
async def button_pressed_callback(call: CallbackQuery):
    file_path = "example.txt"
    file_content = "Этот файл был создан через Telegram-бота!"

    with open(file_path, "w") as f:
        f.write(file_content)

    await call.message.answer(f"Файл '{file_path}' успешно создан на вашем компьютере!")
    await call.answer()

@router.callback_query(F.data == "second_button_pressed")
async def second_button_pressed_callback(call: CallbackQuery):
    # Логика для второй кнопки
    await call.message.answer("Вы нажали на вторую кнопку!")
    await call.answer()


def register_handlers(dp):
    dp.include_router(router)
