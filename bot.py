import asyncio, random, re, requests, httpx, time, threading, string
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- FLASK SERVER (For 24/7 Hosting) ---
web_app = Flask(__name__)
@web_app.route('/')
def health_check(): return "<h1>SMM Bot is Active & Running!</h1>", 200
def run_flask(): web_app.run(host='0.0.0.0', port=10000)

# --- CONFIGURATION ---
TOKEN = "8344334544:AAGRoUZm7mtjeqbqPSgUKhU4lqTb5dLRYWA"
ADMIN_ID = 7840042951
CHANNEL_ID = -1003470556336
LOG_GROUP_ID = -1003619580926

# Tracking Databases (In-Memory)
user_cooldowns = {}   
reel_cooldowns = {}   

class SMMCore:
    def __init__(self):
        self.leofame_main = "https://leofame.com/free-instagram-views"
        self.leofame_api = "https://leofame.com/free-instagram-views?api=1"
        self.fameviso_api = "https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php"
        self.my_proxy_api = "https://proxy-bot-g34t.onrender.com/api/raw?type=http&qty=500"
        self.github_sources = [
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt"
        ]
        self.working_proxies = []

    def proxy_hunter_worker(self):
        """Background Thread: Har 60 sec mein proxies refresh karega"""
        while True:
            all_raw = []
            try:
                r = requests.get(self.my_proxy_api, timeout=10)
                if r.status_code == 200: all_raw.extend(r.text.splitlines())
            except: pass
            for src in self.github_sources:
                try:
                    res = requests.get(src, timeout=10)
                    if res.status_code == 200: all_raw.extend(res.text.splitlines())
                except: continue
            
            all_raw = list(set([p.strip() for p in all_raw if ":" in p]))
            random.shuffle(all_raw)
            temp_working = []
            for p in all_raw[:80]:
                try:
                    px_addr = f"http://{p}"
                    # Fast test
                    test = requests.get("https://fameviso.com/", proxies={"http": px_addr, "https": px_addr}, timeout=3)
                    if test.status_code == 200:
                        temp_working.append(px_addr)
                        if len(temp_working) >= 45: break
                except: continue
            if temp_working: self.working_proxies = temp_working
            time.sleep(60)

    def _extract_id(self, link):
        match = re.search(r'/(?:reels|reel|p)/([A-Za-z0-9_-]+)', link)
        return match.group(1) if match else None

    # ENGINE 1: LEOFAME
    async def fire_leofame(self, link):
        proxy = random.choice(self.working_proxies) if self.working_proxies else None
        session = requests.Session()
        if proxy: session.proxies = {"http": proxy, "https": proxy}
        try:
            r = session.get(self.leofame_main, timeout=10)
            token = re.search(r'name="token" value="([a-f0-9]+)"', r.text).group(1)
            payload = {"token": token, "timezone_offset": "Asia/Calcutta", "free_link": link, "quantity": "200"}
            resp = session.post(self.leofame_api, data=payload, timeout=15)
            return '"success":"Success"' in resp.text, proxy
        except: return False, proxy

    # ENGINE 2: FAMEVISO
    async def fire_fameviso(self, link):
        proxy = random.choice(self.working_proxies) if self.working_proxies else None
        boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        headers = {"authority": "fameviso.com", "content-type": f"multipart/form-data; boundary={boundary}", "origin": "https://fameviso.com", "referer": "https://fameviso.com/free-instagram-views/", "user-agent": "Mozilla/5.0 (Linux; Android 14) Chrome/121.0.0.0"}
        
        async with httpx.AsyncClient(proxies=proxy, verify=False, timeout=25.0) as client:
            try:
                land = await client.get("https://fameviso.com/free-instagram-views/")
                csrf = re.search(r'name="csrf_token" value="(.*?)"', land.text).group(1)
                base_data = f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{link}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n"
                # Step 1
                r1 = await client.post(self.fameviso_api, content=(base_data + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n").encode('utf-8'), headers=headers)
                if r1.json().get("status") == "proceed":
                    token = r1.json().get("request_token")
                    await asyncio.sleep(2)
                    # Step 2
                    p2 = base_data + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                    r2 = await client.post(self.fameviso_api, content=p2.encode('utf-8'), headers=headers)
                    return "success" in r2.text.lower(), proxy
                return False, proxy
            except: return False, proxy

smm = SMMCore()

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"👋 <b>Hello {user.first_name}!</b>\n\n"
        f"🚀 <b>Power SMM Bot V80 is Ready.</b>\n"
        f"Send any Instagram Reel/Post link to get 200+ views for free.\n\n"
        f"⚠️ <b>Limit:</b> Once per 24 hours per user/reel."
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text
    if "instagram.com" not in url: return
    
    reel_id = smm._extract_id(url)
    if not reel_id: return

    # Admin Logging Utility
    async def log_to_admin(status, srv, px):
        msg = f"🔔 <b>NEW ORDER LOG</b>\n👤 User: {user.first_name}\n🔗 Reel: {reel_id}\n⚙️ Server: {srv}\n🌐 Proxy: {px}\n✅ Status: {'SUCCESS' if status else 'FAILED'}"
        try: await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode=ParseMode.HTML)
        except: pass

    current_time = time.time()
    # Checks
    if user.id in user_cooldowns and current_time - user_cooldowns[user.id] < 86400:
        return await update.message.reply_text("⏳ Limit: Come back after 24 hours.")
    if reel_id in reel_cooldowns and current_time - reel_cooldowns[reel_id] < 86400:
        return await update.message.reply_text("⚠️ This reel already received views today.")

    status_msg = await update.message.reply_text("🛡️ <b>Verifying link and activating server...</b>", parse_mode=ParseMode.HTML)
    
    # Try Server 1
    success, p_used = await smm.fire_leofame(url)
    srv_name = "Leofame (S1)"
    
    if not success:
        await status_msg.edit_text("🔄 Server 1 busy. Triggering Backup Engine...")
        success, p_used = await smm.fire_fameviso(url)
        srv_name = "Fameviso (S2)"

    if success:
        user_cooldowns[user.id] = current_time
        reel_cooldowns[reel_id] = current_time
        await status_msg.edit_text("✅ <b>Views Dispatched!</b> Enjoy your free service.")
        await log_to_admin(True, srv_name, p_used)
    else:
        await status_msg.edit_text("❌ All servers are currently busy. Try again later.")
        await log_to_admin(False, srv_name, p_used)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=smm.proxy_hunter_worker, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    
    print("🚀 Bot V80 is Live & Powerful!")
    app.run_polling()
