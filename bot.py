import asyncio, random, re, requests, httpx, time, threading, string
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- FLASK SERVER ---
web_app = Flask(__name__)
@web_app.route('/')
def health_check(): return "Bot is Running!", 200
def run_flask(): web_app.run(host='0.0.0.0', port=10000)

# --- CONFIGURATION ---
TOKEN = "7963420197:AAGvcP9RnHZ-fxJvRzWj774HeGXELg4Mhig"
CHANNEL_ID = -1003470556336
LOG_GROUP_ID = -1003619580926

# Tracking Databases
user_cooldowns = {}   # Tracks User ID
reel_cooldowns = {}   # Tracks Reel ID (Global)

class SMMCore:
    def __init__(self):
        self.leofame_main = "https://leofame.com/free-instagram-views"
        self.leofame_api = "https://leofame.com/free-instagram-views?api=1"
        self.fameviso_api = "https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php"
        self.my_proxy_api = "https://proxy-bot-g34t.onrender.com/api/raw?type=http&qty=500"
        self.github_sources = ["https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"]
        self.working_proxies = []

    def proxy_hunter_worker(self):
        while True:
            all_raw = []
            try:
                r = requests.get(self.my_proxy_api, timeout=10)
                if r.status_code == 200: all_raw.extend(r.text.splitlines())
            except: pass
            all_raw = list(set([p.strip() for p in all_raw if ":" in p]))
            random.shuffle(all_raw)
            temp_working = []
            for p in all_raw[:50]:
                try:
                    px = {"http": f"http://{p}", "https": f"http://{p}"}
                    if requests.get("https://fameviso.com/", proxies=px, timeout=3).status_code == 200:
                        temp_working.append(px)
                        if len(temp_working) >= 30: break
                except: continue
            if temp_working: self.working_proxies = temp_working
            time.sleep(60)

    def get_best_proxy(self):
        return random.choice(self.working_proxies) if self.working_proxies else None

    def _extract_id(self, link):
        match = re.search(r'/(?:reels|reel|p)/([A-Za-z0-9_-]+)', link)
        return match.group(1) if match else None

    # ENGINE 1: LEOFAME
    async def fire_leofame(self, link):
        proxy = self.get_best_proxy()
        session = requests.Session()
        if proxy: session.proxies = proxy
        try:
            r = session.get(self.leofame_main, timeout=10)
            token = re.search(r'name="token" value="([a-f0-9]+)"', r.text).group(1)
            payload = {"token": token, "timezone_offset": "Asia/Calcutta", "free_link": link, "quantity": "200"}
            resp = session.post(self.leofame_api, data=payload, timeout=15)
            return '"success":"Success"' in resp.text
        except: return False

    # ENGINE 2: FAMEVISO
    async def fire_fameviso(self, link):
        proxy = self.get_best_proxy()
        boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        headers = {"authority": "fameviso.com", "content-type": f"multipart/form-data; boundary={boundary}", "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
        proxy_url = proxy['http'] if proxy else None
        async with httpx.AsyncClient(proxies=proxy_url, timeout=20.0, verify=False) as client:
            try:
                land = await client.get("https://fameviso.com/free-instagram-views/")
                csrf = re.search(r'name="csrf_token" value="(.*?)"', land.text).group(1)
                base = f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{link}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n"
                # Step 1
                r1 = await client.post(self.fameviso_api, content=(base + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n").encode('utf-8'), headers=headers)
                res1 = r1.json()
                if res1.get("status") == "proceed":
                    token = res1.get("request_token")
                    # Step 2
                    p2 = base + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                    r2 = await client.post(self.fameviso_api, content=p2.encode('utf-8'), headers=headers)
                    return "success" in r2.text
                return False
            except: return False

smm = SMMCore()

# --- HANDLERS ---
async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except: return False

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text
    if "instagram.com" not in url: return
    if not await check_membership(user.id, context): return
    
    reel_id = smm._extract_id(url)
    if not reel_id: return
    
    current_time = time.time()
    
    # 1. User Daily Limit Check
    if user.id in user_cooldowns and current_time - user_cooldowns[user.id] < 86400:
        return await update.message.reply_text("⏳ <b>Limit:</b> You can get 200 views once every 24 hours.", parse_mode=ParseMode.HTML)

    # 2. Global Reel Tracking Check
    if reel_id in reel_cooldowns and current_time - reel_cooldowns[reel_id] < 86400:
        return await update.message.reply_text("⚠️ <b>Duplicate Order:</b> This reel has already received 200 free views. Our server detected it. Please try again after 24 hours.", parse_mode=ParseMode.HTML)

    status_msg = await update.message.reply_text("🚀 <b>Processing your request...</b>", parse_mode=ParseMode.HTML)
    
    # Attempt Delivery
    success = await smm.fire_leofame(url)
    if not success:
        await status_msg.edit_text("🔄 Server 1 busy, trying backup engine...")
        success = await smm.fire_fameviso(url)

    if success:
        user_cooldowns[user.id] = current_time
        reel_cooldowns[reel_id] = current_time
        await status_msg.edit_text("✅ <b>Success!</b> 200 Views are on the way.")
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=f"💎 <b>ORDER</b>\n👤 {user.first_name}\n🔗 {url}", parse_mode=ParseMode.HTML)
    else:
        await status_msg.edit_text("❌ All servers are busy. Please try again later.")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=smm.proxy_hunter_worker, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("Send IG Link for 200 Views!")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    app.run_polling()
