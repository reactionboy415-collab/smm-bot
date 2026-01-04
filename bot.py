import asyncio, random, re, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "7963420197:AAGvcP9RnHZ-fxJvRzWj774HeGXELg4Mhig"
CHANNEL_ID = -1003470556336
LOG_GROUP_ID = -1003619580926

# 1. SMM CORE (Fast & Clean)
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
        link = link.split('?')[0] # Clean link
        session = requests.Session()
        try:
            # Step 1: Get Token
            r = session.get(self.main_url, headers=self.get_headers())
            token = re.search(r'name="token" value="([a-f0-9]+)"', r.text).group(1)
            
            # Step 2: Humanizing Delay
            await asyncio.sleep(2)
            
            # Step 3: Send Views
            payload = {"token": token, "timezone_offset": "Asia/Calcutta", "free_link": link, "quantity": "200"}
            resp = session.post(self.api_url, headers=self.get_headers(), data=payload)
            return '"success":"Success"' in resp.text
        except: return False

smm = SMMCore()

# 2. HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Force Join Check
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user.id)
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await update.message.reply_text(
                f"<b>Welcome {user.first_name}!</b> 🚀\n\nSend your Instagram Reel or Post link below to get <b>200 Free Views</b> instantly.",
                parse_mode=ParseMode.HTML
            )
        else:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url="https://t.me/+Hp9WVjpwh3Q3NzI1")]])
            await update.message.reply_text(
                "❌ <b>Access Denied!</b>\n\nYou must join our official channel to use this bot.",
                reply_markup=keyboard, parse_mode=ParseMode.HTML
            )
    except:
        await update.message.reply_text("⚠️ Make sure the bot is Admin in your channel!")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text
    
    if "instagram.com" not in url:
        return # Ignore non-instagram messages

    # Immediate User Feedback
    status = await update.message.reply_text("🚀 <b>Delivering free views please wait it can take 12 hours</b>", parse_mode=ParseMode.HTML)
    
    # Fire Request
    success = await smm.fire(url)

    if success:
        await status.edit_text("✅ <b>Order Successful!</b>\nYour views are now in the queue.")
        # Report to your group
        await context.bot.send_message(
            chat_id=LOG_GROUP_ID,
            text=f"🔥 <b>NEW VIEW ORDER</b>\n\n👤 <b>User:</b> {user.first_name}\n🔗 <b>Link:</b> {url}",
            parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )
    else:
        await status.edit_text("⚠️ <b>Server Busy!</b>\nPlease try again in a few minutes.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    print("SMM ULTRA (Stateless Mode) is running...")
    app.run_polling()
