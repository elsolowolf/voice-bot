import os
import requests
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Дані беруться з Railway Variables — нічого не міняй тут
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ELEVENLABS_API_KEY  = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID            = os.environ.get("VOICE_ID")
ADMIN_IDS           = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",")]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_voice(text: str) -> bytes | None:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.85,
            "style": 0.2,
            "use_speaker_boost": True,
        },
    }
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code == 200:
        return response.content
    else:
        logger.error(f"ElevenLabs error {response.status_code}: {response.text}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    await update.message.reply_text(
        "🎙 Надішли мені текст — отримаєш голосове повідомлення.\n"
        "Пересилай куди хочеш: в канал, в особисті, в чат."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    text = update.message.text.strip()
    msg = await update.message.reply_text("⏳ Генерую...")
    audio_bytes = generate_voice(text)
    await msg.delete()

    if audio_bytes is None:
        await update.message.reply_text("❌ Помилка генерації. Перевір API ключ або ліміти ElevenLabs.")
        return

    await update.message.reply_voice(voice=audio_bytes)


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Бот запущено...")
    app.run_polling()


if __name__ == "__main__":
    main()
