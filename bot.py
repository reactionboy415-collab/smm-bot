import asyncio, random, re, requests, sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import os

# Define the database path inside the persistent data folder
DB_PATH = "/app/data/smm_ultra.db"

def init_db():
    # Ensure the directory exists (extra safety)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, last_use TEXT, total_orders INTEGER)''')
    conn.commit()
    conn.close()

# Update all other sqlite3.connect(DB_PATH) calls in your script!


# --- CONFIGURATION ---
TOKEN = "7963420197:AAGvcP9RnHZ-fxJvRzWj774HeGXELg4Mhig"
CHANNEL_ID = -1003470556336
LOG_GROUP_ID = -1003619580926
ADMIN_IDS = [7955644205, 7840042951]  # Both owners added

# 1. DATABASE SETUP
def init_db():
    conn = sqlite3.connect('smm_ultra.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, last_use TEXT, total_orders INTEGER)''')
    conn.commit()
    conn.close()

# 2. SMM LOGIC
class LeofameUltraStealth:
    def __init__(self):
        self.api_url = "https://leofame.com/free-instagram-views?api=1"
        self.main_url = "https://leofame.com/free-instagram-views"

    def get_headers(self):
        return {"User-Agent": f"Mozilla/5.0 (Android 14; Chrome/{random.randint(110,130)}.0.0)", "X-Requested-With": "XMLHttpRequest", "Referer": self.main_url}

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

bot_logic = LeofameUltraStealth()

# 3. HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('smm_ultra.db')
    conn.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", (user_id, '2000-01-01 00:00:00', 0))
    conn.commit()
    conn.close()

    keyboard = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/+Hp9WVjpwh3Q3NzI1")],
                [InlineKeyboardButton("✅ Verified - Start", callback_data='check_sub')]]
    
    await update.message.reply_text(
        f"<b>SMM ULTRA V6.0</b>\n\nTo use this bot, join our channel and click the button below.",
        parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def check_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=query.from_user.id)
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await query.edit_message_text("✅ <b>Access Granted!</b>\nSend your Instagram Reel/Post link now.")
        else:
            await query.answer("❌ Please join the channel first!", show_alert=True)
    except:
        await query.answer("⚠️ Error checking membership. Make sure Bot is Admin in Channel.", show_alert=True)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text
    if "instagram.com" not in url: return

    conn = sqlite3.connect('smm_ultra.db')
    c = conn.cursor()
    c.execute("SELECT last_use FROM users WHERE user_id=?", (user.id,))
    last_use = datetime.strptime(c.fetchone()[0], '%Y-%m-%d %H:%M:%S' if ' ' in c.fetchone()[0] else '%Y-%m-%d')
    
    if datetime.now() < last_use + timedelta(hours=24):
        await update.message.reply_text("❌ <b>Limit Reached:</b> Use again in 24 hours.")
        conn.close()
        return

    # User Notification
    status_msg = await update.message.reply_text("🚀 <b>Delivering free views please wait it can take 12 hours</b>", parse_mode='HTML')
    
    success = await bot_logic.fire(url)

    if success:
        c.execute("UPDATE users SET last_use=?, total_orders=total_orders+1 WHERE user_id=?", 
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user.id))
        conn.commit()
        await status_msg.edit_text("✅ <b>Views queued!</b> Usually delivered within 12 hours.")
        
        # LOG TO GROUP
        await context.bot.send_message(chat_id=LOG_GROUP_ID, parse_mode='HTML', text=(
            f"🔔 <b>NEW FREE ORDER</b>\n👤 User: {user.first_name}\n🆔 <code>{user.id}</code>\n🔗 Link: {url}"))
    else:
        await status_msg.edit_text("⚠️ Server busy. Try again later.")
    conn.close()

# 4. ADMIN COMMANDS
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    conn = sqlite3.connect('smm_ultra.db')
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    await update.message.reply_text(f"📊 <b>Admin Dashboard</b>\n\nTotal Users: {total}\nUse /broadcast [msg] to alert users.", parse_mode='HTML')

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = " ".join(context.args)
    if not msg: return await update.message.reply_text("Usage: /broadcast Hello Users!")
    
    conn = sqlite3.connect('smm_ultra.db')
    users = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    
    count = 0
    for user in users:
        try:
            await context.bot.send_message(chat_id=user[0], text=f"📢 <b>ANNOUNCEMENT</b>\n\n{msg}", parse_mode='HTML')
            count += 1
            await asyncio.sleep(0.05) # Avoid flood
        except: continue
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(check_sub, pattern='check_sub'))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    print("Bot Live with Admin IDs:", ADMIN_IDS)
    app.run_polling()