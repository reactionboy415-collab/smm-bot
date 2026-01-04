import asyncio, random, re, requests, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "7963420197:AAGvcP9RnHZ-fxJvRzWj774HeGXELg4Mhig"
CHANNEL_ID = -1003470556336
LOG_GROUP_ID = -1003619580926

# In-memory database to track users (resets on bot restart)
user_cooldowns = {} 

class SMMCore:
    def __init__(self):
        self.api_url = "https://leofame.com/free-instagram-views?api=1"
        self.main_url = "https://leofame.com/free-instagram-views"

    def get_headers(self):
        return {
            "User-Agent": f"Mozilla/5.0 (Linux; Android 14) Chrome/{random.randint(110,130)}.0.0",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self.main_url
        }

    async def fire(self, link):
        link = link.split('?')[0]
        session = requests.Session()
        try:
            r = session.get(self.main_url, headers=self.get_headers())
            token = re.search(r'name="token" value="([a-f0-9]+)"', r.text).group(1)
            await asyncio.sleep(random.uniform(2, 4)) # Professional human delay
            payload = {"token": token, "timezone_offset": "Asia/Calcutta", "free_link": link, "quantity": "200"}
            resp = session.post(self.api_url, headers=self.get_headers(), data=payload)
            return '"success":"Success"' in resp.text
        except: return False

smm = SMMCore()

# --- HELPERS ---
async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except: return False

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_joined = await check_membership(user.id, context)
    
    if is_joined:
        await update.message.reply_text(
            f"👋 <b>Welcome Back, {user.first_name}!</b>\n\n"
            f"I am the most powerful SMM Stealth bot. Send me your Instagram link and I will inject <b>200 Views</b>.\n\n"
            f"⚠️ <b>Note:</b> You can use this service once every 24 hours.",
            parse_mode=ParseMode.HTML
        )
    else:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url="https://t.me/+Hp9WVjpwh3Q3NzI1")]])
        await update.message.reply_text(
            f"❌ <b>Access Restricted!</b>\n\nHello {user.first_name}, you must be a member of our channel to use this bot.",
            reply_markup=keyboard, parse_mode=ParseMode.HTML
        )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text
    
    if "instagram.com" not in url:
        return

    # 1. Force Join Check
    if not await check_membership(user.id, context):
        return await update.message.reply_text("❌ <b>Error:</b> You must join the channel first to use this bot!")

    # 2. 24-Hour Cooldown Logic
    current_time = time.time()
    if user.id in user_cooldowns:
        last_time = user_cooldowns[user.id]
        if current_time - last_time < 86400: # 86400 seconds = 24 hours
            remaining = int(86400 - (current_time - last_time))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            return await update.message.reply_text(
                f"⏳ <b>Cooldown Active!</b>\n\nYou have already used your free limit. Please wait <b>{hours}h {minutes}m</b> before sending another link.",
                parse_mode=ParseMode.HTML
            )

    # 3. Execution
    status = await update.message.reply_text("🚀 <b>Delivering free views please wait it can take 12 hours</b>", parse_mode=ParseMode.HTML)
    
    # Visual "Stealth" Animation
    await asyncio.sleep(1.5)
    await status.edit_text("🛰 <b>Connecting to Instagram Mainframe...</b>", parse_mode=ParseMode.HTML)
    
    success = await smm.fire(url)

    if success:
        # Save cooldown
        user_cooldowns[user.id] = current_time
        
        await status.edit_text(
            "✅ <b>Order Successful!</b>\n\nYour 200 views have been injected into the delivery queue. Delivery usually starts within 12 hours.",
            parse_mode=ParseMode.HTML
        )
        
        # Log to your Group
        log_text = (
            f"🔔 <b>NEW SMM ORDER</b>\n\n"
            f"👤 <b>User:</b> {user.first_name}\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"🔗 <b>Link:</b> {url}\n"
            f"✨ <b>Service:</b> 200 Views"
        )
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=log_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    else:
        await status.edit_text("⚠️ <b>Service Overloaded!</b>\nPlease try again after 10-15 minutes.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    print("SMM ULTRA V12 (Professional) is Live!")
    app.run_polling()
