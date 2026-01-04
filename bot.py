import asyncio, random, re, requests, time, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- FLASK SERVER FOR RENDER ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot is Running!", 200

def run_flask():
    # Render uses port 10000 by default
    web_app.run(host='0.0.0.0', port=10000)

# --- CONFIGURATION ---
TOKEN = "7963420197:AAGvcP9RnHZ-fxJvRzWj774HeGXELg4Mhig"
CHANNEL_ID = -1003470556336
LOG_GROUP_ID = -1003619580926
user_cooldowns = {} 

# [Previous SMMCore Class and Handlers Code remains exactly the same]
class SMMCore:
    def __init__(self):
        self.api_url = "https://leofame.com/free-instagram-views?api=1"
        self.main_url = "https://leofame.com/free-instagram-views"

    def get_headers(self):
        return {"User-Agent": f"Mozilla/5.0 (Linux; Android 14) Chrome/{random.randint(110,130)}.0.0", "X-Requested-With": "XMLHttpRequest", "Referer": self.main_url}

    async def fire(self, link):
        link = link.split('?')[0]
        session = requests.Session()
        try:
            r = session.get(self.main_url, headers=self.get_headers())
            token = re.search(r'name="token" value="([a-f0-9]+)"', r.text).group(1)
            await asyncio.sleep(2)
            payload = {"token": token, "timezone_offset": "Asia/Calcutta", "free_link": link, "quantity": "200"}
            resp = session.post(self.api_url, headers=self.get_headers(), data=payload)
            return '"success":"Success"' in resp.text
        except: return False

smm = SMMCore()

async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if await check_membership(user.id, context):
        await update.message.reply_text(f"👋 <b>Welcome {user.first_name}!</b>\nSend Instagram link for 200 views.", parse_mode=ParseMode.HTML)
    else:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url="https://t.me/+Hp9WVjpwh3Q3NzI1")]])
        await update.message.reply_text("❌ Join channel first!", reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text
    if "instagram.com" not in url: return
    if not await check_membership(user.id, context):
        return await update.message.reply_text("❌ Join channel first!")

    current_time = time.time()
    if user.id in user_cooldowns and current_time - user_cooldowns[user.id] < 86400:
        return await update.message.reply_text("⏳ Limit: Once per 24 hours.")

    status = await update.message.reply_text("🚀 <b>Delivering free views please wait it can take 12 hours</b>", parse_mode=ParseMode.HTML)
    if await smm.fire(url):
        user_cooldowns[user.id] = current_time
        await status.edit_text("✅ <b>Success!</b> Views queued.")
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=f"🔥 <b>ORDER</b>\n👤 {user.first_name}\n🔗 {url}", parse_mode=ParseMode.HTML)
    else:
        await status.edit_text("⚠️ Server Busy.")

if __name__ == '__main__':
    # Start Flask in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start Telegram Bot
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    print("Bot & Health Check are Live!")
    app.run_polling()
