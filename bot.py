import asyncio, random, re, requests, httpx, time, threading, string
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- FLASK UPTIME ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "SMM Master Pro is Active 🚀", 200
def run_flask(): web_app.run(host='0.0.0.0', port=10000)

# --- CONFIG & DB ---
TOKEN = "7963420197:AAGtGASUJo9viBUFa_fuhVtWAo53eRioplY"
ADMIN_ID = 7840042951
CHANNEL_ID = -1003470556336 
CHANNEL_LINK = "https://t.me/+o0Pj60A5oI0zMmU1" 

user_db = {} 
reel_db = {}
stats = {"total_orders": 0, "success": 0, "failed": 0, "active_users": set()}

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
            raw_ips = self.manual_proxies.copy()
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
                    if requests.get("https://fameviso.com/", proxies={"http": p_form}, timeout=3).status_code == 200:
                        valid.append(p_form)
                        if len(valid) >= 50: break
                except: continue
            self.proxies = valid
            time.sleep(120)

    async def attack(self, clean_url, update, context):
        # --- LIVE REPORT TO ADMIN ---
        user = update.effective_user
        async def admin_log(step_msg):
            try: await context.bot.send_message(ADMIN_ID, f"🛠 <b>Live Log:</b> {user.first_name}\n📡 {step_msg}", parse_mode=ParseMode.HTML)
            except: pass

        if not self.proxies:
            return False, "No Proxy"

        proxy = random.choice(self.proxies)
        await admin_log(f"Proxy Selected: <code>{proxy}</code>\nTarget: {clean_url}")

        boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        ua = f"Mozilla/5.0 (Linux; Android 14; SM-G99{random.randint(1,9)}B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.{random.randint(1000,9999)} Mobile Safari/537.36"
        ext_ua = f"Fingerprint: fp_{int(time.time()*1000)} | User-agent: {ua}"

        headers = {"authority": "fameviso.com", "content-type": f"multipart/form-data; boundary={boundary}", "user-agent": ua, "origin": "https://fameviso.com", "referer": "https://fameviso.com/free-instagram-views/"}

        async with httpx.AsyncClient(proxies=proxy, http2=True, timeout=20.0, verify=False) as client:
            try:
                # Step 1
                await admin_log("Fetching CSRF Token...")
                land = await client.get("https://fameviso.com/free-instagram-views/")
                csrf = re.search(r'name=\"csrf_token\" value=\"(.*?)\"', land.text).group(1)
                
                await asyncio.sleep(2) # Human delay
                
                base_payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                                f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                                f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{clean_url}\r\n"
                                f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n"
                                f"--{boundary}\r\nContent-Disposition: form-data; name=\"extended_user_agent\"\r\n\r\n{ext_ua}\r\n")

                await admin_log("Sending Initial Request (Step 1)...")
                r1 = await client.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                      content=(base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n").encode('utf-8'), headers=headers)
                
                res1 = r1.json()
                if res1.get("status") == "proceed":
                    token = res1.get("request_token")
                    await admin_log(f"Step 1 Success. Token: {token[:10]}... Wait 3s.")
                    await asyncio.sleep(3)
                    
                    # Step 2
                    await admin_log("Finalizing Dispatch (Step 2)...")
                    data2 = base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                    r2 = await client.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", content=data2.encode('utf-8'), headers=headers)
                    
                    return "success" in r2.text, proxy
                return False, proxy
            except Exception as e:
                await admin_log(f"Error in Engine: {str(e)}")
                return False, proxy

core = ProEngine()

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats["active_users"].add(update.effective_user.id)
    await update.message.reply_text("🚀 <b>Professional IG Views Bot</b>\nSend Reel Link for 250 views.", parse_mode=ParseMode.HTML)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = (f"📊 <b>LIVE SYSTEM STATS</b>\n\n"
           f"✅ Success: {stats['success']}\n"
           f"❌ Failed: {stats['failed']}\n"
           f"📦 Total: {stats['total_orders']}\n"
           f"🌐 Proxies: {len(core.proxies)}\n"
           f"👥 Users: {len(stats['active_users'])}")
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def add_proxies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    new_ips = update.message.text.split('/add ')[1].split()
    core.manual_proxies.extend(new_ips)
    await update.message.reply_text(f"✅ Added {len(new_ips)} proxies to manual list.")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    raw_url = update.message.text
    if "instagram.com" not in raw_url: return

    # Check Membership
    try:
        m = await context.bot.get_chat_member(CHANNEL_ID, user.id)
        if m.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await update.message.reply_text(f"❌ Join first: {CHANNEL_LINK}")
    except: pass

    clean_url = core.purify_url(raw_url)
    if not clean_url: return await update.message.reply_text("❌ Invalid Link.")

    reel_id = re.search(r'/(?:reels|reel|p)/([A-Za-z0-9_-]+)', clean_url).group(1)
    now = time.time()
    if user.id in user_db and now - user_db[user.id] < 86400:
        return await update.message.reply_text("⏳ Wait 24h.")
    if reel_id in reel_db and now - reel_db[reel_id] < 86400:
        return await update.message.reply_text("⚠️ Views already sent.")

    status_msg = await update.message.reply_text("🔄 <b>Processing... Admin is tracking live.</b>", parse_mode=ParseMode.HTML)
    
    stats['total_orders'] += 1
    success, px = await core.attack(clean_url, update, context)
    
    if success:
        user_db[user.id], reel_db[reel_id] = now, now
        stats['success'] += 1
        await status_msg.edit_text(f"✅ <b>Views Sent Successfully!</b>\nTarget: {clean_url}", parse_mode=ParseMode.HTML)
    else:
        stats['failed'] += 1
        await status_msg.edit_text("❌ Server Busy. Admin informed.")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=core.hunter_worker, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("add", add_proxies))
    app.add_handler(CommandHandler("proxies", lambda u,c: u.message.reply_text(f"Live: {len(core.proxies)}\nList: {core.proxies[:10]}")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.run_polling()
