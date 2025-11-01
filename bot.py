import os
import json
import logging
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from config import Config

# Log sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Til sozlamalari
TEXTS = {
    'uz': {
        'start': "🎉 Assalomu alaykum {name}!\n\n🤖 *BahovuddinGPT* ga xush kelibsiz!",
        'menu': "🎛️ *Asosiy Menyu*",
        'stats': "📊 *Statistika*",
        'premium': "💎 *Premium Obuna*",
        'help': "ℹ️ *Yordam - BahovuddinGPT*",
        'admin': "👑 *Admin Panel*",
        'error': "❌ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
        'limit_reached': "❌ Kunlik limit tugadi!",
        'processing': "⏳ *Javob tayyorlanmoqda...*",
        'new_chat': "🆕 *Yangi chat boshlandi!*",
        'model_changed': "✅ Model o'zgartirildi: {model}",
        'premium_advantages': "✨ *Afzalliklar:*\n• ♾ Cheksiz so'rovlar\n• 🚀 Barcha AI modellari\n• ⚡ Tezkor javoblar\n• 📊 Batafsil statistika",
        'payment_methods': "💳 *To'lov usullari:*\n🔹 Click | 🔹 Payme\n🔹 Uzumbank | 🔹 Humo",
        'contact_admin': "📞 Admin bilan bog'lanish",
        'user_info': "👤 *Foydalanuvchi ma'lumotlari*",
        'search_user': "🔍 Foydalanuvchi qidirish",
        'broadcast': "📩 Xabar yuborish",
        'region_error': "❌ Hudud cheklovi. Iltimos, VPN yordamida qayta urinib ko'ring yoki boshqa model tanlang."
    },
    'ru': {
        'start': "🎉 Здравствуйте {name}!\n\n🤖 Добро пожаловать в *BahovuddinGPT*!",
        'menu': "🎛️ *Главное Меню*",
        'stats': "📊 *Статистика*",
        'premium': "💎 *Премиум Подписка*",
        'help': "ℹ️ *Помощь - BahovuddinGPT*",
        'admin': "👑 *Админ Панель*",
        'error': "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
        'limit_reached': "❌ Дневной лимит исчерпан!",
        'processing': "⏳ *Ответ готовится...*",
        'new_chat': "🆕 *Новый чат начат!*",
        'model_changed': "✅ Модель изменена: {model}",
        'premium_advantages': "✨ *Преимущества:*\n• ♾ Неограниченные запросы\n• 🚀 Все AI модели\n• ⚡ Быстрые ответы\n• 📊 Подробная статистика",
        'payment_methods': "💳 *Способы оплаты:*\n🔹 Click | 🔹 Payme\n🔹 Uzumbank | 🔹 Humo",
        'contact_admin': "📞 Связаться с администратором",
        'user_info': "👤 *Информация о пользователе*",
        'search_user': "🔍 Поиск пользователя",
        'broadcast': "📩 Рассылка сообщений",
        'region_error': "❌ Ограничение региона. Пожалуйста, попробуйте снова с помощью VPN или выберите другую модель."
    },
    'en': {
        'start': "🎉 Hello {name}!\n\n🤖 Welcome to *BahovuddinGPT*!",
        'menu': "🎛️ *Main Menu*",
        'stats': "📊 *Statistics*",
        'premium': "💎 *Premium Subscription*",
        'help': "ℹ️ *Help - BahovuddinGPT*",
        'admin': "👑 *Admin Panel*",
        'error': "❌ An error occurred. Please try again later.",
        'limit_reached': "❌ Daily limit reached!",
        'processing': "⏳ *Preparing response...*",
        'new_chat': "🆕 *New chat started!*",
        'model_changed': "✅ Model changed: {model}",
        'premium_advantages': "✨ *Advantages:*\n• ♾ Unlimited requests\n• 🚀 All AI models\n• ⚡ Fast responses\n• 📊 Detailed statistics",
        'payment_methods': "💳 *Payment methods:*\n🔹 Click | 🔹 Payme\n🔹 Uzumbank | 🔹 Humo",
        'contact_admin': "📞 Contact administrator",
        'user_info': "👤 *User Information*",
        'search_user': "🔍 Search user",
        'broadcast': "📩 Broadcast message",
        'region_error': "❌ Region restriction. Please try again with VPN or choose another model."
    }
}

