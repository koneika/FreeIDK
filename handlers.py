from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import os  # Для работы с файлами

router = Router()

@router.message(F.text == "/start")
async def start_command(message: Message):
    inline_btn = InlineKeyboardButton(text="Нажми меня!", callback_data="button_pressed")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[inline_btn]])
    await message.answer("Привет! Нажми на кнопку ниже:", reply_markup=keyboard)

@router.callback_query(F.data == "button_pressed")
async def button_pressed_callback(call: CallbackQuery):
    # Определяем путь для нового файла
    file_path = "example.txt"  # Вы можете указать абсолютный или относительный путь
    file_content = "Этот файл был создан через Telegram-бота!"

    # Создаём файл и записываем в него данные
    with open(file_path, "w") as f:
        f.write(file_content)

    # Уведомляем пользователя
    await call.message.answer(f"Файл '{file_path}' успешно создан на вашем компьютере!")
    await call.answer()


def register_handlers(dp):
    dp.include_router(router)
