import asyncio
import random
import re
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ChatMemberUpdated
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Настройка логирования (чтобы видеть ошибки)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Токен бота (ЗАМЕНИ НА СВОЙ!)
TOKEN = "8713010196:AAFrSa5-dUpuSF5qfxo7v_56JOuy8QHiH6M"

# Создаем экземпляры бота и диспетчера с правильными настройками
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()

# Регулярное выражение для разных форматов команд
# Поддерживает: /roll d20, /roll 2d20, /roll d20+5, /roll 2d20+3
ROLL_PATTERN = r'^/roll\s*(?:(\d+))?d(\d+)(?:\+(\d+))?$'

# Множество для отслеживания администраторов группы (кэш)
group_admins_cache = {}

async def is_user_admin(message: Message) -> bool:
    """
    Проверяет, является ли пользователь администратором группы
    """
    if message.chat.type not in ["group", "supergroup"]:
        return False
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Проверяем кэш
    if chat_id in group_admins_cache and user_id in group_admins_cache[chat_id]:
        return True
    
    try:
        # Получаем список администраторов
        admins = await bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in admins]
        
        # Сохраняем в кэш
        group_admins_cache[chat_id] = set(admin_ids)
        
        return user_id in admin_ids
    except Exception as e:
        logger.error(f"Ошибка при проверке прав администратора: {e}")
        return False

@dp.message(Command("start", "help"))
async def cmd_start_help(message: Message):
    """Обработчик команд /start и /help"""
    help_text = (
        "🎲 *Dice Roller Bot*\n\n"
        "Я помогаю бросать кубики в групповых чатах!\n\n"
        "*Доступные команды:*\n"
        "• `/roll dN` - бросить N-гранный кубик (N от 2 до 1,000,000)\n"
        "• `/roll XdN` - бросить X кубиков по N граней\n"
        "• `/roll dN+M` - бросить кубик с бонусом +M\n"
        "• `/roll XdN+M` - бросить X кубиков с бонусом\n"
        "• `/roll stats` - показать статистику бросков\n"
        "• `/help` - показать эту справку\n\n"
        "*Примеры:*\n"
        "• `/roll d20` - для D&D\n"
        "• `/roll 2d6` - два шестигранных кубика\n"
        "• `/roll d100+10` - процентный бросок с бонусом"
    )
    
    await message.reply(help_text)

