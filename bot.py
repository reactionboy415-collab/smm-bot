import asyncio, random, re, requests, httpx, time, threading, string, json
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- SECTION 1: FLASK UPTIME ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "SMM Master Pro is Active 🚀", 200
def run_flask(): web_app.run(host='0.0.0.0', port=10000)

# --- SECTION 2: CONFIG & DB ---
TOKEN = "7963420197:AAGtGASUJo9viBUFa_fuhVtWAo53eRioplY"
ADMIN_ID = 7840042951
CHANNEL_ID = -1003470556336 
CHANNEL_LINK = "https://t.me/+o0Pj60A5oI0zMmU1" 

user_db = {} 
reel_db = {}
stats = {"total_orders": 0, "success": 0, "failed": 0}

class ProEngine:
    def __init__(self):
        self.proxies = []
        self.proxy_sources = [
            "https://proxy-bot-g34t.onrender.com/api/raw?type=http&qty=500",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
        ]

    # --- NEW: URL PURIFIER ---
    def purify_url(self, raw_url):
        """Removes ?igsh= and other parameters, returns clean URL with trailing slash"""
        # Regex to find the base URL (reels/reel/p)
        match = re.search(r'(https?://(?:www\.)?instagram\.com/(?:reels|reel|p)/[A-Za-z0-9_-]+)', raw_url)
        if match:
            clean_url = match.group(1)
            if not clean_url.endswith('/'): clean_url += '/'
            return clean_url
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
                    if requests.get("https://fameviso.com/", proxies={"http": f"http://{p}"}, timeout=3).status_code == 200:
                        valid.append(f"http://{p}")
                        if len(valid) >= 40: break
                except: continue
            if valid: self.proxies = valid
            time.sleep(120)

    async def attack(self, clean_url):
        proxy = random.choice(self.proxies) if self.proxies else None
        boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        ua = f"Mozilla/5.0 (Linux; Android 14; SM-G99{random.randint(1,9)}B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.{random.randint(1000,9999)} Mobile Safari/537.36"
        fp = f"fp_{int(time.time()*1000)}"
        ext_ua = f"Fingerprint: {fp} | User-agent: {ua}"

        headers = {
            "authority": "fameviso.com",
            "content-type": f"multipart/form-data; boundary={boundary}",
            "user-agent": ua,
            "x-requested-with": "XMLHttpRequest",
            "origin": "https://fameviso.com",
            "referer": "https://fameviso.com/free-instagram-views/"
        }

        async with httpx.AsyncClient(proxies=proxy, http2=True, timeout=30.0, verify=False) as client:
            try:
                land = await client.get("https://fameviso.com/free-instagram-views/")
                csrf = re.search(r'name=\"csrf_token\" value=\"(.*?)\"', land.text).group(1)
                await asyncio.sleep(random.uniform(2, 4)) 

                base_payload = (
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{clean_url}\r\n"
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n"
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"extended_user_agent\"\r\n\r\n{ext_ua}\r\n"
                )

                r1 = await client.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                      content=(base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n").encode('utf-8'), 
                                      headers=headers)
                
                if r1.json().get("status") == "proceed":
                    token = r1.json().get("request_token")
                    await asyncio.sleep(3) 
                    data2 = base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                    r2 = await client.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", content=data2.encode('utf-8'), headers=headers)
                    return "success" in r2.text, proxy
                return False, proxy
            except: return False, proxy

core = ProEngine()

# --- SECTION 3: BOT LOGIC ---
async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except: return False

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    raw_url = update.message.text
    if "instagram.com" not in raw_url: return
    
    # Force Join Check
    if not await is_member(user.id, context):
        btn = [[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]]
        return await update.message.reply_text("❌ <b>Access Denied!</b>\n\nPlease join our channel first to use this bot.", 
                                              reply_markup=InlineKeyboardMarkup(btn), parse_mode=ParseMode.HTML)

    # Clean the URL automatically
    clean_url = core.purify_url(raw_url)
    if not clean_url:
        return await update.message.reply_text("❌ Invalid Instagram Link format.")

    # Extract ID for database tracking
    reel_id = re.search(r'/(?:reels|reel|p)/([A-Za-z0-9_-]+)', clean_url).group(1)

    now = time.time()
    if user.id in user_db and now - user_db[user.id] < 86400:
        return await update.message.reply_text("⏳ <b>Cooldown:</b> Please wait 24h.")
    if reel_id in reel_db and now - reel_db[reel_id] < 86400:
        return await update.message.reply_text("⚠️ <b>Reel Block:</b> Views already sent.")

    status_msg = await update.message.reply_text(f"⚡ <b>Purifying Link & Bypassing...</b>\n<code>{clean_url}</code>", parse_mode=ParseMode.HTML)
    
    stats['total_orders'] += 1
    success, px = await core.attack(clean_url)
    
    if success:
        user_db[user.id] = now
        reel_db[reel_id] = now
        stats['success'] += 1
        await status_msg.edit_text(f"✅ <b>Success!</b>\nViews are sent to: <code>{clean_url}</code>", parse_mode=ParseMode.HTML)
        await context.bot.send_message(ADMIN_ID, f"🔔 <b>Success</b>\nUser: {user.first_name}\nURL: {clean_url}")
    else:
        stats['failed'] += 1
        await status_msg.edit_text("❌ <b>Failed:</b> Server busy or Invalid Link. Try again later.")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=core.hunter_worker, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("🚀 Send IG Link!")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.run_polling()
