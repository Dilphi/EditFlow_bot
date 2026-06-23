import logging
import asyncio
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.enums import ParseMode, ChatAction
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import MODES, TELEGRAM_TOKEN
from prompts import get_prompt
from services import process_text_with_ai, process_file

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Создаем роутер для обработчиков
router = Router()

# Хранилище режимов пользователей
user_modes: dict[int, str] = {}

# Клавиатура выбора режима
def get_mode_keyboard(current_mode: str = "default") -> InlineKeyboardMarkup:
    """Создает клавиатуру с режимами обработки."""
    buttons = []
    for mode_id, mode_name in MODES.items():
        is_active = " ✅" if mode_id == current_mode else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{mode_name}{is_active}",
                callback_data=f"mode_{mode_id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="📖 Как использовать?", callback_data="help")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Вспомогательная клавиатура
def get_action_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с действиями."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Сменить режим", callback_data="change_mode")],
        [InlineKeyboardButton(text="📖 Помощь", callback_data="help")]
    ])

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start."""
    user_id = message.from_user.id
    user_modes[user_id] = "default"
    
    welcome_text = (
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "📎 Я бот для обработки текстовых файлов.\n\n"
        "✅ <b>Что я умею:</b>\n"
        "• 📝 Стандартный — привести текст в порядок\n"
        "• 🎓 Курсы 1С — создание структуры курса из материала\n"
        "• 📊 Профессиональный — деловой стиль\n"
        "• ✍️ Креативный — художественная обработка\n"
        "• 📋 Краткое содержание — выделение главного\n\n"
        "📤 <b>Просто отправьте текстовый файл (.txt, .docx, .pptx)</b>\n"
        "или вставьте текст в сообщение!\n\n"
        "Выберите режим обработки:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_mode_keyboard("default")
    )

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обработчик команды /help."""
    help_text = (
        "📖 <b>Как работать с ботом:</b>\n\n"
        "1️⃣ <b>Выберите режим</b> обработки текста\n"
        "2️⃣ <b>Отправьте файл</b> (.txt, .docx, .pptx)\n"
        "   или вставьте текст в сообщение\n"
        "3️⃣ <b>Получите</b> обработанный текст\n\n"
        "📌 <b>Режимы:</b>\n"
        "• 📝 Стандартный — исправление ошибок и структурирование\n"
        "• 🎓 Курсы 1С — создание структурированного учебного курса\n"
        "• 📊 Профессиональный — деловой стиль\n"
        "• ✍️ Креативный — художественная обработка\n"
        "• 📋 Краткое содержание — выделение главного\n\n"
        "📞 Вопросы: @support"
    )
    await message.answer(help_text, reply_markup=get_action_keyboard())

@router.callback_query(F.data.startswith("mode_"))
async def callback_mode(callback: CallbackQuery) -> None:
    """Обработчик выбора режима."""
    mode_id = callback.data.replace("mode_", "")
    user_id = callback.from_user.id
    
    if mode_id in MODES:
        user_modes[user_id] = mode_id
        await callback.answer(f"✅ Режим «{MODES[mode_id]}» активирован!")
        
        await callback.message.edit_text(
            f"🎯 <b>Выбран режим:</b> {MODES[mode_id]}\n\n"
            "📤 Отправьте текстовый файл или вставьте текст для обработки.",
            reply_markup=get_mode_keyboard(mode_id)
        )
    else:
        await callback.answer("❌ Неизвестный режим", show_alert=True)

@router.callback_query(F.data == "change_mode")
async def callback_change_mode(callback: CallbackQuery) -> None:
    """Обработчик смены режима."""
    user_id = callback.from_user.id
    current_mode = user_modes.get(user_id, "default")
    
    await callback.message.edit_text(
        "🎯 <b>Выберите режим обработки текста:</b>",
        reply_markup=get_mode_keyboard(current_mode)
    )
    await callback.answer()

@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery) -> None:
    """Обработчик помощи."""
    help_text = (
        "📖 <b>Инструкция:</b>\n\n"
        "1️⃣ Нажмите «Сменить режим» для выбора обработки\n"
        "2️⃣ Отправьте текстовый файл или вставьте текст\n"
        "3️⃣ Получите обработанный результат\n\n"
        "📁 <b>Поддерживаемые форматы:</b>\n"
        "• .txt (простой текст)\n"
        "• .docx (документы Word)\n"
        "• .pptx (презентации)\n\n"
        "Также можно просто вставить текст в чат!"
    )
    await callback.message.answer(help_text, reply_markup=get_action_keyboard())
    await callback.answer()

