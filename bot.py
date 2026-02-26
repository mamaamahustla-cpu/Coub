import asyncio
import random
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

# Токен бота (получите у @BotFather)
TOKEN = "8713010196:AAFrSa5-dUpuSF5qfxo7v_56JOuy8QHiH6M"

# Создаем экземпляры бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Регулярное выражение для парсинга команды /roll dN
# Примеры: /roll d20, /roll d6, /roll d100
ROLL_PATTERN = r'^/roll\s+d(\d+)$'

@dp.message(Command("roll"))
async def cmd_roll(message: Message):
    """
    Обработчик команды /roll
    Поддерживает формат: /roll dN, где N - число граней
    """
    # Получаем текст сообщения
    text = message.text.strip()
    
    # Проверяем соответствие шаблону
    match = re.match(ROLL_PATTERN, text, re.IGNORECASE)
    
    if not match:
        # Если формат неверный, отправляем инструкцию
        await message.reply(
            "❌ Неправильный формат команды!\n"
            "Используйте: `/roll dN`\n"
            "Пример: `/roll d20` - бросить 20-гранный кубик",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Получаем количество граней из команды
    sides = int(match.group(1))
    
    # Проверяем корректность числа граней
    if sides < 2:
        await message.reply("❌ У кубика должно быть минимум 2 грани!")
        return
    
    if sides > 1000000:
        await message.reply("❌ Слишком большое число граней! Максимум - 1,000,000")
        return
    
    # Генерируем случайное число от 1 до N
    result = random.randint(1, sides)
    
    # Получаем информацию об отправителе
    user = message.from_user
    user_name = user.first_name
    if user.username:
        user_name = f"@{user.username}"
    
    # Формируем красивое сообщение с результатом
    # Если группа большая, добавляем упоминание пользователя
    if message.chat.type in ["group", "supergroup"]:
        response = (
            f"🎲 *Бросок кубика d{sides}*\n"
            f"👤 Игрок: {user_name}\n"
            f"✨ Результат: **{result}**"
        )
    else:
        # Если это личный чат с ботом
        response = (
            f"🎲 Бросок d{sides}: **{result}**"
        )
    
    # Отправляем результат
    await message.reply(response, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("start", "help"))
async def cmd_start_help(message: Message):
    """Обработчик команд /start и /help"""
    help_text = (
        "🎲 *Dice Roller Bot*\n\n"
        "Я помогу вам бросать кубики в групповых чатах!\n\n"
        "*Команды:*\n"
        "• `/roll dN` - бросить N-гранный кубик (N от 2 до 1,000,000)\n"
        "• `/help` - показать эту справку\n\n"
        "*Примеры:*\n"
        "• `/roll d20` - для D&D\n"
        "• `/roll d6` - для настольных игр\n"
        "• `/roll d100` - процентный бросок"
    )
    
    await message.reply(help_text, parse_mode=ParseMode.MARKDOWN)

@dp.message()
async def handle_other_messages(message: Message):
    """Игнорируем все остальные сообщения в группе"""
    # Можно ничего не делать, чтобы не спамить
    pass

async def main():
    """Главная функция запуска бота"""
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
