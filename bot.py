import asyncio, random, re, requests, time, threading, string
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- SECTION 1: FLASK ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "SMM Master Pro V7 Anti-Block is Active 🚀", 200
def run_flask(): web_app.run(host='0.0.0.0', port=10000)

# --- SECTION 2: CONFIG ---
TOKEN = "7963420197:AAGtGASUJo9viBUFa_fuhVtWAo53eRioplY"
ADMIN_ID = 7840042951
CHANNEL_ID = -1003470556336 
CHANNEL_LINK = "https://t.me/+o0Pj60A5oI0zMmU1" 

stats = {"success": 0, "failed": 0, "total": 0, "users": set()}

class AntiBlockEngine:
    def __init__(self):
        self.priority_pool = []
        self.public_pool = []
        self.sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
        ]

    def hunter_worker(self):
        """Advanced Proxy Scraper with Real-Site Validation"""
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
                    # Deep Validation: Check if it can reach the landing page
                    with requests.get("https://fameviso.com/free-instagram-views/", proxies={"http": p_form, "https": p_form}, timeout=3) as r:
                        if r.status_code == 200 and "csrf_token" in r.text:
                            valid.append(p_form)
                            if len(valid) >= 50: break
                except: continue
            self.public_pool = valid
            time.sleep(120)

    def attack(self, clean_url, user_name, context):
        def send_admin(msg):
            try: context.bot.send_message(ADMIN_ID, f"📡 <b>Live Tracker:</b> {user_name}\n{msg}", parse_mode=ParseMode.HTML)
            except: pass

        test_pool = self.priority_pool + self.public_pool
        if not test_pool: return False, "No Proxy"

        send_admin(f"🔥 <b>Anti-Block Engine Engaged!</b>\nTarget: {clean_url}")

        for attempt in range(1, 26): # Increased attempts to 25
            proxy = random.choice(test_pool)
            send_admin(f"Attempt {attempt}/25 | IP: <code>{proxy}</code>")

            session = requests.Session()
            session.proxies = {"http": proxy, "https": proxy}
            
            # Dynamic Identity Generation
            boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36"
            ]
            ua = random.choice(user_agents)

            try:
                # Step 1: CSRF with Human Delay
                time.sleep(random.uniform(1.5, 3.0))
                land = session.get("https://fameviso.com/free-instagram-views/", timeout=12)
                csrf = re.search(r'name=\"csrf_token\" value=\"(.*?)\"', land.text).group(1)
                
                payload_parts = {
                    "csrf_token": csrf,
                    "service": "8061",
                    "photoLink": clean_url,
                    "viewsQuantity": "250",
                    "extended_user_agent": f"Fingerprint: fp_{int(time.time()*1000)} | {ua}",
                    "action_type": "initial_request"
                }

                # Construct Multipart Manually for maximum control
                def build_data(data_dict, bnd):
                    body = ""
                    for k, v in data_dict.items():
                        body += f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n"
                    return body + f"--{bnd}--\r\n"

                # Step 2: Initial Request
                r1 = session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                 data=build_data(payload_parts, boundary).encode('utf-8'), 
                                 headers={"content-type": f"multipart/form-data; boundary={boundary}", "user-agent": ua}, timeout=15)
                
                res1 = r1.json()
                if res1.get("status") == "proceed":
                    token = res1.get("request_token")
                    send_admin(f"✨ Step 1 Success! Token: <code>{token[:8]}...</code>")
                    
                    time.sleep(random.uniform(3.5, 5.0)) # Critical delay
                    
                    payload_parts["request_token"] = token
                    payload_parts["action_type"] = "verify_request"
                    
                    # Step 3: Final Dispatch
                    r2 = session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                     data=build_data(payload_parts, boundary).encode('utf-8'), 
                                     headers={"content-type": f"multipart/form-data; boundary={boundary}", "user-agent": ua}, timeout=15)
                    
                    if "success" in r2.text.lower():
                        send_admin("🏆 <b>VICTORY!</b> Views dispatched to Instagram.")
                        return True, proxy
                
                send_admin("❌ Rejected by Fameviso Server.")
            except Exception as e:
                send_admin(f"⚠️ Connection Error: {str(e)[:40]}")
                if proxy in test_pool: test_pool.remove(proxy)
                continue
                
        return False, "Exhausted"

core = AntiBlockEngine()

# --- ADMIN HANDLERS ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    if not msg: return await update.message.reply_text("Usage: /broadcast Hello")
    count = 0
    for uid in stats["users"]:
        try:
            await context.bot.send_message(uid, f"📢 <b>Announcement:</b>\n\n{msg}", parse_mode=ParseMode.HTML)
            count += 1
        except: continue
    await update.message.reply_text(f"✅ Sent to {count} users.")

async def add_proxies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    ips = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', update.message.text)
    if not ips: return await update.message.reply_text("❌ Give me IP:PORT list.")
    core.priority_pool = [f"http://{i}" for i in ips] + core.priority_pool
    await update.message.reply_text(f"👑 <b>Master, {len(ips)} Priority IPs Added!</b>")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    stats["users"].add(user.id)
    if "instagram.com" not in update.message.text: return

    match = re.search(r'(https?://(?:www\.)?instagram\.com/(?:reels|reel|p)/[A-Za-z0-9_-]+)', update.message.text)
    if not match: return
    clean_url = match.group(1) + "/"

    status_msg = await update.message.reply_text("🛸 <b>Bypassing Security Cloud...</b>\nRotation started.", parse_mode=ParseMode.HTML)
    
    stats["total"] += 1
    loop = asyncio.get_event_loop()
    success, px = await loop.run_in_executor(None, core.attack, clean_url, user.first_name, context)
    
    if success:
        stats["success"] += 1
        await status_msg.edit_text(f"✅ <b>Mission Accomplished!</b>\nViews sent to: <code>{clean_url}</code>", parse_mode=ParseMode.HTML)
    else:
        stats["failed"] += 1
        await status_msg.edit_text("❌ <b>Security Level High.</b>\nFameviso rejected all IPs. Please add fresh proxies with /add or try after 1 hour.")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=core.hunter_worker, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("🔥 <b>SMM Masterpiece V7 Ready!</b>")))
    app.add_handler(CommandHandler("stats", lambda u,c: u.message.reply_text(f"📊 Stats\nSuccess: {stats['success']}\nTotal: {stats['total']}")))
    app.add_handler(CommandHandler("add", add_proxies))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.run_polling()
