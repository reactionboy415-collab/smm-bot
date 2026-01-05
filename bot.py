import asyncio, aiohttp, sqlite3, time, re, random, string, signal, os, gc
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from fake_useragent import UserAgent

# ================= 🌐 HEALTH CHECK SERVER =================
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "🚀 SMM Bot v20 - Ultra Stable", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ================= ⚙️ CONFIGURATION =================
BOT_TOKEN = "7963420197:AAGkT11vdj3rhmbS2AHYw1wF9nE94ngQ1EA"
ADMIN_ID = 7840042951
ua_gen = UserAgent()

PROXY_SOURCES = [
    "https://proxy-bot-g34t.onrender.com/api/raw?type=http&qty=50000", # Reduced qty slightly to save RAM
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
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

# ================= 🛰️ ADVANCED HUNTER ENGINE =================
async def test_proxy(session, proxy, semaphore):
    global total_scanned
    async with semaphore:
        total_scanned += 1
        try:
            headers = {'User-Agent': ua_gen.random}
            async with session.get(TEST_URL, proxy=f"http://{proxy}", timeout=5, headers=headers) as r:
                if r.status == 200:
                    text = await r.text()
                    if 'csrf_token' in text:
                        cur.execute("INSERT OR REPLACE INTO proxies (proxy, last_ok, fail_count) VALUES (?, ?, 0)", (proxy, int(time.time())))
                        db.commit()
        except: pass

async def proxy_worker():
    sem = asyncio.Semaphore(100) # Balanced for Render/VPS
    async with aiohttp.ClientSession() as session:
        while True:
            all_proxies = set()
            for source in PROXY_SOURCES:
                try:
                    async with session.get(source, timeout=30) as r:
                        text = await r.text()
                        # Use iterator to save memory on large text
                        for match in re.finditer(r'\d+\.\d+\.\d+\.\d+:\d+', text):
                            all_proxies.add(match.group())
                except: continue
            
            p_list = list(all_proxies)
            random.shuffle(p_list)
            
            # Batch testing to prevent CPU spikes
            for i in range(0, len(p_list), 200):
                batch = p_list[i:i+200]
                await asyncio.gather(*[test_proxy(session, p, sem) for p in batch])
                gc.collect() 
                await asyncio.sleep(1)
            
            await asyncio.sleep(300)

# ================= 💥 BYPASS ENGINE =================
async def run_attack(url, proxy):
    boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    headers = {
        "User-Agent": ua_gen.random,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": "https://fameviso.com",
        "Referer": "https://fameviso.com/free-instagram-views/",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "X-Requested-With": "XMLHttpRequest"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # 1. Fetch CSRF
            async with session.get(TEST_URL, proxy=f"http://{proxy}", timeout=10) as r:
                page = await r.text()
                csrf = re.search(r'name="csrf_token" value="(.*?)"', page).group(1)

            base_payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{url}\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n")

            # 2. Step 1 Request
            d1 = base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n"
            async with session.post(f"{TEST_URL}submitForm.php", data=d1, proxy=f"http://{proxy}", timeout=12) as r:
                res1 = await r.json()

            if res1.get("status") == "tasks":
                token = res1.get("request_token")
                for task in res1.get('tasks', []):
                    t_pay = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                             f"--{boundary}\r\nContent-Disposition: form-data; name=\"task_id\"\r\n\r\n{task['id']}\r\n"
                             f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n"
                             f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ntask_finish\r\n--{boundary}--\r\n")
                    await session.post(f"{TEST_URL}submitForm.php", data=t_pay, proxy=f"http://{proxy}", timeout=10)
                
                # 3. Verify
                d2 = base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n" + \
                                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                async with session.post(f"{TEST_URL}submitForm.php", data=d2, proxy=f"http://{proxy}", timeout=12) as r:
                    return "success" in (await r.text()).lower()
            return False
        except: return False

# ================= 🤖 HANDLERS =================
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("🔥 **SMM MASTER V20 ACTIVE**\nSend your Instagram link to start.")

async def handle_dispatch(u: Update, c: ContextTypes.DEFAULT_TYPE):
    url = u.message.text
    if "instagram.com" not in url: return
    
    msg = await u.message.reply_text("🔄 **Checking Proxy Health...**")
    
    for i in range(1, 11):
        proxy = get_best_proxy()
        if not proxy:
            return await msg.edit_text("❌ DB Empty. Waiting for hunter...")

        await msg.edit_text(f"🚀 **Attempt {i}/10**\n📡 Node: `{proxy}`")
        if await run_attack(url, proxy):
            return await msg.edit_text("✅ **SUCCESS! Views Sent.**")
        else:
            mark_fail(proxy)
    
    await msg.edit_text("❌ **All proxies failed. Site security is high.**")

async def proxies_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != ADMIN_ID: return
    cur.execute("SELECT COUNT(*) FROM proxies")
    count = cur.fetchone()[0]
    await u.message.reply_text(f"📊 **Bot Status**\nProxies in DB: `{count}`\nScanned today: `{total_scanned}`")

# ================= ⚙️ MAIN =================
async def main():
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("proxies", proxies_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_dispatch))
    
    p_task = asyncio.create_task(proxy_worker())
    
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        for s in (signal.SIGINT, signal.SIGTERM):
            try: loop.add_signal_handler(s, stop.set)
            except: pass
                
        await stop.wait()
        p_task.cancel()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit): pass
