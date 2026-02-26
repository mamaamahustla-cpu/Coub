import asyncio
import random
import re
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота (ЗАМЕНИ НА СВОЙ НОВЫЙ! Старый конфликтует)
TOKEN = "8713010196:AAF-JiZfrvW0zLYTsVhPTKJFlwUIzi7hA2k"

# Создаем экземпляры бота и диспетчера
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # ← ВАЖНО:改用 HTML
)
dp = Dispatcher()

@dp.message(Command("start", "help"))
async def cmd_start_help(message: Message):
    """Обработчик команд /start и /help"""
    help_text = (
        "🎲 <b>Dice Roller Bot</b>\n\n"
        "Я помогаю бросать кубики!\n\n"
        "<b>Команды:</b>\n"
        "• /roll d20 - один кубик\n"
        "• /roll 2d6 - два кубика\n"
        "• /roll d100+10 - с бонусом\n\n"
        "<b>Пример:</b> /roll d20"
    )
    await message.reply(help_text, parse_mode=ParseMode.HTML)

@dp.message(Command("roll"))
async def cmd_roll(message: Message):
    """
    Упрощенный обработчик /roll
    """
    # Получаем текст после команды
    text = message.text.strip()
    parts = text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.reply(
            "❌ Напиши: /roll d20\n"
            "Примеры: /roll 2d6, /roll d100+10"
        )
        return
    
    roll_arg = parts[1].strip().lower()
    logger.info(f"Бросок: {roll_arg}")
    
    # Убираем лишние пробелы
    roll_arg = roll_arg.replace(" ", "")
    
    # Простейший парсинг
    try:
        # Проверяем формат d20
        if roll_arg.startswith('d') and '+' not in roll_arg:
            sides = int(roll_arg[1:])
            result = random.randint(1, sides)
            await message.reply(f"🎲 <b>d{sides}:</b> {result}")
            
        # Проверяем формат 2d20
        elif 'd' in roll_arg and '+' not in roll_arg:
            num, sides = map(int, roll_arg.split('d'))
            if num > 10:
                await message.reply("❌ Слишком много кубиков (макс 10)")
                return
            results = [random.randint(1, sides) for _ in range(num)]
            total = sum(results)
            results_str = " + ".join(map(str, results))
            await message.reply(
                f"🎲 <b>{num}d{sides}:</b>\n"
                f"{results_str} = <b>{total}</b>"
            )
            
        # Проверяем формат d20+5
        elif roll_arg.startswith('d') and '+' in roll_arg:
            dice_part, bonus = roll_arg.split('+')
            sides = int(dice_part[1:])
            bonus = int(bonus)
            result = random.randint(1, sides)
            total = result + bonus
            await message.reply(
                f"🎲 <b>d{sides}+{bonus}:</b>\n"
                f"{result} + {bonus} = <b>{total}</b>"
            )
            
        # Проверяем формат 2d20+3
        elif 'd' in roll_arg and '+' in roll_arg:
            dice_part, bonus = roll_arg.split('+')
            num, sides = map(int, dice_part.split('d'))
            bonus = int(bonus)
            if num > 10:
                await message.reply("❌ Слишком много кубиков (макс 10)")
                return
            results = [random.randint(1, sides) for _ in range(num)]
            total = sum(results) + bonus
            results_str = " + ".join(map(str, results))
            await message.reply(
                f"🎲 <b>{num}d{sides}+{bonus}:</b>\n"
                f"{results_str} + {bonus} = <b>{total}</b>"
            )
            
        else:
            await message.reply("❌ Непонятный формат. Пиши /roll d20")
            
    except ValueError:
        await message.reply("❌ Ошибка в числах. Пример: /roll d20")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.reply("❌ Что-то пошло не так")

@dp.message()
async def ignore_all(message: Message):
    """Игнорируем всё кроме команд"""
    pass

async def main():
    logger.info("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")
