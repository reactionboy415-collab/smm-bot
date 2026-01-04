import asyncio, random, re, requests, httpx, time, threading, string
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- FLASK UPTIME ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "SMM Master Pro V3 is Active 🚀", 200
def run_flask(): web_app.run(host='0.0.0.0', port=10000)

# --- CONFIG & DB ---
TOKEN = "7963420197:AAGtGASUJo9viBUFa_fuhVtWAo53eRioplY"
ADMIN_ID = 7840042951
CHANNEL_ID = -1003470556336 
CHANNEL_LINK = "https://t.me/+o0Pj60A5oI0zMmU1" 

stats = {"success": 0, "failed": 0, "total": 0}

class ProEngine:
    def __init__(self):
        self.proxies = []
        self.manual_proxies = []
        self.proxy_sources = [
            "https://proxy-bot-g34t.onrender.com/api/raw?type=http&qty=500",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        ]

    def purify_url(self, raw_url):
        match = re.search(r'(https?://(?:www\.)?instagram\.com/(?:reels|reel|p)/[A-Za-z0-9_-]+)', raw_url)
        if match:
            clean = match.group(1)
            return clean + "/" if not clean.endswith('/') else clean
        return None

    def hunter_worker(self):
        """Background Proxy Scraper & Tester"""
        while True:
            raw_ips = self.manual_proxies.copy()
            for src in self.proxy_sources:
                try:
                    res = requests.get(src, timeout=10)
                    if res.status_code == 200: raw_ips.extend(res.text.splitlines())
                except: continue
            
            raw_ips = list(set([i.strip() for i in raw_ips if ":" in i]))
            random.shuffle(raw_ips)
            
            valid = []
            for p in raw_ips[:200]:
                try:
                    p_form = f"http://{p}" if "://" not in p else p
                    # Test against a real endpoint
                    with requests.get("https://fameviso.com/", proxies={"http": p_form}, timeout=2) as r:
                        if r.status_code == 200:
                            valid.append(p_form)
                            if len(valid) >= 60: break
                except: continue
            self.proxies = valid
            time.sleep(180)

    async def attack(self, clean_url, update, context):
        user = update.effective_user
        
        async def admin_log(msg):
            try: await context.bot.send_message(ADMIN_ID, f"🛠 <b>Live Log:</b> {user.first_name}\n📡 {msg}", parse_mode=ParseMode.HTML)
            except: pass

        # --- INFINITE RETRY LOOP (Max 10 tries) ---
        for attempt in range(1, 11):
            if not self.proxies:
                await admin_log("No working proxies in pool. Waiting for Hunter...")
                await asyncio.sleep(5)
                continue

            proxy = random.choice(self.proxies)
            await admin_log(f"Attempt {attempt}/10\nUsing Proxy: <code>{proxy}</code>")

            boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            ua = f"Mozilla/5.0 (Linux; Android 14; SM-G99{random.randint(1,9)}B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.{random.randint(1000,9999)} Mobile Safari/537.36"
            ext_ua = f"Fingerprint: fp_{int(time.time()*1000)} | User-agent: {ua}"
            headers = {"authority": "fameviso.com", "content-type": f"multipart/form-data; boundary={boundary}", "user-agent": ua, "origin": "https://fameviso.com", "referer": "https://fameviso.com/free-instagram-views/"}

            try:
                async with httpx.AsyncClient(proxies=proxy, http2=True, timeout=15.0, verify=False) as client:
                    # Step 1: CSRF
                    land = await client.get("https://fameviso.com/free-instagram-views/")
                    csrf = re.search(r'name=\"csrf_token\" value=\"(.*?)\"', land.text).group(1)
                    
                    base_payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{clean_url}\r\n"
                                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n"
                                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"extended_user_agent\"\r\n\r\n{ext_ua}\r\n")

                    # Step 2: Initial Request
                    r1 = await client.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                          content=(base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n").encode('utf-8'), headers=headers)
                    
                    res1 = r1.json()
                    if res1.get("status") == "proceed":
                        token = res1.get("request_token")
                        await asyncio.sleep(2)
                        
                        # Step 3: Verify
                        data2 = base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                        r2 = await client.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", content=data2.encode('utf-8'), headers=headers)
                        
                        if "success" in r2.text.lower():
                            await admin_log("✅ <b>SUCCESS!</b> Views Dispatched.")
                            return True, proxy
                    
                    await admin_log(f"⚠️ Proxy rejected/failed. Retrying...")
                    if proxy in self.proxies: self.proxies.remove(proxy) # Remove bad proxy

            except Exception as e:
                await admin_log(f"❌ Proxy Error: {str(e)[:50]}... Skipping.")
                if proxy in self.proxies: self.proxies.remove(proxy)
                continue
        
        return False, "All Retries Failed"

core = ProEngine()

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 <b>Professional SMM Master V3</b>\nSend Reel Link for 250 views.", parse_mode=ParseMode.HTML)

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    raw_url = update.message.text
    if "instagram.com" not in raw_url: return

    # Membership Check
    try:
        m = await context.bot.get_chat_member(CHANNEL_ID, user.id)
        if m.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            btn = [[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]]
            return await update.message.reply_text("❌ Join first!", reply_markup=InlineKeyboardMarkup(btn))
    except: pass

    clean_url = core.purify_url(raw_url)
    if not clean_url: return

    status_msg = await update.message.reply_text("🔄 <b>Searching Working Proxy...</b>", parse_mode=ParseMode.HTML)
    
    stats['total'] += 1
    success, used_px = await core.attack(clean_url, update, context)
    
    if success:
        stats['success'] += 1
        await status_msg.edit_text(f"✅ <b>Order Successful!</b>\nViews are coming to: <code>{clean_url}</code>", parse_mode=ParseMode.HTML)
    else:
        stats['failed'] += 1
        await status_msg.edit_text("❌ <b>All Proxies Failed.</b> Server is very busy, try after some time.")

# Admin Stats
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = f"📊 <b>STATS</b>\nSuccess: {stats['success']}\nFailed: {stats['failed']}\nLive Proxies: {len(core.proxies)}"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=core.hunter_worker, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("proxies", lambda u,c: u.message.reply_text(f"Live: {len(core.proxies)}")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.run_polling()