@router.message(Command("mode"))
async def cmd_mode(message: Message) -> None:
    """Команда для смены режима."""
    user_id = message.from_user.id
    current_mode = user_modes.get(user_id, "default")
    
    await message.answer(
        "🎯 <b>Выберите режим обработки:</b>",
        reply_markup=get_mode_keyboard(current_mode)
    )

@router.message(F.text)
async def handle_text(message: Message) -> None:
    """Обработчик текстовых сообщений."""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if len(text) < 10:
        await message.answer(
            "⚠️ Текст слишком короткий. Отправьте более содержательный текст или файл."
        )
        return
    
    if text.startswith("/"):
        return
    
    # Получаем режим пользователя
    mode = user_modes.get(user_id, "default")
    mode_name = MODES.get(mode, "Стандартный")
    
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    # Обработка текста
    result = await process_text_with_ai(text, mode)
    
    # Отправка результата
    if len(result) > 4000:
        # Разбиваем на части
        parts = [result[i:i+4000] for i in range(0, len(result), 4000)]
        for i, part in enumerate(parts):
            prefix = f"📄 Часть {i+1}/{len(parts)}:\n\n" if len(parts) > 1 else ""
            await message.answer(f"{prefix}{part}")
    else:
        await message.answer(
            f"✅ <b>Режим:</b> {mode_name}\n\n{result}",
            reply_markup=get_action_keyboard()
        )

@router.message(F.document)
async def handle_document(message: Message) -> None:
    """Обработчик документов."""
    user_id = message.from_user.id
    document = message.document
    
    # Проверяем расширение
    allowed_extensions = ['.txt', '.docx', '.pptx']
    file_ext = f".{document.file_name.split('.')[-1].lower()}" if document.file_name else ""
    
    if file_ext not in allowed_extensions:
        await message.answer(
            f"❌ Формат {file_ext} не поддерживается.\n"
            f"Поддерживаемые форматы: {', '.join(allowed_extensions)}"
        )
        return
    
    # Проверяем размер
    if document.file_size > 10 * 1024 * 1024:
        await message.answer("⚠️ Файл слишком большой. Максимальный размер: 10 MB")
        return
    
    # Сообщаем о начале обработки
    status_msg = await message.answer(
        f"⏳ Начинаю обработку файла <b>{document.file_name}</b>...\n"
        f"📊 Размер: {document.file_size // 1024} KB\n\n"
        f"Это может занять несколько минут ⏰"
    )
    
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    try:
        # Скачиваем файл
        file = await bot.get_file(document.file_id)
        file_data = await bot.download_file(file.file_path)
        
        # Конвертируем в bytes
        if hasattr(file_data, 'read'):
            file_bytes = file_data.read()
        elif hasattr(file_data, 'getvalue'):
            file_bytes = file_data.getvalue()
        else:
            file_bytes = bytes(file_data)
        
        # Обновляем статус
        await status_msg.edit_text(
            f"⏳ Обработка файла <b>{document.file_name}</b>...\n"
            f"📊 Размер: {document.file_size // 1024} KB\n"
            f"🔄 Выполняется анализ и структурирование..."
        )
        
        # Обрабатываем файл
        mode = user_modes.get(user_id, "default")
        mode_name = MODES.get(mode, "Стандартный")
        
        result_text = await process_file(file_bytes, document.file_name, mode)
        
        # Обновляем статус
        await status_msg.edit_text(
            f"✅ Обработка завершена!\n"
            f"📄 Режим: {mode_name}\n"
            f"📊 Длина: {len(result_text)} символов"
        )
        
        # Создаем имя для выходного файла
        base_name = document.file_name.rsplit('.', 1)[0]
        output_filename = f"{base_name}_processed.txt"
        
        # Отправляем результат как текстовый файл
        await message.answer_document(
            BufferedInputFile(
                result_text.encode('utf-8'),
                filename=output_filename
            ),
            caption=f"✅ <b>Обработано в режиме:</b> {mode_name}\n\n"
                   f"📄 Исходный файл: {document.file_name}\n"
                   f"📊 Длина: {len(result_text)} символов"
        )
        
        # Показываем превью
        preview = result_text[:300] + "..." if len(result_text) > 300 else result_text
        await message.answer(
            f"📝 <b>Превью результата:</b>\n\n{preview}"
        )
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        await status_msg.edit_text(
            f"❌ Ошибка при обработке файла: {str(e)[:200]}\n"
            "Попробуйте скопировать текст в сообщение."
        )

@router.message()
async def handle_other(message: Message) -> None:
    """Обработчик всех остальных сообщений."""
    await message.answer(
        "📎 Отправьте текстовый файл или вставьте текст для обработки.\n"
        "Используйте /help для инструкции."
    )