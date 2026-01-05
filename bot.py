import asyncio, aiohttp, sqlite3, time, re, random, string, signal, os, gc
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from fake_useragent import UserAgent

# ================= 🌐 HEALTH CHECK SERVER =================
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "🚀 SMM Bot v19 - Massive Proxy Mode!", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ================= ⚙️ CONFIGURATION =================
BOT_TOKEN = "7963420197:AAGkT11vdj3rhmbS2AHYw1wF9nE94ngQ1EA"
ADMIN_ID = 7840042951
ua_gen = UserAgent()

# Added your new massive source + existing ones
PROXY_SOURCES = [
    "https://proxy-bot-g34t.onrender.com/api/raw?type=http&qty=300000",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
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
    cur.execute("SELECT proxy FROM proxies WHERE fail_count < 3 ORDER BY last_ok DESC LIMIT 50")
    results = cur.fetchall()
    return random.choice(results)[0] if results else None

def mark_fail(proxy):
    cur.execute("UPDATE proxies SET fail_count = fail_count + 1 WHERE proxy = ?", (proxy,))
    cur.execute("DELETE FROM proxies WHERE fail_count > 5")
    db.commit()

# ================= 🛰️ ADVANCED HUNTER ENGINE =================
async def test_proxy(session, proxy, semaphore):
    global total_scanned
    async with semaphore:
        total_scanned += 1
        try:
            # Random UA for every test
            headers = {'User-Agent': ua_gen.random}
            async with session.get(TEST_URL, proxy=f"http://{proxy}", timeout=5, headers=headers) as r:
                if r.status == 200:
                    text = await r.text()
                    if 'csrf_token' in text:
                        cur.execute("INSERT OR REPLACE INTO proxies (proxy, last_ok, fail_count) VALUES (?, ?, 0)", (proxy, int(time.time())))
                        db.commit()
        except: pass

async def proxy_worker():
    # Semaphores protect from crashing the CPU
    sem = asyncio.Semaphore(150) 
    async with aiohttp.ClientSession() as session:
        while True:
            all_proxies = set()
            for source in PROXY_SOURCES:
                try:
                    async with session.get(source, timeout=20) as r:
                        text = await r.text()
                        found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', text)
                        all_proxies.update(found)
                        print(f"Fetched {len(found)} from {source}")
                except: continue
            
            p_list = list(all_proxies)
            random.shuffle(p_list)
            
            # Rapid testing in batches of 300 to keep RAM low
            for i in range(0, len(p_list), 300):
                batch = p_list[i:i+300]
                await asyncio.gather(*[test_proxy(session, p, sem) for p in batch])
                gc.collect() # Clean memory
                await asyncio.sleep(0.5)
            
            await asyncio.sleep(300) # Full re-scan every 5 mins

# ================= 💥 BYPASS ENGINE (WITH ADVANCED UA & HEADERS) =================
async def run_attack(url, proxy):
    boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    # Real Browser Header Rotation
    headers = {
        "User-Agent": ua_gen.random,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://fameviso.com",
        "Referer": "https://fameviso.com/free-instagram-views/",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "X-Requested-With": "XMLHttpRequest"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # 1. Get Token with Proxy
            async with session.get(TEST_URL, proxy=f"http://{proxy}", timeout=8) as r:
                page = await r.text()
                csrf = re.search(r'name="csrf_token" value="(.*?)"', page).group(1)

            # 2. Main Payload
            payload_base = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{url}\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n")

            # 3. Initial Request
            d1 = payload_base + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n"
            async with session.post(f"{TEST_URL}submitForm.php", data=d1, proxy=f"http://{proxy}", timeout=10) as r:
                res1 = await r.json()

            if res1.get("status") == "tasks":
                token = res1.get("request_token")
                for task in res1.get('tasks', []):
                    t_payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                                 f"--{boundary}\r\nContent-Disposition: form-data; name=\"task_id\"\r\n\r\n{task['id']}\r\n"
                                 f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n"
                                 f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ntask_finish\r\n--{boundary}--\r\n")
                    await session.post(f"{TEST_URL}submitForm.php", data=t_payload, proxy=f"http://{proxy}", timeout=8)
                
                # 4. Final Verify
                d2 = payload_base + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n" + \
                                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                async with session.post(f"{TEST_URL}submitForm.php", data=d2, proxy=f"http://{proxy}", timeout=10) as r:
                    resp_final = await r.text()
                    return "success" in resp_final.lower()
            return False
        except:
            return False

# ================= 🤖 HANDLERS =================
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("⏩ **SMM MASTER V19 (MAX PROXY MODE)**\nSend me Instagram link!")

async def handle_dispatch(u: Update, c: ContextTypes.DEFAULT_TYPE):
    url = u.message.text
    if "instagram.com" not in url: return
    
    m = await u.message.reply_text("🔎 **Searching High-Quality Node...**")
    
    for attempt in range(1, 16):
        proxy = get_best_proxy()
        if not proxy:
            return await m.edit_text("⏳ DB is empty. Hunter is scanning 300k proxies, please wait 1 min.")

        await m.edit_text(f"🚀 **Attempt {attempt}/15**\n📡 Node: `{proxy}`\n⚙️ Rotating User-Agent...")
        
        if await run_attack(url, proxy):
            return await m.edit_text("✅ **MISSION SUCCESSFUL!**\nViews are on the way.")
        else:
            mark_fail(proxy)
    
    await m.edit_text("❌ **All attempts failed.**\nThe website might have high security right now. Try again later.")

async def proxies_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != ADMIN_ID: return
    cur.execute("SELECT COUNT(*) FROM proxies")
    db_count = cur.fetchone()[0]
    await u.message.reply_text(f"📊 **ENGINE STATS**\n━━━━━━━━━━━━━━━\n✅ Active Proxies: `{db_count}`\n🔍 Total Scanned: `{total_scanned}`\n🌐 Sources: `4` (Inc. 300k API)")

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
            loop.add_signal_handler(s, stop.set)
        await stop.wait()
        p_task.cancel()
        await app.shutdown()

if __name__ == "__main__":
    try:
        async with asyncio.Runner() as runner:
            asyncio.run(main())
    except: pass