# User data management
class UserManager:
    def __init__(self):
        self.user_data_dir = "user_data"
        os.makedirs(self.user_data_dir, exist_ok=True)

    def get_user_file(self, user_id):
        return os.path.join(self.user_data_dir, f"{user_id}.json")

    def get_user_data(self, user_id):
        user_file = self.get_user_file(user_id)
        today = datetime.now().strftime("%Y-%m-%d")

        default_data = {
            "user_id": user_id,
            "username": "",
            "first_name": "",
            "last_name": "",
            "phone_number": "",
            "birth_date": "",
            "address": "",
            "email": "",
            "language": "uz",
            "is_premium": False,
            "is_admin": user_id in Config.ADMIN_IDS,
            "daily_usage": 0,
            "monthly_usage": 0,
            "total_usage": 0,
            "daily_limit": Config.FREE_DAILY_LIMIT,
            "monthly_limit": Config.FREE_MONTHLY_LIMIT,
            "current_model": Config.DEFAULT_MODEL,
            "last_reset_date": today,
            "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_activity": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "premium_until": None,
            "contact_info": {
                "phone": "",
                "email": "",
                "telegram": ""
            }
        }

        try:
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)

                # Yangi kunni tekshirish
                if user_data.get('last_reset_date') != today:
                    user_data['daily_usage'] = 0
                    user_data['last_reset_date'] = today

                # Oylik reset (har oyning 1-kuni)
                current_month = datetime.now().month
                last_activity_str = user_data.get('last_activity', today)
                if last_activity_str:
                    try:
                        last_activity_date = last_activity_str.split()[0]
                        last_activity = datetime.strptime(last_activity_date, "%Y-%m-%d")
                        if last_activity.month != current_month:
                            user_data['monthly_usage'] = 0
                    except ValueError:
                        user_data['monthly_usage'] = 0

                # Premium muddatini tekshirish
                if user_data.get('premium_until'):
                    try:
                        premium_until = datetime.strptime(user_data['premium_until'], "%Y-%m-%d")
                        if datetime.now() > premium_until:
                            user_data['is_premium'] = False
                            user_data['daily_limit'] = Config.FREE_DAILY_LIMIT
                            user_data['monthly_limit'] = Config.FREE_MONTHLY_LIMIT
                            user_data['premium_until'] = None
                    except ValueError:
                        user_data['premium_until'] = None

                # Yangi maydonlarni qo'shish
                for key, value in default_data.items():
                    if key not in user_data:
                        user_data[key] = value

                return user_data
            else:
                return default_data

        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"User data o'qishda xato: {e}")
            return default_data

    def save_user_data(self, user_data):
        try:
            user_file = self.get_user_file(user_data['user_id'])
            user_data['last_activity'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"User data saqlashda xato: {e}")
            return False

    def create_new_user(self, user, user_id):
        user_data = self.get_user_data(user_id)
        user_data.update({
            "user_id": user_id,
            "username": user.username or "",
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "is_admin": user_id in Config.ADMIN_IDS,
            "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "contact_info": {
                "telegram": f"@{user.username}" if user.username else ""
            }
        })
        self.save_user_data(user_data)
        return user_data

    def increment_usage(self, user_id):
        user_data = self.get_user_data(user_id)
        user_data['daily_usage'] += 1
        user_data['monthly_usage'] += 1
        user_data['total_usage'] += 1
        self.save_user_data(user_data)
        return user_data

    def set_premium(self, user_id, months=1):
        user_data = self.get_user_data(user_id)

        if user_data.get('premium_until'):
            try:
                current_date = datetime.strptime(user_data['premium_until'], "%Y-%m-%d")
                new_date = current_date + timedelta(days=30 * months)
            except ValueError:
                new_date = datetime.now() + timedelta(days=30 * months)
        else:
            new_date = datetime.now() + timedelta(days=30 * months)

        user_data['is_premium'] = True
        user_data['premium_until'] = new_date.strftime("%Y-%m-%d")
        user_data['daily_limit'] = Config.PREMIUM_DAILY_LIMIT
        user_data['monthly_limit'] = Config.PREMIUM_MONTHLY_LIMIT

        self.save_user_data(user_data)
        return user_data

    def remove_premium(self, user_id):
        user_data = self.get_user_data(user_id)
        user_data['is_premium'] = False
        user_data['premium_until'] = None
        user_data['daily_limit'] = Config.FREE_DAILY_LIMIT
        user_data['monthly_limit'] = Config.FREE_MONTHLY_LIMIT
        self.save_user_data(user_data)
        return user_data

    def set_language(self, user_id, language):
        user_data = self.get_user_data(user_id)
        user_data['language'] = language
        self.save_user_data(user_data)
        return user_data

    def update_contact_info(self, user_id, phone="", email="", birth_date="", address=""):
        user_data = self.get_user_data(user_id)
        if phone:
            user_data['phone_number'] = phone
            user_data['contact_info']['phone'] = phone
        if email:
            user_data['email'] = email
            user_data['contact_info']['email'] = email
        if birth_date:
            user_data['birth_date'] = birth_date
        if address:
            user_data['address'] = address

        self.save_user_data(user_data)
        return user_data

    def get_all_users(self):
        users = []
        if not os.path.exists(self.user_data_dir):
            return users

        for filename in os.listdir(self.user_data_dir):
            if filename.endswith('.json'):
                try:
                    user_id = int(filename.split('.')[0])
                    user_data = self.get_user_data(user_id)
                    if user_data:
                        users.append(user_data)
                except (ValueError, Exception) as e:
                    logger.error(f"Foydalanuvchi ma'lumotlarini o'qishda xato {filename}: {e}")
        return users

    def search_users(self, query):
        users = self.get_all_users()
        results = []
        query = query.lower()

        for user in users:
            # Ism bo'yicha qidirish
            if (query in user.get('first_name', '').lower() or
                    query in user.get('last_name', '').lower() or
                    query in user.get('username', '').lower() or
                    query in str(user.get('user_id', '')) or
                    query in user.get('phone_number', '').lower() or
                    query in user.get('email', '').lower()):
                results.append(user)

        return results


user_manager = UserManager()


# OpenRouter API with retry mechanism
class OpenRouterAPI:
    def __init__(self):
        self.api_key = Config.OPENROUTER_API_KEY
        self.api_url = Config.OPENROUTER_API_URL

    async def get_response_with_retry(self, message, model, max_retries=Config.MAX_RETRIES):
        for attempt in range(max_retries):
            try:
                response, tokens = await self.get_response(message, model)
                if "❌" not in response or attempt == max_retries - 1:
                    return response, tokens
                else:
                    logger.info(f"Qayta urinish {attempt + 1}/{max_retries}")
                    await asyncio.sleep(Config.RETRY_DELAY * (attempt + 1))
            except Exception as e:
                logger.error(f"Urinish {attempt + 1} xatosi: {e}")
                if attempt == max_retries - 1:
                    return f"❌ Xatolik: {str(e)}", 0
                await asyncio.sleep(Config.RETRY_DELAY * (attempt + 1))
        return "❌ Server xatosi. Keyinroq urinib ko'ring.", 0

    async def get_response(self, message, model):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me/BahovuddinGPTBot",
            "X-Title": "BahovuddinGPT"
        }

        model_settings = Config.MODEL_SETTINGS.get(model, {"max_tokens": 1500})

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "max_tokens": model_settings["max_tokens"],
            "temperature": 0.7,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.api_url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status == 200:
                        result = await response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            return result['choices'][0]['message']['content'], result.get('usage', {}).get(
                                'total_tokens', 0)
                        else:
                            return "❌ API javobi noto'g'ri formatda.", 0

                    elif response.status == 404:
                        return "❌ Model topilmadi. Iltimos, /model buyrug'i bilan boshqa model tanlang.", 0

                    elif response.status == 401:
                        return "❌ API kaliti noto'g'ri. Admin bilan bog'laning.", 0

                    elif response.status == 429:
                        return "❌ So'rovlar cheklovi. Iltimos, bir oz kuting va qayta urinib ko'ring.", 0

                    elif response.status == 403:
                        return get_user_text({"language": "uz"}, 'region_error'), 0

                    else:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API xatosi: {response.status} - {error_text}")
                        return f"❌ API xatosi ({response.status}). Keyinroq urinib ko'ring.", 0

        except asyncio.TimeoutError:
            return "❌ Javob kutish vaqti tugadi. Qayta urinib ko'ring.", 0
        except aiohttp.ClientError as e:
            logger.error(f"Tarmoq xatosi: {e}")
            return f"❌ Tarmoq xatosi. Qayta urinib ko'ring.", 0
        except Exception as e:
            logger.error(f"OpenRouter xatosi: {e}")
            return f"❌ Ulanish xatosi: {str(e)}", 0


openrouter_api = OpenRouterAPI()


# Conversation manager
class ConversationManager:
    def __init__(self):
        self.conversations = {}

    def get_conversation(self, user_id):
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]

    def add_message(self, user_id, role, content):
        conversation = self.get_conversation(user_id)
        conversation.append({"role": role, "content": content})

        # Faqat oxirgi 10 ta xabarni saqlash
        if len(conversation) > 10:
            self.conversations[user_id] = conversation[-10:]

    def clear_conversation(self, user_id):
        if user_id in self.conversations:
            del self.conversations[user_id]


conversation_manager = ConversationManager()


# Admin notification
async def notify_admins(context: ContextTypes.DEFAULT_TYPE, message: str):
    for admin_id in Config.ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=message)
        except Exception as e:
            logger.error(f"Adminga xabar yuborishda xato {admin_id}: {e}")


