import asyncio, random, re, requests, httpx, time, threading, string
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- FLASK UPTIME ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "SMM Master Pro V3.1 Fixed 🚀", 200
def run_flask(): web_app.run(host='0.0.0.0', port=10000)

# --- CONFIG ---
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
            # Combining manual and web proxies
            raw_ips = self.manual_proxies.copy()
            for src in self.proxy_sources:
                try:
                    res = requests.get(src, timeout=10)
                    if res.status_code == 200: raw_ips.extend(res.text.splitlines())
                except: continue
            
            raw_ips = list(set([i.strip() for i in raw_ips if ":" in i]))
            random.shuffle(raw_ips)
            
            valid = []
            for p in raw_ips[:150]:
                try:
                    p_form = f"http://{p}" if "://" not in p else p
                    # Pre-test
                    with requests.get("https://fameviso.com/", proxies={"http": p_form}, timeout=2) as r:
                        if r.status_code == 200:
                            valid.append(p_form)
                            if len(valid) >= 70: break
                except: continue
            self.proxies = valid
            time.sleep(180)

    async def attack(self, clean_url, update, context):
        user = update.effective_user
        async def admin_log(msg):
            try: await context.bot.send_message(ADMIN_ID, f"🛠 <b>Live Log:</b> {user.first_name}\n📡 {msg}", parse_mode=ParseMode.HTML)
            except: pass

        for attempt in range(1, 11):
            if not self.proxies:
                await admin_log("Waiting for working proxies...")
                await asyncio.sleep(3)
                continue

            proxy_url = random.choice(self.proxies)
            await admin_log(f"Attempt {attempt}/10\nProxy: <code>{proxy_url}</code>")

            boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            ua = f"Mozilla/5.0 (Linux; Android 14; SM-G99{random.randint(1,9)}B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.{random.randint(1000,9999)} Mobile Safari/537.36"
            ext_ua = f"Fingerprint: fp_{int(time.time()*1000)} | User-agent: {ua}"
            headers = {"authority": "fameviso.com", "content-type": f"multipart/form-data; boundary={boundary}", "user-agent": ua, "origin": "https://fameviso.com", "referer": "https://fameviso.com/free-instagram-views/"}

            try:
                # --- FIXED PROXY SYNTAX FOR NEW HTTPX ---
                async with httpx.AsyncClient(proxy=proxy_url, http2=True, timeout=15.0, verify=False) as client:
                    # Step 1
                    land = await client.get("https://fameviso.com/free-instagram-views/")
                    csrf = re.search(r'name=\"csrf_token\" value=\"(.*?)\"', land.text).group(1)
                    
                    base_payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{clean_url}\r\n"
                                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n"
                                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"extended_user_agent\"\r\n\r\n{ext_ua}\r\n")

                    r1 = await client.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                          content=(base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n").encode('utf-8'), headers=headers)
                    
                    if r1.json().get("status") == "proceed":
                        token = r1.json().get("request_token")
                        await asyncio.sleep(2)
                        data2 = base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                        r2 = await client.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", content=data2.encode('utf-8'), headers=headers)
                        if "success" in r2.text.lower():
                            return True, proxy_url

            except Exception as e:
                await admin_log(f"❌ Error: {str(e)[:40]}...")
                if proxy_url in self.proxies: self.proxies.remove(proxy_url)
                continue
        return False, "Failed"

core = ProEngine()

# --- ADMIN COMMANDS ---
async def add_proxies_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    # Message se saare IPs nikalne ke liye regex
    raw_text = update.message.text
    ips = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', raw_text)
    
    if not ips:
        return await update.message.reply_text("❌ No valid proxies found in your message.")
    
    core.manual_proxies.extend(ips)
    await update.message.reply_text(f"✅ <b>Successfully Added {len(ips)} Proxies!</b>\nThey will be used in current and future attacks.", parse_mode=ParseMode.HTML)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = f"📊 <b>STATS</b>\nSuccess: {stats['success']}\nFailed: {stats['failed']}\nLive Proxies: {len(core.proxies)}\nManual Pool: {len(core.manual_proxies)}"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# --- USER HANDLER ---
async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if "instagram.com" not in update.message.text: return
    
    clean_url = core.purify_url(update.message.text)
    if not clean_url: return

    status_msg = await update.message.reply_text("🔄 <b>Finding Working Proxy from Pool...</b>", parse_mode=ParseMode.HTML)
    stats['total'] += 1
    success, used_px = await core.attack(clean_url, update, context)
    
    if success:
        stats['success'] += 1
        await status_msg.edit_text(f"✅ <b>Order Placed!</b>\nTarget: <code>{clean_url}</code>", parse_mode=ParseMode.HTML)
    else:
        stats['failed'] += 1
        await status_msg.edit_text("❌ <b>All attempts failed.</b> Try again with better proxies.")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=core.hunter_worker, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("🚀 Send IG Link!")))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("add", add_proxies_fixed))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.run_polling()
