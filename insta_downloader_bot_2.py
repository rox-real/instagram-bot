import re
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_TOKEN = "8380492578:AAGa9NzlRW9Zd2tESXTzpHnF7kTDCND0FPs"

class InstagramDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'cookiefile': None,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }
    
    def download_video(self, url):
        """Скачать видео и получить информацию"""
        try:
            # Временная папка для скачивания
            temp_path = 'temp_video.mp4'
            
            # Настройки для скачивания
            ydl_opts = self.ydl_opts.copy()
            ydl_opts['outtmpl'] = temp_path
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Получаем информацию
                info = ydl.extract_info(url, download=True)
                
                # Извлекаем статистику
                stats = {
                    'likes': info.get('like_count', 'N/A'),
                    'views': info.get('view_count', 'N/A'),
                    'comments': info.get('comment_count', 'N/A'),
                    'title': info.get('title', ''),
                    'description': info.get('description', '')[:200]
                }
                
                # Читаем файл
                if os.path.exists(temp_path):
                    with open(temp_path, 'rb') as f:
                        video_data = f.read()
                    os.remove(temp_path)
                    return video_data, stats
                else:
                    return None, None
                    
        except Exception as e:
            logger.error(f"Ошибка yt-dlp: {e}")
            return None, None

# Создаем экземпляр загрузчика
downloader = InstagramDownloader()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    welcome_text = """
🎬 Instagram Downloader Bot

Отправь мне ссылку на:
• Reels
• Stories (публичные)
• IGTV/видео посты

И я скачаю видео для тебя!

📝 Пример:
https://www.instagram.com/reel/ABC123/

✅ Работает с публичными постами!
⚡ Использует продвинутый метод загрузки
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
📚 Как использовать:

1️⃣ Скопируй ссылку на Reels/пост в Instagram
2️⃣ Отправь её мне
3️⃣ Жди загрузки!

Поддерживаемые форматы:
✅ instagram.com/reel/XXX
✅ instagram.com/p/XXX
✅ instagram.com/tv/XXX
✅ Короткие ссылки instagr.am

🔥 Новая версия - более надёжная!
    """
    await update.message.reply_text(help_text)

async def handle_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ссылки на Instagram"""
    url = update.message.text.strip()
    
    # Проверяем что это Instagram ссылка
    if not ('instagram.com' in url or 'instagr.am' in url):
        await update.message.reply_text("❌ Это не похоже на ссылку Instagram!")
        return
    
    # Отправляем статус
    status_msg = await update.message.reply_text("🔍 Обрабатываю ссылку...")
    
    try:
        await status_msg.edit_text("📥 Получаю данные и скачиваю видео...")
        
        # Скачиваем видео
        video_data, stats = downloader.download_video(url)
        
        if not video_data:
            await status_msg.edit_text(
                "❌ Не удалось скачать видео.\n\n"
                "Возможные причины:\n"
                "• Пост приватный\n"
                "• Это не видео (фото)\n"
                "• Instagram временно заблокировал загрузку\n\n"
                "Попробуй другую ссылку!"
            )
            return
        
        await status_msg.edit_text("📤 Отправляю видео...")
        
        # Формируем описание
        if stats:
            caption = f"""
📊 Статистика:
❤️ Лайков: {stats['likes']}
👁 Просмотров: {stats['views']}
💬 Комментариев: {stats['comments']}

📝 {stats['description']}

🔗 {url}
            """
        else:
            caption = f"🔗 {url}"
        
        # Отправляем видео
        await update.message.reply_video(
            video=video_data,
            caption=caption[:1024],
            supports_streaming=True,
            read_timeout=60,
            write_timeout=60
        )
        
        # Удаляем статусное сообщение
        await status_msg.delete()
        
        logger.info(f"Успешно скачан пост: {url}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке: {e}")
        await status_msg.edit_text(
            f"❌ Произошла ошибка при загрузке.\n\n"
            f"Попробуйте:\n"
            f"1. Другую ссылку\n"
            f"2. Подождать несколько минут\n"
            f"3. Убедиться что пост публичный"
        )

def main():
    """Запуск бота"""
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("❌ Ошибка: Добавьте токен Telegram бота в переменную TELEGRAM_TOKEN!")
        return
    
    # Создание приложения
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Обработчик для ссылок Instagram
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_instagram_link
        )
    )
    
    # Запуск бота
    print("🤖 Бот запущен и готов к работе!")
    print("📱 Отправьте ссылку на Instagram пост/Reels")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
