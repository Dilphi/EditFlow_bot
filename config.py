import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#llama-3.1-70b-versatile (самая мощная) llama-3.1-8b-instant (быстрая и дешевая)
GROQ_MODEL = "llama-3.1-8b-instant" 
GEMINI_MODEL = "gemini-2.5-flash"

# Режимы обработки
MODES = {
    "default": "📝 Стандартный",
    "course_1c": "🎓 Курсы 1С",
    "video_script": "🎬 Видео-сценарий",
    "professional": "📊 Профессиональный",
    "creative": "✍️ Креативный",
    "summary": "📋 Краткое содержание"
}

def check_config():
    missing = []
    if not TELEGRAM_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    
    if missing:
        raise RuntimeError(
            f"❌ Отсутствуют переменные окружения: {', '.join(missing)}\n"
            "Скопируйте .env.example в .env и заполните значения."
        )