@dp.message(Command("roll"))
async def cmd_roll(message: Message, command: CommandObject):
    """
    Обработчик команды /roll с поддержкой разных форматов
    """
    # Проверяем, является ли чат группой/супергруппой
    chat_type = message.chat.type
    
    # Логируем входящее сообщение для отладки
    logger.info(f"Получена команда /roll от {message.from_user.id} в чате {message.chat.id} ({chat_type})")
    
    # Если это группа, проверяем права бота (опционально)
    if chat_type in ["group", "supergroup"]:
        try:
            bot_member = await bot.get_chat_member(message.chat.id, bot.id)
            if bot_member.status not in ["administrator", "creator"]:
                await message.reply(
                    "⚠️ *Внимание!*\n\n"
                    "Для корректной работы в супергруппе сделайте меня администратором.\n"
                    "Это нужно, чтобы я видел все сообщения и мог отвечать всем пользователям.",
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Ошибка при проверке прав бота: {e}")
    
    # Получаем аргументы команды
    args = command.args
    if not args:
        await message.reply(
            "❌ Не указан кубик!\n"
            "Используйте: `/roll dN`\n"
            "Пример: `/roll d20`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Приводим к нижнему регистру и убираем лишние пробелы
    roll_str = args.lower().strip()
    
    # Разбираем разные форматы команд
    match = re.match(ROLL_PATTERN, roll_str)
    
    if not match:
        await message.reply(
            "❌ Неправильный формат команды!\n"
            "Примеры правильных команд:\n"
            "• `/roll d20`\n"
            "• `/roll 2d6`\n"
            "• `/roll d100+10`\n"
            "• `/roll 3d8+5`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Извлекаем параметры
    num_dice = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    bonus = int(match.group(3)) if match.group(3) else 0
    
    # Проверки валидности
    if num_dice < 1:
        await message.reply("❌ Количество кубиков должно быть хотя бы 1!")
        return
    
    if num_dice > 100:
        await message.reply("❌ Слишком много кубиков! Максимум - 100")
        return
    
    if sides < 2:
        await message.reply("❌ У кубика должно быть минимум 2 грани!")
        return
    
    if sides > 1000000:
        await message.reply("❌ Слишком большое число граней! Максимум - 1,000,000")
        return
    
    if bonus > 10000:
        await message.reply("❌ Слишком большой бонус! Максимум - 10,000")
        return
    
    # Генерируем результаты
    results = []
    total = 0
    
    for i in range(num_dice):
        roll = random.randint(1, sides)
        results.append(roll)
        total += roll
    
    # Добавляем бонус
    total_with_bonus = total + bonus
    
    # Получаем информацию об отправителе
    user = message.from_user
    user_mention = f"@{user.username}" if user.username else user.full_name
    
    # Формируем красивое сообщение с результатом
    if num_dice == 1:
        # Один кубик
        if bonus > 0:
            response = (
                f"🎲 *Бросок d{sides}* {('+' + str(bonus)) if bonus > 0 else ''}\n"
                f"👤 {user_mention}\n"
                f"✨ Результат: {results[0]}"
            )
            if bonus > 0:
                response += f" + {bonus} = **{total_with_bonus}**"
        else:
            response = (
                f"🎲 *Бросок d{sides}*\n"
                f"👤 {user_mention}\n"
                f"✨ Результат: **{results[0]}**"
            )
    else:
        # Несколько кубиков
        results_str = " + ".join(map(str, results))
        if bonus > 0:
            response = (
                f"🎲 *Бросок {num_dice}d{sides}* {('+' + str(bonus)) if bonus > 0 else ''}\n"
                f"👤 {user_mention}\n"
                f"📊 Кости: {results_str}\n"
                f"📈 Сумма: {total}"
            )
            if bonus > 0:
                response += f" + {bonus} = **{total_with_bonus}**"
        else:
            response = (
                f"🎲 *Бросок {num_dice}d{sides}*\n"
                f"👤 {user_mention}\n"
                f"📊 Кости: {results_str}\n"
                f"📈 Результат: **{total}**"
            )
    
    # Отправляем результат
    try:
        await message.reply(response)
        logger.info(f"Ответ отправлен пользователю {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа: {e}")
        # Пробуем отправить без Markdown если была ошибка
        try:
            await message.reply(
                response.replace("*", "").replace("**", ""),
                parse_mode=None
            )
        except Exception as e2:
            logger.error(f"Критическая ошибка при отправке: {e2}")

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """
    Показывает статистику бросков в группе (простая версия)
    """
    # Здесь можно хранить статистику в базе данных
    # Пока просто заглушка
    await message.reply(
        "📊 *Статистика*\n\n"
        "Функция статистики находится в разработке.\n"
        "Скоро здесь будет показываться:\n"
        "• Количество бросков\n"
        "• Средние значения\n"
        "• Самые везучие игроки",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message()
async def handle_other_messages(message: Message):
    """
    Обработчик всех остальных сообщений
    """
    # Проверяем, является ли чат группой
    if message.chat.type in ["group", "supergroup"]:
        # Здесь можно добавить какую-то логику для обычных сообщений
        # Например, реагировать на упоминания кубиков в тексте
        text = message.text or ""
        
        # Ищем упоминания кубиков в тексте (например, "кинь d20")
        if "d" in text.lower() and any(c.isdigit() for c in text):
            # Просто логируем, но не отвечаем
            logger.info(f"Найдено упоминание кубика в сообщении: {text}")

@dp.chat_member()
async def on_chat_member_update(event: ChatMemberUpdated):
    """
    Отслеживаем изменения в составе группы
    """
    # Если бота сделали админом, сбрасываем кэш для этой группы
    if event.new_chat_member.user.id == bot.id:
        if event.new_chat_member.status in ["administrator", "creator"]:
            # Очищаем кэш для этой группы
            if event.chat.id in group_admins_cache:
                del group_admins_cache[event.chat.id]
            
            # Отправляем приветственное сообщение (опционально)
            try:
                await bot.send_message(
                    event.chat.id,
                    "✅ Спасибо! Теперь я администратор и буду видеть все сообщения.\n"
                    "Используйте `/roll d20` чтобы бросить кубик!",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass

async def on_startup():
    """Действия при запуске бота"""
    logger.info("=" * 50)
    logger.info("Бот запущен и готов к работе!")
    logger.info("=" * 50)
    
    # Проверяем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"Имя бота: {bot_info.full_name}")
    logger.info(f"Username: @{bot_info.username}")
    logger.info(f"ID: {bot_info.id}")

async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("Бот останавливается...")
    await bot.session.close()

async def main():
    """Главная функция"""
    # Регистрируем функции запуска и остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запускаем бота с правильными настройками
    # allowed_updates=["message", "chat_member"] - это важно для групп!
    await dp.start_polling(
        bot,
        allowed_updates=["message", "chat_member"],
        skip_updates=True  # Пропускаем старые обновления
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
