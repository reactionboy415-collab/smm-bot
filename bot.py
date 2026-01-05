import asyncio, aiohttp, sqlite3, time, re, random, string, signal, os, gc
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ================= 🌐 HEALTH CHECK SERVER =================
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "🚀 SMM Bot v23 - System Online", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ================= ⚙️ CONFIGURATION =================
BOT_TOKEN = "7963420197:AAGkT11vdj3rhmbS2AHYw1wF9nE94ngQ1EA"
ADMIN_ID = 7840042951

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
]

PROXY_SOURCES = [
    "https://proxy-bot-g34t.onrender.com/api/raw?type=http&qty=50000",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
]

TEST_URL = "https://fameviso.com/free-instagram-views/"
total_scanned = 0

# ================= 🗄️ DATABASE SYSTEM =================
db = sqlite3.connect("proxy_pool.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS proxies (proxy TEXT PRIMARY KEY, last_ok INTEGER, fail_count INTEGER DEFAULT 0)")
db.commit()

def get_best_proxy():
    cur.execute("SELECT proxy FROM proxies WHERE fail_count < 3 ORDER BY last_ok DESC LIMIT 100")
    results = cur.fetchall()
    return random.choice(results)[0] if results else None

def mark_fail(proxy):
    cur.execute("UPDATE proxies SET fail_count = fail_count + 1 WHERE proxy = ?", (proxy,))
    cur.execute("DELETE FROM proxies WHERE fail_count > 4")
    db.commit()

# ================= 🛰️ PROXY HUNTER =================
async def test_proxy(session, proxy, semaphore):
    global total_scanned
    async with semaphore:
        total_scanned += 1
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            async with session.get(TEST_URL, proxy=f"http://{proxy}", timeout=5, headers=headers) as r:
                if r.status == 200 and 'csrf_token' in await r.text():
                    cur.execute("INSERT OR REPLACE INTO proxies (proxy, last_ok, fail_count) VALUES (?, ?, 0)", (proxy, int(time.time())))
                    db.commit()
        except: pass

async def proxy_worker():
    sem = asyncio.Semaphore(100)
    async with aiohttp.ClientSession() as session:
        while True:
            all_p = set()
            for src in PROXY_SOURCES:
                try:
                    async with session.get(src, timeout=20) as r:
                        for m in re.finditer(r'\d+\.\d+\.\d+\.\d+:\d+', await r.text()): all_p.add(m.group())
                except: continue
            p_list = list(all_p); random.shuffle(p_list)
            for i in range(0, len(p_list), 200):
                await asyncio.gather(*[test_proxy(session, p, sem) for p in p_list[i:i+200]])
                gc.collect(); await asyncio.sleep(1)
            await asyncio.sleep(300)

# ================= 💥 BYPASS ENGINE =================
async def run_attack(url, proxy):
    boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Origin": "https://fameviso.com",
        "Referer": TEST_URL,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "X-Requested-With": "XMLHttpRequest"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(TEST_URL, proxy=f"http://{proxy}", timeout=8) as r:
                csrf = re.search(r'name="csrf_token" value="(.*?)"', await r.text()).group(1)

            payload_base = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{url}\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n")

            d1 = payload_base + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n"
            async with session.post(f"{TEST_URL}submitForm.php", data=d1, proxy=f"http://{proxy}", timeout=10) as r:
                res1 = await r.json()

            server_msg = res1.get("message", "Unknown Error")

            if res1.get("status") == "tasks":
                token = res1.get("request_token")
                for task in res1.get('tasks', []):
                    t_pay = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                             f"--{boundary}\r\nContent-Disposition: form-data; name=\"task_id\"\r\n\r\n{task['id']}\r\n"
                             f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n"
                             f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ntask_finish\r\n--{boundary}--\r\n")
                    await session.post(f"{TEST_URL}submitForm.php", data=t_pay, proxy=f"http://{proxy}", timeout=8)
                
                d2 = payload_base + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n" + \
                                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                async with session.post(f"{TEST_URL}submitForm.php", data=d2, proxy=f"http://{proxy}", timeout=10) as r:
                    res_final = await r.text()
                    if "success" in res_final.lower(): return True, "Success"
                    return False, "Verification Failed"
            
            return False, server_msg
        except Exception: return False, "Proxy Connection Error"

# ================= 🤖 HANDLERS =================
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "✨ *WELCOME TO SMM MASTER V23* ✨\n\n"
        "🚀 *The Fastest Instagram Views Bot*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📍 *How to use:*\n"
        "Just send your Instagram Reel/Post link below.\n\n"
        "✅ *Features:*\n"
        "• 50,000+ Fresh Proxies Hourly\n"
        "• Anti-Block Technology\n"
        "• Real Server Response Logs\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📢 *Status:* `SYSTEM ONLINE`"
    )
    await u.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

async def handle_dispatch(u: Update, c: ContextTypes.DEFAULT_TYPE):
    url = u.message.text
    if "instagram.com" not in url:
        return await u.message.reply_text("❌ *Invalid Link!* Please send a valid Instagram URL.", parse_mode=ParseMode.MARKDOWN)
    
    status_msg = await u.message.reply_text("🔍 *Searching for a high-speed node...*", parse_mode=ParseMode.MARKDOWN)
    
    last_response = "No response"
    
    for i in range(1, 11):
        proxy = get_best_proxy()
        if not proxy: 
            return await status_msg.edit_text("⏳ *Proxy pool warming up...* Try in 60 seconds.")
        
        await status_msg.edit_text(f"🚀 *Attempt {i}/10*\n📡 Connecting via: `{proxy}`", parse_mode=ParseMode.MARKDOWN)
        success, server_text = await run_attack(url, proxy)
        
        if success:
            final_text = (
                "✅ *MISSION SUCCESSFUL*\n\n"
                f"🔗 *Link:* `{url}`\n"
                "⚡ *Status:* Views Sent to Server\n"
                "📝 *Message:* `The process is being processed...`"
            )
            return await status_msg.edit_text(final_text, parse_mode=ParseMode.MARKDOWN)
        else:
            last_response = server_text
            mark_fail(proxy)
            # Stop if server says limit reached
            if any(word in server_text.lower() for word in ["limit", "already", "daily"]):
                break

    fail_text = (
        "❌ *SUBMISSION FAILED*\n\n"
        f"📩 *Server Message:* `{last_response}`\n\n"
        "💡 *Hint:* If it says 'Already Claimed', the server has blocked this link for 24 hours."
    )
    await status_msg.edit_text(fail_text, parse_mode=ParseMode.MARKDOWN)

async def proxies_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != ADMIN_ID: return
    cur.execute("SELECT COUNT(*) FROM proxies"); count = cur.fetchone()[0]
    await u.message.reply_text(f"📊 *ADMIN DASHBOARD*\n━━━━━━━━━━━━━━\n✅ Active Proxies: `{count}`\n📡 Sources: `3` Sources", parse_mode=ParseMode.MARKDOWN)

# ================= ⚙️ MAIN =================
async def main():
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("proxies", proxies_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_dispatch))
    p_task = asyncio.create_task(proxy_worker())
    async with app:
        await app.initialize(); await app.start(); await app.updater.start_polling()
        stop = asyncio.Event(); loop = asyncio.get_running_loop()
        for s in (signal.SIGINT, signal.SIGTERM):
            try: loop.add_signal_handler(s, stop.set)
            except: pass
        await stop.wait(); p_task.cancel(); await app.shutdown()

if __name__ == "__main__":
    try: asyncio.run(main())
    except (KeyboardInterrupt, SystemExit): pass
