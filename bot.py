import asyncio, random, re, requests, time, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- WEB SERVER FOR RENDER ---
app_server = Flask(__name__)
@app_server.route('/')
def home(): return "SMM Bot Status: Online", 200

def run_web_server():
    app_server.run(host='0.0.0.0', port=10000)

# --- CONFIGURATION ---
TOKEN = "7963420197:AAGvcP9RnHZ-fxJvRzWj774HeGXELg4Mhig"
CHANNEL_ID = -1003470556336
LOG_GROUP_ID = -1003619580926
ADMIN_REPORT_ID = 7840042951

user_cooldowns = {} 

class SMMCore:
    def __init__(self):
        self.api_url = "https://leofame.com/free-instagram-views?api=1"
        self.main_url = "https://leofame.com/free-instagram-views"

    def get_headers(self):
        v = random.choice(["118", "119", "120", "121", "122"])
        return {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{v}.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self.main_url,
            "Origin": "https://leofame.com"
        }

    async def fire_with_debug(self, link):
        link = link.split('?')[0]
        last_response = "No response"
        
        for attempt in range(2): # 2 Retries
            session = requests.Session()
            try:
                r = session.get(self.main_url, headers=self.get_headers(), timeout=10)
                token_match = re.search(r'name="token" value="([a-f0-9]+)"', r.text)
                if not token_match:
                    last_response = "Token not found in HTML"
                    continue
                
                token = token_match.group(1)
                await asyncio.sleep(3)
                
                payload = {"token": token, "timezone_offset": "Asia/Calcutta", "free_link": link, "quantity": "200"}
                resp = session.post(self.api_url, headers=self.get_headers(), data=payload, timeout=15)
                last_response = resp.text[:200] # Capture first 200 chars of response
                
                if '"success":"Success"' in resp.text:
                    return True, "Success"
                elif "Please wait" in resp.text:
                    last_response = "Server Rate Limit: Please wait"
                
            except Exception as e:
                last_response = f"Error: {str(e)}"
                await asyncio.sleep(2)
        
        return False, last_response

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
    if await check_membership(user.id, context):
        await update.message.reply_text(f"🚀 <b>Welcome {user.first_name}!</b>\nSend link for 200 free views.", parse_mode=ParseMode.HTML)
    else:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url="https://t.me/+Hp9WVjpwh3Q3NzI1")]])
        await update.message.reply_text("❌ Join channel first!", reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text
    if "instagram.com" not in url: return

    if not await check_membership(user.id, context):
        return await update.message.reply_text("❌ Join channel first!")

    now = time.time()
    if user.id in user_cooldowns and now - user_cooldowns[user.id] < 86400:
        rem = int(86400 - (now - user_cooldowns[user.id]))
        return await update.message.reply_text(f"⏳ Wait {rem//3600}h {(rem%3600)//60}m.")

    status_msg = await update.message.reply_text("🚀 <b>Delivering free views please wait it can take 12 hours</b>", parse_mode=ParseMode.HTML)
    
    success, server_resp = await smm.fire_with_debug(url)
    
    # --- ADMIN REPORT ---
    report = (
        f"User - {user.first_name} (<code>{user.id}</code>)\n"
        f"Reel / post link - {url}\n"
        f"Status - {'✅ Success' if success else '❌ Failed'}\n"
        f"Server Response - <code>{server_resp}</code>"
    )

    try:
        # Report to Admin
        await context.bot.send_message(chat_id=ADMIN_REPORT_ID, text=report, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        # Report to Group
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=report, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except: pass

    if success:
        user_cooldowns[user.id] = now
        await status_msg.edit_text("✅ <b>Order Successful!</b> Views queued.")
    else:
        await status_msg.edit_text(f"⚠️ <b>Server Error!</b>\nResponse: <code>{server_resp}</code>\nTry again later.", parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    print("SMM ULTRA V15.0 (Debug Mode) Live!")
    app.run_polling()
