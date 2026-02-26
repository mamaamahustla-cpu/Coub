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

# Токен бота (ЗАМЕНИ НА СВОЙ!)
TOKEN = "8713010196:AAFrSa5-dUpuSF5qfxo7v_56JOuy8QHiH6M"

# Создаем экземпляры бота и диспетчера
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()

# Регулярное выражение для разных форматов
ROLL_PATTERN = r'^/roll\s*(?:(\d+))?d(\d+)(?:\+(\d+))?$'

@dp.message(Command("start", "help"))
async def cmd_start_help(message: Message):
    """Обработчик команд /start и /help"""
    help_text = (
        "🎲 *Dice Roller Bot*\n\n"
        "Я помогаю бросать кубики в групповых чатах!\n\n"
        "*Доступные команды:*\n"
        "• `/roll dN` - бросить N-гранный кубик\n"
        "• `/roll XdN` - бросить X кубиков по N граней\n"
        "• `/roll dN+M` - бросить кубик с бонусом +M\n"
        "• `/roll XdN+M` - бросить X кубиков с бонусом\n\n"
        "*Примеры:*\n"
        "• `/roll d20`\n"
        "• `/roll 2d6`\n"
        "• `/roll d100+10`"
    )
    await message.reply(help_text)

@dp.message(Command("roll"))
async def cmd_roll(message: Message):
    """
    УПРОЩЕННЫЙ обработчик команды /roll
    """
    # Получаем полный текст сообщения
    full_text = message.text.strip()
    logger.info(f"Получена команда: {full_text}")
    
    # Просто проверяем, что после /roll что-то есть
    parts = full_text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.reply(
            "❌ Не указан кубик!\n"
            "Используйте: `/roll d20` или `/roll 2d6+3`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Получаем аргумент (то, что после /roll)
    roll_arg = parts[1].strip().lower()
    logger.info(f"Аргумент: {roll_arg}")
    
    # Проверяем базовый формат: должно содержать 'd' и цифры
    if 'd' not in roll_arg:
        await message.reply(
            "❌ Неправильный формат! Должно быть что-то типа `d20`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Разбираем формат
    # Вариант 1: просто d20
    if re.match(r'^d\d+$', roll_arg):
        sides = int(roll_arg[1:])
        num_dice = 1
        bonus = 0
    
    # Вариант 2: 2d20
    elif re.match(r'^\d+d\d+$', roll_arg):
        num_dice, sides = map(int, roll_arg.split('d'))
        bonus = 0
    
    # Вариант 3: d20+5
    elif re.match(r'^d\d+\+\d+$', roll_arg):
        dice_part, bonus = roll_arg.split('+')
        sides = int(dice_part[1:])
        num_dice = 1
        bonus = int(bonus)
    
    # Вариант 4: 2d20+3
    elif re.match(r'^\d+d\d+\+\d+$', roll_arg):
        dice_part, bonus = roll_arg.split('+')
        num_dice, sides = map(int, dice_part.split('d'))
        bonus = int(bonus)
    
    else:
        await message.reply(
            "❌ Не могу распознать формат. Попробуй:\n"
            "• `/roll d20`\n"
            "• `/roll 2d6`\n"
            "• `/roll d100+10`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Проверки
    if num_dice > 100:
        await message.reply("❌ Слишком много кубиков! Максимум 100")
        return
    
    if sides > 1000000:
        await message.reply("❌ Слишком большое число граней!")
        return
    
    # Бросаем кубики
    results = [random.randint(1, sides) for _ in range(num_dice)]
    total = sum(results) + bonus
    
    # Формируем ответ
    user = message.from_user
    user_name = f"@{user.username}" if user.username else user.full_name
    
    if num_dice == 1 and bonus == 0:
        response = f"🎲 *d{sides}*\n👤 {user_name}\n✨ **{results[0]}**"
    elif num_dice == 1 and bonus > 0:
        response = f"🎲 *d{sides}+{bonus}*\n👤 {user_name}\n✨ {results[0]} + {bonus} = **{total}**"
    elif num_dice > 1 and bonus == 0:
        dice_str = " + ".join(map(str, results))
        response = f"🎲 *{num_dice}d{sides}*\n👤 {user_name}\n📊 {dice_str}\n📈 **{total}**"
    else:
        dice_str = " + ".join(map(str, results))
        response = f"🎲 *{num_dice}d{sides}+{bonus}*\n👤 {user_name}\n📊 {dice_str}\n📈 Сумма: {total - bonus} + {bonus} = **{total}**"
    
    await message.reply(response)

@dp.message()
async def handle_other(message: Message):
    """Игнорируем остальные сообщения"""
    pass

async def main():
    logger.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
