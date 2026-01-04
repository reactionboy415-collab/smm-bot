import asyncio, aiohttp, sqlite3, time, re, random, string, signal, os, gc
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= 🌐 HEALTH CHECK SERVER =================
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "🚀 SMM Bot Ultra Fast Mode!", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ================= ⚙️ CONFIGURATION =================
BOT_TOKEN = "7963420197:AAGkT11vdj3rhmbS2AHYw1wF9nE94ngQ1EA"
ADMIN_ID = 7840042951

# Added 10+ New Reliable Sources
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-tester/master/proxies.txt",
    "https://raw.githubusercontent.com/rooster127/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxyscan.io/download?type=http"
]

TEST_URL = "https://fameviso.com/free-instagram-views/"
total_scanned = 0

# ================= 🗄️ DATABASE SYSTEM =================
db = sqlite3.connect("proxy_pool.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS proxies (proxy TEXT PRIMARY KEY, last_ok INTEGER)")
db.commit()

def get_random_proxy():
    cur.execute("SELECT proxy FROM proxies ORDER BY RANDOM() LIMIT 1")
    r = cur.fetchone(); return r[0] if r else None

def remove_dead_proxy(proxy):
    cur.execute("DELETE FROM proxies WHERE proxy = ?", (proxy,)); db.commit()

# ================= 🛰️ ULTRA FAST HUNTER ENGINE =================
async def test_proxy(session, proxy, semaphore):
    global total_scanned
    async with semaphore:
        total_scanned += 1
        try:
            # Low timeout (4s) to skip slow proxies immediately
            async with session.get(TEST_URL, proxy=f"http://{proxy}", timeout=4) as r:
                if r.status == 200:
                    if "csrf_token" in await r.text():
                        cur.execute("INSERT OR REPLACE INTO proxies VALUES (?, ?)", (proxy, int(time.time())))
                        db.commit()
        except: pass

async def proxy_worker():
    # Performance Tuning: 100 concurrent tests for speed
    sem = asyncio.Semaphore(100) 
    connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
    
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            while True:
                all_proxies = set()
                # Fetching from all sources in parallel
                fetch_tasks = [session.get(url, timeout=15) for url in PROXY_SOURCES]
                responses = await asyncio.gather(*fetch_tasks, return_exceptions=True)
                
                for r in responses:
                    if isinstance(r, aiohttp.ClientResponse):
                        text = await r.text()
                        found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', text)
                        all_proxies.update(found)
                
                proxy_list = list(all_proxies)
                random.shuffle(proxy_list)

                # Rapid Fire Testing in Chunks
                for i in range(0, len(proxy_list), 200):
                    batch = proxy_list[i:i+200]
                    tasks = [test_proxy(session, p, sem) for p in batch]
                    await asyncio.gather(*tasks)
                    gc.collect() # Crucial for 490MB RAM
                    await asyncio.sleep(1) # Tiny pause to prevent CPU pegging

                await asyncio.sleep(180) # Re-scan every 3 mins
    except Exception as e:
        print(f"Worker Error: {e}")
        await asyncio.sleep(10)

# ================= 💥 BYPASS ENGINE =================
async def run_attack(url, proxy):
    clean_url = url.split('?')[0]
    if not clean_url.endswith('/'): clean_url += '/'
    boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    ua = f"Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.{random.randint(100,999)} Mobile Safari/537.36"
    headers = {"content-type": f"multipart/form-data; boundary={boundary}", "user-agent": ua}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(TEST_URL, proxy=f"http://{proxy}", timeout=6) as r:
                csrf = re.search(r'name="csrf_token" value="(.*?)"', await r.text()).group(1)

            payload_base = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{clean_url}\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n")

            d1 = payload_base + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n"
            async with session.post(f"{TEST_URL}submitForm.php", data=d1, headers=headers, proxy=f"http://{proxy}", timeout=7) as r:
                res1 = await r.json()

            if res1.get("status") == "tasks":
                token = res1.get("request_token")
                for task in res1.get('tasks', []):
                    t_payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                                 f"--{boundary}\r\nContent-Disposition: form-data; name=\"task_id\"\r\n\r\n{task['id']}\r\n"
                                 f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n"
                                 f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ntask_finish\r\n--{boundary}--\r\n")
                    await session.post(f"{TEST_URL}submitForm.php", data=t_payload, headers=headers, proxy=f"http://{proxy}", timeout=6)
                
                await asyncio.sleep(1)
                d2 = payload_base + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n" + \
                                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                async with session.post(f"{TEST_URL}submitForm.php", data=d2, headers=headers, proxy=f"http://{proxy}", timeout=7) as r:
                    return "success" in (await r.text()).lower()
            return res1.get("status") in ["success", "proceed"]
        except: return False

# ================= 🤖 HANDLERS =================
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("⏩ **SMM MASTER V17 (ULTRA SPEED)**\nDrop your link!")

async def proxies_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != ADMIN_ID: return
    cur.execute("SELECT COUNT(*) FROM proxies")
    db_count = cur.fetchone()[0]
    await u.message.reply_text(f"🚀 **LIVE ENGINE STATUS**\n━━━━━━━━━━━━━━━\n📡 Sources: `{len(PROXY_SOURCES)}` APIs\n✅ DB Ready: `{db_count}`\n🔍 Scanned: `{total_scanned}`")

async def handle_dispatch(u: Update, c: ContextTypes.DEFAULT_TYPE):
    url = u.message.text
    if "instagram.com" not in url: return
    m = await u.message.reply_text("⚡ **Fetching High-Speed Node...**")
    for attempt in range(1, 11):
        proxy = get_random_proxy()
        if not proxy: break
        await m.edit_text(f"🚀 Attempt {attempt}/10\nNode: `{proxy}`")
        if await run_attack(url, proxy):
            return await m.edit_text("✅ **MISSION SUCCESS**")
        remove_dead_proxy(proxy)
    await m.edit_text("❌ **FAILED**")

# ================= ⚙️ MAIN =================
async def main():
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("proxies", proxies_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_dispatch))
    p_task = asyncio.create_task(proxy_worker())
    async with app:
        await app.initialize(); await app.start()
        await app.updater.start_polling()
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        for s in (signal.SIGINT, signal.SIGTERM): loop.add_signal_handler(s, stop.set)
        await stop.wait()
        p_task.cancel(); await app.shutdown()

if __name__ == "__main__":
    try: asyncio.run(main())
    except (KeyboardInterrupt, SystemExit): pass
