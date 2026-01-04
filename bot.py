import asyncio, random, re, requests, time, threading, string
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- SECTION 1: FLASK UPTIME (FOR RENDER) ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "SMM Master Pro V6 Masterpiece is Active 🚀", 200
def run_flask(): web_app.run(host='0.0.0.0', port=10000)

# --- SECTION 2: CONFIGURATION ---
TOKEN = "7963420197:AAGtGASUJo9viBUFa_fuhVtWAo53eRioplY"
ADMIN_ID = 7840042951
CHANNEL_ID = -1003470556336 
CHANNEL_LINK = "https://t.me/+o0Pj60A5oI0zMmU1" 

stats = {"success": 0, "failed": 0, "total": 0, "users": set()}

class MasterEngine:
    def __init__(self):
        self.priority_pool = [] # Admin's manual proxies
        self.public_pool = []   # Auto-scraped proxies
        self.sources = [
            "https://proxy-bot-g34t.onrender.com/api/raw?type=http&qty=500",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
        ]

    def hunter_worker(self):
        """Infinite Background Proxy Hunter"""
        while True:
            raw = []
            for s in self.sources:
                try:
                    res = requests.get(s, timeout=10)
                    if res.status_code == 200: raw.extend(res.text.splitlines())
                except: continue
            
            clean_ips = list(set([i.strip() for i in raw if ":" in i]))
            random.shuffle(clean_ips)
            
            valid = []
            for p in clean_ips[:150]:
                try:
                    p_form = f"http://{p}" if "://" not in p else p
                    if requests.get("https://fameviso.com/", proxies={"http": p_form, "https": p_form}, timeout=2.5).status_code == 200:
                        valid.append(p_form)
                        if len(valid) >= 60: break
                except: continue
            self.public_pool = valid
            time.sleep(150)

    def attack(self, clean_url, user_name, context):
        """The Master Attack Logic with Live Reporting"""
        def send_admin(msg):
            try: context.bot.send_message(ADMIN_ID, f"📡 <b>Live Tracker:</b> {user_name}\n{msg}", parse_mode=ParseMode.HTML)
            except: pass

        # Combine Pools (Priority First like Mobile Data Rotation)
        total_pool = self.priority_pool + self.public_pool
        if not total_pool:
            return False, "No Proxy Available"

        send_admin(f"🔄 Starting Engine...\nTarget: <code>{clean_url}</code>\nPool Size: {len(total_pool)}")

        for attempt in range(1, 21): # Try 20 times with different IPs
            proxy = random.choice(total_pool)
            p_type = "⭐ Private" if proxy in self.priority_pool else "🌐 Public"
            
            send_admin(f"Attempt {attempt}/20\nUsing {p_type} IP: <code>{proxy}</code>")

            session = requests.Session()
            session.proxies = {"http": proxy, "https": proxy}
            boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            ua = f"Mozilla/5.0 (Linux; Android 14; SM-G99{random.randint(1,9)}B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.{random.randint(1000,9999)} Mobile Safari/537.36"
            
            try:
                # STEP 1: BYPASS CSRF
                land = session.get("https://fameviso.com/free-instagram-views/", timeout=10)
                csrf = re.search(r'name=\"csrf_token\" value=\"(.*?)\"', land.text).group(1)
                
                payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                           f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                           f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{clean_url}\r\n"
                           f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n"
                           f"--{boundary}\r\nContent-Disposition: form-data; name=\"extended_user_agent\"\r\n\r\nFingerprint: fp_{int(time.time())} | {ua}\r\n")

                # STEP 2: INITIALIZE
                r1 = session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                 data=(payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n").encode('utf-8'), 
                                 headers={"content-type": f"multipart/form-data; boundary={boundary}", "user-agent": ua}, timeout=12)
                
                if r1.json().get("status") == "proceed":
                    token = r1.json().get("request_token")
                    time.sleep(2.5) # Emulate human wait
                    
                    # STEP 3: DISPATCH
                    final_data = payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                    r2 = session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                     data=final_data.encode('utf-8'), headers={"content-type": f"multipart/form-data; boundary={boundary}", "user-agent": ua}, timeout=12)
                    
                    if "success" in r2.text.lower():
                        send_admin("✅ <b>SUCCESS!</b> Views Dispatched.")
                        return True, proxy

            except Exception as e:
                send_admin(f"⚠️ Proxy Failed: {str(e)[:40]}")
                if proxy in total_pool: total_pool.remove(proxy)
                continue
                
        return False, "Exhausted"

core = MasterEngine()

# --- SECTION 3: BOT LOGIC ---

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    stats["users"].add(user.id)
    raw_url = update.message.text
    if "instagram.com" not in raw_url: return

    # URL Purifier (Standardize Link)
    match = re.search(r'(https?://(?:www\.)?instagram\.com/(?:reels|reel|p)/[A-Za-z0-9_-]+)', raw_url)
    if not match: return await update.message.reply_text("❌ Invalid Reel Link.")
    clean_url = match.group(1) + "/"

    status_msg = await update.message.reply_text("💎 <b>Masterpiece Engine: Rotating IP...</b>\nAdmin is monitoring live.", parse_mode=ParseMode.HTML)
    
    stats["total"] += 1
    # Run in thread for high performance
    loop = asyncio.get_event_loop()
    success, px = await loop.run_in_executor(None, core.attack, clean_url, user.first_name, context)
    
    if success:
        stats["success"] += 1
        await status_msg.edit_text(f"✅ <b>Order Placed!</b>\nTarget: <code>{clean_url}</code>\nViews will arrive in 5-10 mins.", parse_mode=ParseMode.HTML)
    else:
        stats["failed"] += 1
        await status_msg.edit_text("❌ <b>All IP Rotations Failed.</b>\nTry again with fresh proxies or wait for server reset.")

# --- ADMIN COMMANDS ---

async def add_proxies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    ips = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', update.message.text)
    if not ips: return await update.message.reply_text("❌ Give me IP:PORT list.")
    core.priority_pool = [f"http://{i}" for i in ips] + core.priority_pool
    await update.message.reply_text(f"👑 <b>Master, {len(ips)} Priority IPs Added!</b>")

async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text(f"📊 <b>Master Dashboard</b>\n\n✅ Success: {stats['success']}\n❌ Failed: {stats['failed']}\n👥 Users: {len(stats['users'])}\n⭐ Priority IPs: {len(core.priority_pool)}\n🌐 Public IPs: {len(core.public_pool)}", parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=core.hunter_worker, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("🔥 <b>SMM Masterpiece V6 Ready!</b>\nSend link to start views.", parse_mode=ParseMode.HTML)))
    app.add_handler(CommandHandler("stats", get_stats))
    app.add_handler(CommandHandler("add", add_proxies))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.run_polling()