# Helper functions
def get_user_text(user_data, text_key, **kwargs):
    """Foydalanuvchi tiliga mos matn olish"""
    language = user_data.get('language', 'uz')
    text = TEXTS.get(language, {}).get(text_key, TEXTS['uz'].get(text_key, text_key))
    return text.format(**kwargs) if kwargs else text


async def send_safe_message(update, text, reply_markup=None, parse_mode='Markdown'):
    """Xavfsiz xabar yuborish funksiyasi"""
    try:
        if update.message:
            return await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
        else:
            return await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
    except Exception as e:
        logger.error(f"Xabar yuborishda xato: {e}")
        # Formatlashsiz qayta urinib ko'rish
        safe_text = text.replace('*', '').replace('_', '').replace('`', '')
        try:
            if update.message:
                return await update.message.reply_text(
                    safe_text,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            else:
                return await update.callback_query.edit_message_text(
                    safe_text,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
        except Exception as e2:
            logger.error(f"Xabar yuborishda ikkinchi xato: {e2}")


async def get_detailed_user_info(user_data):
    """Foydalanuvchi to'liq ma'lumotlari"""
    user_id = user_data.get('user_id', 'Noma lum')
    username = user_data.get('username', 'Noma lum')
    first_name = user_data.get('first_name', 'Noma lum')
    last_name = user_data.get('last_name', '')
    language = user_data.get('language', 'uz')
    is_premium = user_data.get('is_premium', False)
    is_admin = user_data.get('is_admin', False)

    # Kontakt ma'lumotlari
    phone_number = user_data.get('phone_number', 'Kiritilmagan')
    email = user_data.get('email', 'Kiritilmagan')
    birth_date = user_data.get('birth_date', 'Kiritilmagan')
    address = user_data.get('address', 'Kiritilmagan')

    # Statistik ma'lumotlar
    daily_usage = user_data.get('daily_usage', 0)
    monthly_usage = user_data.get('monthly_usage', 0)
    total_usage = user_data.get('total_usage', 0)
    daily_limit = user_data.get('daily_limit', Config.FREE_DAILY_LIMIT)
    monthly_limit = user_data.get('monthly_limit', Config.FREE_MONTHLY_LIMIT)

    # Model va sozlamalar
    current_model = user_data.get('current_model', Config.DEFAULT_MODEL)
    model_name = Config.AI_MODELS.get(current_model, current_model)

    # Vaqt ma'lumotlari
    registration_date = user_data.get('registration_date', 'Noma lum')
    last_activity = user_data.get('last_activity', 'Noma lum')
    premium_until = user_data.get('premium_until', 'Yo\'q')
    last_reset_date = user_data.get('last_reset_date', 'Noma lum')

    # Statuslar
    status = "💎 PREMIUM" if is_premium else "🆓 BEPUL"
    admin_status = "👑 ADMIN" if is_admin else "👤 USER"

    # Faollik darajasi
    activity_level = "⚫ Ma'lumot yo'q"
    if last_activity != 'Noma lum':
        try:
            last_active = datetime.strptime(last_activity.split()[0], "%Y-%m-%d")
            days_inactive = (datetime.now() - last_active).days
            activity_level = "🟢 Faol" if days_inactive == 0 else "🟡 Kam faol" if days_inactive <= 7 else "🔴 No faol"
        except ValueError:
            activity_level = "⚫ Ma'lumot yo'q"

    user_info = f"""👤 *FOYDALANUVCHI MA'LUMOTLARI*

🆔 *ID:* `{user_id}`
👤 *Ism:* {first_name} {last_name}
📱 *Username:* @{username}
🌐 *Til:* {language.upper()}

📞 *Telefon:* {phone_number}
📧 *Email:* {email}
🎂 *Tug'ilgan sana:* {birth_date}
📍 *Manzil:* {address}

📊 *STATUS:*
{status} | {admin_status}
{activity_level}

📈 *STATISTIKA:*
• 📅 Kunlik: {daily_usage}/{daily_limit}
• 📈 Oylik: {monthly_usage}/{monthly_limit}
• 🎯 Jami: {total_usage} so'rov
• 🤖 Model: {model_name}

🕐 *VAQT MA'LUMOTLARI:*
• 📝 Ro'yxatdan: {registration_date}
• ⏰ So'nggi faollik: {last_activity}
• 🔄 So'nggi reset: {last_reset_date}
• 💎 Premium tugashi: {premium_until}"""

    return user_info


# ==============================
# ASOSIY COMMANDLAR
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = user_manager.get_user_data(user.id)

    # Yangi foydalanuvchi
    if not user_data.get('username') or user_data.get('username') != user.username:
        user_data = user_manager.create_new_user(user, user.id)
        new_user_msg = f"""🆕 *Yangi foydalanuvchi:*
👤 Ism: {user.first_name}
📱 Username: @{user.username}
🆔 ID: {user.id}
📅 Ro'yxatdan: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 Til: O'zbek"""
        await notify_admins(context, new_user_msg)

    # Til tanlash keyboard
    keyboard = [
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = f"""🎉 Assalomu alaykum {user.first_name}!

🤖 *BahovuddinGPT* ga xush kelibsiz!
Iltimos, tilni tanlang:

Please choose your language:

Пожалуйста, выберите язык:"""

    await send_safe_message(update, welcome_text, reply_markup)


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE, language):
    user = update.effective_user
    user_data = user_manager.set_language(user.id, language)

    # Asosiy menyu
    keyboard = [
        [InlineKeyboardButton("🤖 AI dan Savol Ber", callback_data="ask_ai")],
        [InlineKeyboardButton("🔄 Model Tanlash", callback_data="show_models")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats"),
         InlineKeyboardButton("💎 Premium", callback_data="premium")],
        [InlineKeyboardButton("🌐 Til", callback_data="change_lang"),
         InlineKeyboardButton("🆕 Yangi Chat", callback_data="new_chat")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]

    if user_data['is_admin']:
        keyboard.append([InlineKeyboardButton("👑 Admin", callback_data="admin")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = get_user_text(user_data, 'start', name=user.first_name)
    welcome_text += f"""

💡 *{get_user_text(user_data, 'menu')}* 
Quyidagi menyudan tanlang yoki to'g'ridan-to'g'ri savolingizni yuboring!

📊 *Sizning holatingiz:*
{'💎 Premium' if user_data['is_premium'] else '🆓 Bepul'} • 🤖 {Config.AI_MODELS.get(user_data['current_model'], user_data['current_model'])}
📈 Bugun: {user_data['daily_usage']}/{user_data['daily_limit']}"""

    await send_safe_message(update, welcome_text, reply_markup)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = user_manager.get_user_data(user.id)

    keyboard = [
        [InlineKeyboardButton("🤖 AI dan Savol Ber", callback_data="ask_ai")],
        [InlineKeyboardButton("🔄 Model Tanlash", callback_data="show_models")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats"),
         InlineKeyboardButton("💎 Premium", callback_data="premium")],
        [InlineKeyboardButton("🌐 Til", callback_data="change_lang"),
         InlineKeyboardButton("🆕 Yangi Chat", callback_data="new_chat")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]

    if user_data['is_admin']:
        keyboard.append([InlineKeyboardButton("👑 Admin", callback_data="admin")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_safe_message(update, get_user_text(user_data, 'menu'), reply_markup)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = user_manager.get_user_data(user.id)

    status = "💎 PREMIUM" if user_data['is_premium'] else "🆓 BEPUL"
    premium_info = f"\n⭐ Premium muddati: {user_data['premium_until']}" if user_data['premium_until'] else ""

    stats_text = f"""📊 *{get_user_text(user_data, 'stats')}*

{status}{premium_info}

📅 *Kunlik:* {user_data['daily_usage']}/{user_data['daily_limit']}
📈 *Oylik:* {user_data['monthly_usage']}/{user_data['monthly_limit']}
🎯 *Jami:* {user_data['total_usage']}

🤖 *Model:* {Config.AI_MODELS.get(user_data['current_model'], user_data['current_model'])}
📝 *Ro'yxatdan:* {user_data['registration_date'].split()[0]}
🌐 *Til:* {user_data.get('language', 'uz').upper()}"""

    keyboard = [
        [InlineKeyboardButton("🔄 Model Tanlash", callback_data="show_models")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_safe_message(update, stats_text, reply_markup)


async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = user_manager.get_user_data(user.id)

    keyboard = [
        [InlineKeyboardButton("1 oy - 50,000 so'm", callback_data="premium_1oy")],
        [InlineKeyboardButton("3 oy - 120,000 so'm", callback_data="premium_3oy")],
        [InlineKeyboardButton("6 oy - 200,000 so'm", callback_data="premium_6oy")],
        [InlineKeyboardButton("12 oy - 350,000 so'm", callback_data="premium_12oy")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    premium_text = f"""💎 *{get_user_text(user_data, 'premium')}*

{get_user_text(user_data, 'premium_advantages')}

{get_user_text(user_data, 'payment_methods')}

⬇️ Obuna muddatini tanlang:"""

    await send_safe_message(update, premium_text, reply_markup)


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = user_manager.get_user_data(user.id)

    available_models = Config.PREMIUM_MODELS if user_data['is_premium'] else Config.FREE_MODELS
    current_model = user_data['current_model']

    keyboard = []
    for model_id in available_models:
        model_name = Config.AI_MODELS.get(model_id, model_id)
        prefix = "✅" if model_id == current_model else "🔘"
        keyboard.append([InlineKeyboardButton(f"{prefix} {model_name}", callback_data=f"model_{model_id}")])

    keyboard.append([InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    status = "💎 Premium" if user_data['is_premium'] else "🆓 Bepul"

    message_text = f"🤖 *Modelni tanlang* ({status})\n💡 Hozirgi: {Config.AI_MODELS.get(current_model, current_model)}"

    await send_safe_message(update, message_text, reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = user_manager.get_user_data(user.id)

    help_text = f"""ℹ️ *{get_user_text(user_data, 'help')}*

🎯 *Qanday ishlatish:*
1. To'g'ridan-to'g'ri savol yuboring
2. Men sizga AI orqali javob beraman

📋 *Buyruqlar:*
/start - Botni ishga tushirish
/menu - Asosiy menyu
/stats - Statistika
/model - Modelni o'zgartirish
/premium - Premium obuna
/help - Yordam
/newchat - Yangi chat boshlash
/language - Tilni o'zgartirish

💡 *Maslahatlar:*
• Savollaringiz aniq va tushunarli bo'lsin
• Har bir yangi suhbat yangi kontekstda boshlanadi
• Limitlaringizni /stats buyrug'i orqali tekshiring

🚀 *Tezkor javoblar uchun GPT-3.5 modelini tavsiya qilamiz!*"""

    keyboard = [
        [InlineKeyboardButton("🤖 Savol Berish", callback_data="ask_ai")],
        [InlineKeyboardButton("🌐 Tilni o'zgartirish", callback_data="change_lang")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_safe_message(update, help_text, reply_markup)


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = """🌐 *Tilni tanlang / Choose language / Выберите язык:*

🇺🇿 O'zbek tili
🇷🇺 Русский язык  
🇺🇸 English language"""

    await send_safe_message(update, text, reply_markup)


async def newchat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = user_manager.get_user_data(user.id)
    conversation_manager.clear_conversation(user.id)

    await send_safe_message(update, f"🆕 *{get_user_text(user_data, 'new_chat')}*\n\nAvvalgi suhbat tarixi tozalandi.")


# ==============================
# ADMIN COMMANDLAR
# ==============================

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        if update.message:
            await update.message.reply_text("❌ Bu buyruq faqat adminlar uchun!")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton("🔍 Foydalanuvchi qidirish", callback_data="admin_search")],
        [InlineKeyboardButton("💎 Premium Boshqaruv", callback_data="admin_premium")],
        [InlineKeyboardButton("📩 Xabar yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_safe_message(update, get_user_text(user_manager.get_user_data(user.id), 'admin'), reply_markup)


async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    users = user_manager.get_all_users()
    total_users = len(users)
    premium_users = len([u for u in users if u.get('is_premium', False)])

    # Bugun faol foydalanuvchilar
    today = datetime.now().strftime("%Y-%m-%d")
    active_today = len([u for u in users if u.get('last_activity', '').startswith(today)])

    total_usage = sum(u.get('total_usage', 0) for u in users)

    # Til statistikasi
    lang_stats = {}
    for u in users:
        lang = u.get('language', 'uz')
        lang_stats[lang] = lang_stats.get(lang, 0) + 1

    stats_text = f"""📈 *Admin Statistika*

👥 *Foydalanuvchilar:*
• Jami: {total_users}
• Premium: {premium_users}
• Bepul: {total_users - premium_users}
• Bugun faol: {active_today}

🌐 *Tillar:*
• O'zbek: {lang_stats.get('uz', 0)}
• Русский: {lang_stats.get('ru', 0)}
• English: {lang_stats.get('en', 0)}

📊 *Faollik:*
• Jami so'rovlar: {total_usage}
• O'rtacha: {total_usage // max(1, total_users)} so'rov/foydalanuvchi

🕐 *Server:*
• Vaqt: {datetime.now().strftime('%H:%M:%S')}
• Sana: {datetime.now().strftime('%Y-%m-%d')}"""

    keyboard = [
        [InlineKeyboardButton("📊 Boshqa statistikalar", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_safe_message(update, stats_text, reply_markup)


async def admin_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    users = user_manager.get_all_users()
    recent_users = sorted(users, key=lambda x: x.get('last_activity', ''), reverse=True)[:20]

    users_text = "👥 *So'nggi 20 foydalanuvchi:*\n\n"
    for i, user_data in enumerate(recent_users, 1):
        username = user_data.get('username', 'Noma lum')
        first_name = user_data.get('first_name', '')
        user_id = user_data.get('user_id', '')
        premium = "💎" if user_data.get('is_premium') else "🆓"
        lang = user_data.get('language', 'uz').upper()
        last_active = user_data.get('last_activity', '').split()[0] if user_data.get('last_activity') else 'Noma lum'

        users_text += f"{i}. {first_name} (@{username}) {premium} [{lang}]\n"
        users_text += f"   🆔 {user_id} | 📅 {last_active}\n"
        users_text += f"   📊 {user_data.get('total_usage', 0)} so'rov\n"
        users_text += f"   [👁 Ma'lumot](userinfo_{user_id}) | [💎 Premium](premium_{user_id}_1)\n\n"

    keyboard = [
        [InlineKeyboardButton("🔍 Foydalanuvchi qidirish", callback_data="admin_search")],
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_safe_message(update, users_text, reply_markup)


async def admin_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    keyboard = [
        [InlineKeyboardButton("🔍 ID bo'yicha qidirish", callback_data="search_by_id")],
        [InlineKeyboardButton("👤 Ism bo'yicha qidirish", callback_data="search_by_name")],
        [InlineKeyboardButton("📞 Telefon bo'yicha", callback_data="search_by_phone")],
        [InlineKeyboardButton("💎 Premium foydalanuvchilar", callback_data="search_premium")],
        [InlineKeyboardButton("📈 Faol foydalanuvchilar", callback_data="search_active")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_safe_message(update, "🔍 *Foydalanuvchi qidirish*", reply_markup)


async def search_by_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    await send_safe_message(update,
                            "🔍 *ID bo'yicha qidirish*\n\n"
                            "Foydalanuvchi ID sini yuboring:\n"
                            "Misol: `/user_info 123456789`",
                            parse_mode='Markdown'
                            )


async def user_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "❌ *Foydalanish:* `/user_info user_id`\n"
            "Misol: `/user_info 123456789`",
            parse_mode='Markdown'
        )
        return

    try:
        target_user_id = int(context.args[0])
        user_data = user_manager.get_user_data(target_user_id)

        if not user_data.get('username'):
            await update.message.reply_text("❌ Foydalanuvchi topilmadi!")
            return

        # Foydalanuvchi to'liq ma'lumotlari
        user_info_text = await get_detailed_user_info(user_data)

        # Harakatlar tugmalari
        keyboard = [
            [InlineKeyboardButton("💎 Premium berish", callback_data=f"premium_{target_user_id}_1"),
             InlineKeyboardButton("❌ Premium olib tashlash", callback_data=f"remove_premium_{target_user_id}")],
            [InlineKeyboardButton("📩 Xabar yuborish", callback_data=f"message_{target_user_id}")],
            [InlineKeyboardButton("🔄 Yangilash", callback_data=f"refresh_{target_user_id}")],
            [InlineKeyboardButton("🔍 Boshqa qidiruv", callback_data="admin_search"),
             InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(user_info_text, reply_markup=reply_markup, parse_mode='Markdown')

    except ValueError:
        await update.message.reply_text("❌ User ID raqam bo'lishi kerak!")
    except Exception as e:
        logger.error(f"User info olishda xato: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi!")


async def search_by_name_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    await send_safe_message(update,
                            "👤 *Ism bo'yicha qidirish*\n\n"
                            "Foydalanuvchi ismini yuboring:\n"
                            "Misol: `/search_name Aziz`",
                            parse_mode='Markdown'
                            )


async def search_name_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "❌ *Foydalanish:* `/search_name ism`\n"
            "Misol: `/search_name Aziz`",
            parse_mode='Markdown'
        )
        return

    search_query = ' '.join(context.args)
    results = user_manager.search_users(search_query)

    if not results:
        await update.message.reply_text(f"❌ '{search_query}' bo'yicha foydalanuvchi topilmadi!")
        return

    results_text = f"🔍 *Qidiruv natijalari:* '{search_query}'\n\n"
    for i, user_data in enumerate(results[:10], 1):
        first_name = user_data.get('first_name', 'Noma lum')
        username = user_data.get('username', 'Noma lum')
        user_id = user_data.get('user_id', '')
        premium = "💎" if user_data.get('is_premium') else "🆓"
        phone = user_data.get('phone_number', 'Yo\'q')

        results_text += f"{i}. {first_name} (@{username}) {premium}\n"
        results_text += f"   🆔 {user_id} | 📞 {phone}\n"
        results_text += f"   📊 {user_data.get('total_usage', 0)} so'rov\n"
        results_text += f"   [👁 Ma'lumot](userinfo_{user_id})\n\n"

    if len(results) > 10:
        results_text += f"\n... va yana {len(results) - 10} ta foydalanuvchi"

    keyboard = [
        [InlineKeyboardButton("🔍 Boshqa qidiruv", callback_data="admin_search")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(results_text, reply_markup=reply_markup, parse_mode='Markdown',
                                    disable_web_page_preview=True)


async def search_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    users = user_manager.get_all_users()
    premium_users = [u for u in users if u.get('is_premium', False)]

    if not premium_users:
        await send_safe_message(update, "💎 Premium foydalanuvchilar topilmadi!")
        return

    premium_users_sorted = sorted(premium_users,
                                  key=lambda x: datetime.strptime(x.get('premium_until', '2000-01-01'), "%Y-%m-%d")
                                  if x.get('premium_until') else datetime.min, reverse=True)

    premium_text = "💎 *PREMIUM FOYDALANUVCHILAR*\n\n"
    for i, user_data in enumerate(premium_users_sorted[:15], 1):
        first_name = user_data.get('first_name', 'Noma lum')
        username = user_data.get('username', 'Noma lum')
        user_id = user_data.get('user_id', '')
        premium_until = user_data.get('premium_until', 'Noma lum')
        total_usage = user_data.get('total_usage', 0)
        phone = user_data.get('phone_number', 'Yo\'q')

        try:
            premium_end = datetime.strptime(premium_until, "%Y-%m-%d")
            days_left = (premium_end - datetime.now()).days
            days_info = f" ({days_left} kun qoldi)" if days_left > 0 else " (Muddati tugagan)"
        except:
            days_info = ""

        premium_text += f"{i}. {first_name} (@{username})\n"
        premium_text += f"   🆔 {user_id} | 📞 {phone}\n"
        premium_text += f"   📊 {total_usage} so'rov\n"
        premium_text += f"   ⭐ {premium_until}{days_info}\n"
        premium_text += f"   [👁 Ma'lumot](userinfo_{user_id})\n\n"

    if len(premium_users) > 15:
        premium_text += f"\n... va yana {len(premium_users) - 15} ta premium foydalanuvchi"

    keyboard = [
        [InlineKeyboardButton("📊 Umumiy statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("🔍 Boshqa qidiruv", callback_data="admin_search")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_safe_message(update, premium_text, reply_markup)


async def admin_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    keyboard = [
        [InlineKeyboardButton("📢 Barcha foydalanuvchilar", callback_data="broadcast_all")],
        [InlineKeyboardButton("💎 Premium foydalanuvchilar", callback_data="broadcast_premium")],
        [InlineKeyboardButton("🆓 Bepul foydalanuvchilar", callback_data="broadcast_free")],
        [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_safe_message(update, "📩 *Xabar yuborish* - Kimga xabar yubormoqchisiz?", reply_markup)


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "❌ *Foydalanish:* `/broadcast xabar matni`",
            parse_mode='Markdown'
        )
        return

    message_text = ' '.join(context.args)
    users = user_manager.get_all_users()

    sent_count = 0
    failed_count = 0

    progress_msg = await update.message.reply_text(f"📤 Xabar yuborilmoqda... 0/{len(users)}")

    for user_data in users:
        try:
            await context.bot.send_message(
                chat_id=user_data['user_id'],
                text=f"📢 *Admin xabari:*\n\n{message_text}\n\n— BahovuddinGPT jamoasi",
                parse_mode='Markdown'
            )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            logger.error(f"Xabar yuborishda xato {user_data['user_id']}: {e}")

        # Har 10 ta xabardan so'ng progress yangilash
        if sent_count % 10 == 0:
            await progress_msg.edit_text(f"📤 Xabar yuborilmoqda... {sent_count}/{len(users)}")

    await progress_msg.edit_text(
        f"✅ *Xabar yuborish yakunlandi!*\n\n"
        f"📤 Yuborildi: {sent_count} ta\n"
        f"❌ Xatolik: {failed_count} ta\n"
        f"👥 Jami: {len(users)} ta"
    )


async def broadcast_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "❌ *Foydalanish:* `/broadcast_premium xabar matni`",
            parse_mode='Markdown'
        )
        return

    message_text = ' '.join(context.args)
    users = user_manager.get_all_users()
    premium_users = [u for u in users if u.get('is_premium', False)]

    if not premium_users:
        await update.message.reply_text("❌ Premium foydalanuvchilar topilmadi!")
        return

    sent_count = 0
    failed_count = 0

    progress_msg = await update.message.reply_text(f"📤 Premium foydalanuvchilarga xabar yuborilmoqda... 0/{len(premium_users)}")

    for user_data in premium_users:
        try:
            await context.bot.send_message(
                chat_id=user_data['user_id'],
                text=f"💎 *Premium xabari:*\n\n{message_text}\n\n— BahovuddinGPT jamoasi",
                parse_mode='Markdown'
            )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            logger.error(f"Xabar yuborishda xato {user_data['user_id']}: {e}")

        # Har 10 ta xabardan so'ng progress yangilash
        if sent_count % 10 == 0:
            await progress_msg.edit_text(f"📤 Premium foydalanuvchilarga xabar yuborilmoqda... {sent_count}/{len(premium_users)}")

    await progress_msg.edit_text(
        f"✅ *Premium xabar yuborish yakunlandi!*\n\n"
        f"📤 Yuborildi: {sent_count} ta\n"
        f"❌ Xatolik: {failed_count} ta\n"
        f"💎 Jami premium: {len(premium_users)} ta"
    )


async def premium_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ *Foydalanish:* /premium_user user_id oylar\n"
            "Misol: /premium_user 123456789 3"
        )
        return

    try:
        target_user_id = int(context.args[0])
        months = int(context.args[1])

        if months <= 0:
            await update.message.reply_text("❌ Oylar soni musbat bo'lishi kerak!")
            return

        user_data = user_manager.set_premium(target_user_id, months)

        # Foydalanuvchiga xabar yuborish
        try:
            target_user_data = user_manager.get_user_data(target_user_id)
            premium_text = get_user_text(target_user_data, 'premium')
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 Tabriklayman! Sizga {months} oy {premium_text} berildi!\n"
                     f"⭐ Premium muddati: {user_data['premium_until']}\n\n"
                     f"Endi barcha modellardan foydalanishingiz va cheksiz so'rov yuborishingiz mumkin!"
            )
        except Exception as e:
            logger.error(f"Foydalanuvchiga premium xabar yuborishda xato: {e}")

        await update.message.reply_text(
            f"✅ *Premium berildi!*\n"
            f"👤 Foydalanuvchi: {target_user_id}\n"
            f"📅 Muddat: {months} oy\n"
            f"⭐ Tugash: {user_data['premium_until']}",
            parse_mode='Markdown'
        )

    except ValueError:
        await update.message.reply_text("❌ User ID va oylar soni raqam bo'lishi kerak!")
    except Exception as e:
        logger.error(f"Premium berishda xato: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi!")


async def remove_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "❌ *Foydalanish:* /remove_premium user_id\n"
            "Misol: /remove_premium 123456789"
        )
        return

    try:
        target_user_id = int(context.args[0])
        user_data = user_manager.remove_premium(target_user_id)

        # Foydalanuvchiga xabar yuborish
        try:
            target_user_data = user_manager.get_user_data(target_user_id)
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"ℹ️ *Premium obuna bekor qilindi!*\n\n"
                     f"Sizning premium obunangiz admin tomonidan bekor qilindi.\n"
                     f"Endi siz bepul tarifda foydalanasiz."
            )
        except Exception as e:
            logger.error(f"Foydalanuvchiga premium bekor qilish xabarini yuborishda xato: {e}")

        await update.message.reply_text(
            f"✅ *Premium obuna bekor qilindi!*\n"
            f"👤 Foydalanuvchi: {target_user_id}\n"
            f"📊 Yangi holat: Bepul",
            parse_mode='Markdown'
        )

    except ValueError:
        await update.message.reply_text("❌ User ID raqam bo'lishi kerak!")
    except Exception as e:
        logger.error(f"Premium olib tashlashda xato: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi!")


# ==============================
# MESSAGE HANDLER
# ==============================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text

    # Command emasligini tekshirish
    if message_text.startswith('/'):
        return

    user_data = user_manager.get_user_data(user.id)

    # Agar til tanlanmagan bo'lsa
    if not user_data.get('language'):
        await language_command(update, context)
        return

    # Limitlarni tekshirish
    if not user_data['is_premium']:
        if user_data['daily_usage'] >= user_data['daily_limit']:
            await update.message.reply_text(
                f"❌ {get_user_text(user_data, 'limit_reached')}\n"
                f"📊 {user_data['daily_usage']}/{user_data['daily_limit']}\n\n"
                f"💎 Cheksiz foydalanish uchun premium obuna sotib oling!\n"
                f"Yoki ertaga qayta urinib ko'ring."
            )
            return

        if user_data['monthly_usage'] >= user_data['monthly_limit']:
            await update.message.reply_text(
                f"❌ Oylik limit tugadi!\n"
                f"📈 {user_data['monthly_usage']}/{user_data['monthly_limit']}\n\n"
                f"💎 Keyingi oyda qayta tiklanadi yoki premium sotib oling!"
            )
            return

    # Modelni tekshirish
    available_models = Config.PREMIUM_MODELS if user_data['is_premium'] else Config.FREE_MODELS
    if user_data['current_model'] not in available_models:
        user_data['current_model'] = Config.DEFAULT_MODEL
        user_manager.save_user_data(user_data)

    # Typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Progress message
        progress_msg = await update.message.reply_text(get_user_text(user_data, 'processing'), parse_mode='Markdown')

        # AI response with retry
        response, tokens_used = await openrouter_api.get_response_with_retry(message_text, user_data['current_model'])

        # Progress messageni o'chirish
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=progress_msg.message_id
            )
        except Exception as e:
            logger.error(f"Progress messageni o'chirishda xato: {e}")

        # Foydalanish hisobini oshirish
        user_data = user_manager.increment_usage(user.id)

        # Javobni yuborish
        status = "💎" if user_data['is_premium'] else "🆓"
        model_name = Config.AI_MODELS.get(user_data['current_model'], "AI")

        response_text = f"{response}\n\n---\n{status} {model_name} | 📊 {user_data['daily_usage']}/{user_data['daily_limit']} | 🌐 {user_data.get('language', 'uz').upper()}"

        # Agar javob uzun bo'lsa, bo'laklarga bo'lish
        if len(response_text) > 4096:
            for i in range(0, len(response_text), 4096):
                part = response_text[i:i + 4096]
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(response_text)

    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await update.message.reply_text(get_user_text(user_data, 'error'))


# ==============================
# BUTTON HANDLER
# ==============================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "menu":
        await menu_command(update, context)

    elif data == "ask_ai":
        user_data = user_manager.get_user_data(user_id)
        if not user_data.get('language'):
            await language_command(update, context)
            return

        await query.edit_message_text(
            "💬 Savolingizni yuboring!\n\n"
            "Men sizga AI yordamida javob berishga harakat qilaman."
        )

    elif data == "show_models":
        await model_command(update, context)

    elif data == "stats":
        await stats_command(update, context)

    elif data == "premium":
        await premium_command(update, context)

    elif data == "help":
        await help_command(update, context)

    elif data == "new_chat":
        await newchat_command(update, context)

    elif data == "change_lang":
        await language_command(update, context)

    elif data == "admin":
        await admin_command(update, context)

    elif data == "admin_stats":
        await admin_stats_command(update, context)

    elif data == "admin_users":
        await admin_users_command(update, context)

    elif data == "admin_search":
        await admin_search_command(update, context)

    elif data == "admin_premium":
        keyboard = [
            [InlineKeyboardButton("💎 Premium berish", callback_data="admin_give_premium")],
            [InlineKeyboardButton("❌ Premium olib tashlash", callback_data="admin_remove_premium")],
            [InlineKeyboardButton("📊 Premium statistikasi", callback_data="search_premium")],
            [InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💎 *Premium Boshqaruv* - Kerakli amalni tanlang:", reply_markup=reply_markup)

    elif data == "admin_give_premium":
        await query.edit_message_text(
            "💎 *Premium berish:*\n\n"
            "Foydalanuvchi ID sini yuboring:\n"
            "`/premium_user user_id months`\n\n"
            "Misol: `/premium_user 123456789 3`",
            parse_mode='Markdown'
        )

    elif data == "admin_remove_premium":
        await query.edit_message_text(
            "❌ *Premium olib tashlash:*\n\n"
            "Foydalanuvchi ID sini yuboring:\n"
            "`/remove_premium user_id`\n\n"
            "Misol: `/remove_premium 123456789`",
            parse_mode='Markdown'
        )

    elif data == "admin_broadcast":
        await admin_broadcast_command(update, context)

    elif data == "broadcast_all":
        await query.edit_message_text(
            "📢 *Barcha foydalanuvchilarga xabar yuborish:*\n\n"
            "Xabar matnini yuboring:\n"
            "`/broadcast xabar matni`\n\n"
            "Misol: `/broadcast Salom! Yangi yangilik...`",
            parse_mode='Markdown'
        )

    elif data == "broadcast_premium":
        await query.edit_message_text(
            "💎 *Premium foydalanuvchilarga xabar yuborish:*\n\n"
            "Xabar matnini yuboring:\n"
            "`/broadcast_premium xabar matni`\n\n"
            "Misol: `/broadcast_premium Premium yangiliklari...`",
            parse_mode='Markdown'
        )

    elif data == "broadcast_free":
        await query.edit_message_text(
            "🆓 *Bepul foydalanuvchilarga xabar yuborish:*\n\n"
            "Xabar matnini yuboring:\n"
            "`/broadcast_free xabar matni`\n\n"
            "Misol: `/broadcast_free Bepul foydalanuvchilar uchun yangilik...`",
            parse_mode='Markdown'
        )

    elif data == "search_by_id":
        await search_by_id_command(update, context)

    elif data == "search_by_name":
        await search_by_name_command(update, context)

    elif data == "search_premium":
        await search_premium_command(update, context)

    elif data == "search_active":
        users = user_manager.get_all_users()
        today = datetime.now().strftime("%Y-%m-%d")
        active_today = [u for u in users if u.get('last_activity', '').startswith(today)]

        active_text = f"📈 *Bugun faol foydalanuvchilar:* {len(active_today)} ta\n\n"
        for i, user_data in enumerate(active_today[:10], 1):
            first_name = user_data.get('first_name', 'Noma lum')
            username = user_data.get('username', 'Noma lum')
            user_id = user_data.get('user_id', '')

            active_text += f"{i}. {first_name} (@{username})\n"
            active_text += f"   🆔 {user_id} | [👁 Ma'lumot](userinfo_{user_id})\n\n"

        if len(active_today) > 10:
            active_text += f"... va yana {len(active_today) - 10} ta"

        await query.edit_message_text(active_text, parse_mode='Markdown')

    elif data.startswith("lang_"):
        language = data.replace("lang_", "")
        await set_language(update, context, language)

    elif data.startswith("model_"):
        model_id = data.replace("model_", "")
        user_data = user_manager.get_user_data(user_id)

        # Model mavjudligini tekshirish
        available_models = Config.PREMIUM_MODELS if user_data['is_premium'] else Config.FREE_MODELS
        if model_id not in available_models:
            await query.edit_message_text(
                "❌ Bu model faqat premium foydalanuvchilar uchun!\n\n"
                "💎 Premium sotib olish uchun /premium buyrug'ini ishlating."
            )
            return

        user_data['current_model'] = model_id
        user_manager.save_user_data(user_data)

        model_name = Config.AI_MODELS.get(model_id, model_id)
        await query.edit_message_text(get_user_text(user_data, 'model_changed', model=model_name))

    elif data.startswith("premium_"):
        if data.count("_") == 1:
            # Premium obuna sotib olish
            period = data.replace("premium_", "")
            amount = Config.PAYMENT_AMOUNTS.get(period, 0)

            payment_text = f"""💎 Premium obuna - {period}

💰 Narx: {amount:,} so'm

📞 To'lov uchun admin bilan bog'laning:
@BahovuddinAdmin

📲 Telefon: +998 90 123 45 67

💬 To'lov qilgach, adminga chek screenshot'ini yuboring."""

            await query.edit_message_text(payment_text)

            # Adminlarga bildirish
            user = query.from_user
            payment_notify = f"""💳 Yangi to'lov so'rovi:
👤 {user.first_name} (@{user.username})
🆔 {user.id}
📞 Telefon: +998 90 123 45 67
💰 {period} - {amount:,} so'm
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            await notify_admins(context, payment_notify)
        else:
            # Admin tomonidan premium berish
            parts = data.split("_")
            if len(parts) == 3:
                target_user_id = int(parts[1])
                months = int(parts[2])
                user_data = user_manager.set_premium(target_user_id, months)

                await query.edit_message_text(
                    f"✅ Premium berildi!\n"
                    f"👤 Foydalanuvchi: {target_user_id}\n"
                    f"⭐ Muddat: {months} oy\n"
                    f"📅 Tugash: {user_data['premium_until']}"
                )

    elif data.startswith("remove_premium_"):
        target_user_id = int(data.replace("remove_premium_", ""))
        user_data = user_manager.remove_premium(target_user_id)

        await query.edit_message_text(
            f"✅ Premium olib tashlandi!\n"
            f"👤 Foydalanuvchi: {target_user_id}\n"
            f"📊 Yangi holat: Bepul"
        )

    elif data.startswith("message_"):
        target_user_id = int(data.replace("message_", ""))
        await query.edit_message_text(
            f"📩 Foydalanuvchiga xabar yuborish:\n"
            f"👤 Foydalanuvchi ID: {target_user_id}\n\n"
            f"Xabar matnini yuboring:"
        )
        context.user_data['awaiting_message'] = target_user_id

    elif data.startswith("refresh_"):
        target_user_id = int(data.replace("refresh_", ""))
        user_data = user_manager.get_user_data(target_user_id)
        user_info_text = await get_detailed_user_info(user_data)

        keyboard = [
            [InlineKeyboardButton("💎 Premium berish", callback_data=f"premium_{target_user_id}_1"),
             InlineKeyboardButton("❌ Premium olib tashlash", callback_data=f"remove_premium_{target_user_id}")],
            [InlineKeyboardButton("📩 Xabar yuborish", callback_data=f"message_{target_user_id}")],
            [InlineKeyboardButton("🔄 Yangilash", callback_data=f"refresh_{target_user_id}")],
            [InlineKeyboardButton("🔍 Boshqa qidiruv", callback_data="admin_search"),
             InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(user_info_text, reply_markup=reply_markup, parse_mode='Markdown')

    elif data.startswith("userinfo_"):
        target_user_id = int(data.replace("userinfo_", ""))
        user_data = user_manager.get_user_data(target_user_id)
        user_info_text = await get_detailed_user_info(user_data)

        keyboard = [
            [InlineKeyboardButton("💎 Premium berish", callback_data=f"premium_{target_user_id}_1"),
             InlineKeyboardButton("❌ Premium olib tashlash", callback_data=f"remove_premium_{target_user_id}")],
            [InlineKeyboardButton("📩 Xabar yuborish", callback_data=f"message_{target_user_id}")],
            [InlineKeyboardButton("🔄 Yangilash", callback_data=f"refresh_{target_user_id}")],
            [InlineKeyboardButton("🔍 Boshqa qidiruv", callback_data="admin_search"),
             InlineKeyboardButton("🏠 Asosiy Sahifa", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(user_info_text, reply_markup=reply_markup, parse_mode='Markdown')


# ==============================
# ERROR HANDLER
# ==============================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error_msg = str(context.error)
    logger.error(f"Xatolik yuz berdi: {error_msg}")

    # Tarmoq xatolari uchun
    if "httpx.ReadError" in error_msg or "httpx.ConnectError" in error_msg:
        logger.error("Tarmoq xatosi - internet aloqasi muammosi")
        return

    # Formatlash xatolari uchun maxsus qayta ishlash
    if "Can't parse entities" in error_msg:
        logger.error("Formatlash xatosi - Markdown sintaksisi noto'g'ri")
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."
                )
        except Exception as e:
            logger.error(f"Xatolik haqida xabar yuborishda xato: {e}")
    else:
        try:
            if update and update.effective_user:
                user_data = user_manager.get_user_data(update.effective_user.id)
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=get_user_text(user_data, 'error')
                )
        except Exception as e:
            logger.error(f"Xatolik haqida xabar yuborishda xato: {e}")


# ==============================
# MAIN FUNCTION
# ==============================

def main():
    try:
        # Application yaratish
        application = Application.builder().token(Config.BOT_TOKEN).build()

        # Asosiy commandlar
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("menu", menu_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("premium", premium_command))
        application.add_handler(CommandHandler("model", model_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("newchat", newchat_command))
        application.add_handler(CommandHandler("language", language_command))
        application.add_handler(CommandHandler("admin", admin_command))

        # Yangi admin commandlari
        application.add_handler(CommandHandler("premium_user", premium_user_command))
        application.add_handler(CommandHandler("remove_premium", remove_premium_command))
        application.add_handler(CommandHandler("user_info", user_info_command))
        application.add_handler(CommandHandler("search_name", search_name_command))
        application.add_handler(CommandHandler("broadcast", broadcast_command))
        application.add_handler(CommandHandler("broadcast_premium", broadcast_premium_command))

        # Message handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_handler))

        # Error handler
        application.add_error_handler(error_handler)

        print("🚀 BahovuddinGPT Bot ishga tushdi...")
        print(f"🤖 Adminlar: {Config.ADMIN_IDS}")
        print(f"📊 Modellar: {len(Config.AI_MODELS)} ta")
        print(f"🌐 Tillar: O'zbek, Русский, English")
        print(f"👑 Admin funksiyalari: Faol!")
        print(f"🔍 Foydalanuvchi qidirish: Mavjud")
        print(f"📞 Kontakt ma'lumotlari: Saqlanadi")
        print(f"🏠 Asosiy sahifa tugmasi: Qo'shildi")
        print(f"💎 Premium boshqaruv: Faol")
        print(f"📩 Xabar yuborish: To'liq funksiya")

        # Polling ni boshlash
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            timeout=30,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30,
            drop_pending_updates=True
        )

    except Exception as e:
        logger.error(f"Botni ishga tushirishda xatolik: {e}")
        print(f"❌ Xatolik: {e}")
        time.sleep(5)
        main()


if __name__ == "__main__":
    main()
