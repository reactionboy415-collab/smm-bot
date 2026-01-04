import asyncio, random, re, requests, time, threading, string
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- FLASK UPTIME ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "SMM Master Pro V5 Fixed 🚀", 200
def run_flask(): web_app.run(host='0.0.0.0', port=10000)

# --- CONFIG ---
TOKEN = "7963420197:AAGtGASUJo9viBUFa_fuhVtWAo53eRioplY"
ADMIN_ID = 7840042951
CHANNEL_ID = -1003470556336 
CHANNEL_LINK = "https://t.me/+o0Pj60A5oI0zMmU1" 

stats = {"success": 0, "failed": 0, "total": 0}

class ProEngine:
    def __init__(self):
        self.public_proxies = [] 
        self.priority_proxies = [] 
        self.proxy_sources = [
            "https://proxy-bot-g34t.onrender.com/api/raw?type=http&qty=500",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
        ]

    def purify_url(self, raw_url):
        match = re.search(r'(https?://(?:www\.)?instagram\.com/(?:reels|reel|p)/[A-Za-z0-9_-]+)', raw_url)
        if match:
            clean = match.group(1)
            return clean + "/" if not clean.endswith('/') else clean
        return None

    def hunter_worker(self):
        while True:
            raw_ips = []
            for src in self.proxy_sources:
                try:
                    res = requests.get(src, timeout=10)
                    if res.status_code == 200: raw_ips.extend(res.text.splitlines())
                except: continue
            raw_ips = list(set([i.strip() for i in raw_ips if ":" in i]))
            random.shuffle(raw_ips)
            valid = []
            for p in raw_ips[:100]:
                try:
                    p_form = f"http://{p}" if "://" not in p else p
                    if requests.get("https://fameviso.com/", proxies={"http": p_form, "https": p_form}, timeout=2).status_code == 200:
                        valid.append(p_form)
                        if len(valid) >= 50: break
                except: continue
            self.public_proxies = valid
            time.sleep(180)

    def attack(self, clean_url, update, context):
        user = update.effective_user
        def admin_log(msg):
            try: context.bot.send_message(ADMIN_ID, f"🛠 <b>Live Log:</b> {user.first_name}\n📡 {msg}", parse_mode=ParseMode.HTML)
            except: pass

        # Pool merging: Latest Priority First
        test_pool = self.priority_proxies + self.public_proxies
        if not test_pool: return False, "No Proxy"

        max_attempts = min(len(test_pool), 25)
        
        for attempt in range(1, max_attempts + 1):
            proxy_url = test_pool[attempt-1]
            p_type = "⭐ Priority" if proxy_url in self.priority_proxies else "🌐 Public"
            admin_log(f"Attempt {attempt}/{max_attempts}\nType: {p_type}\nProxy: <code>{proxy_url}</code>")

            session = requests.Session()
            session.proxies = {"http": proxy_url, "https": proxy_url}
            
            boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            ua = f"Mozilla/5.0 (Linux; Android 14; SM-G99{random.randint(1,9)}B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.{random.randint(1000,9999)} Mobile Safari/537.36"
            ext_ua = f"Fingerprint: fp_{int(time.time()*1000)} | User-agent: {ua}"
            
            headers = {
                "authority": "fameviso.com",
                "content-type": f"multipart/form-data; boundary={boundary}",
                "user-agent": ua,
                "x-requested-with": "XMLHttpRequest",
                "origin": "https://fameviso.com",
                "referer": "https://fameviso.com/free-instagram-views/"
            }

            try:
                # Step 1: CSRF
                land = session.get("https://fameviso.com/free-instagram-views/", timeout=10)
                csrf = re.search(r'name=\"csrf_token\" value=\"(.*?)\"', land.text).group(1)
                
                base_payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                                f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                                f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{clean_url}\r\n"
                                f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n"
                                f"--{boundary}\r\nContent-Disposition: form-data; name=\"extended_user_agent\"\r\n\r\n{ext_ua}\r\n")

                # Step 2: Initial Request
                r1 = session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                 data=(base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n").encode('utf-8'), 
                                 headers=headers, timeout=12)
                
                res1 = r1.json()
                if res1.get("status") == "proceed":
                    token = res1.get("request_token")
                    time.sleep(2)
                    
                    # Step 3: Verify Request
                    data2 = base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                    r2 = session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                     data=data2.encode('utf-8'), headers=headers, timeout=12)
                    
                    if "success" in r2.text.lower():
                        admin_log("🏆 <b>SUCCESS!</b> Order Sent.")
                        return True, proxy_url
                
                admin_log("⚠️ Proxy Busy/Rejected. Next...")
            except Exception as e:
                admin_log(f"❌ Connection Error: {str(e)[:40]}")
                if proxy_url in self.priority_proxies: self.priority_proxies.remove(proxy_url)
                continue
        return False, "Failed"

core = ProEngine()

# --- HANDLERS ---
async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if "instagram.com" not in update.message.text: return
    
    clean_url = core.purify_url(update.message.text)
    if not clean_url: return

    status_msg = await update.message.reply_text("🚀 <b>V5 Engine: Using Priority Queue...</b>", parse_mode=ParseMode.HTML)
    
    # Run attack in thread to avoid blocking bot
    loop = asyncio.get_event_loop()
    success, px = await loop.run_in_executor(None, core.attack, clean_url, update, context)
    
    if success:
        stats['success'] += 1
        await status_msg.edit_text(f"✅ <b>Order Successful!</b>\nTarget: <code>{clean_url}</code>", parse_mode=ParseMode.HTML)
    else:
        stats['failed'] += 1
        await status_msg.edit_text("❌ <b>Failed.</b> All priority and public proxies were rejected.")

async def add_proxies_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    ips = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', update.message.text)
    if not ips: return await update.message.reply_text("❌ No valid Proxies.")
    formatted = [f"http://{ip}" for ip in ips]
    core.priority_proxies = formatted + core.priority_proxies
    await update.message.reply_text(f"✅ Added {len(ips)} Priority Proxies.")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=core.hunter_worker, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("🚀 Bot V5 Ready!")))
    app.add_handler(CommandHandler("stats", lambda u,c: u.message.reply_text(f"Success: {stats['success']}\nManual: {len(core.priority_proxies)}")))
    app.add_handler(CommandHandler("add", add_proxies_priority))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.run_polling()
