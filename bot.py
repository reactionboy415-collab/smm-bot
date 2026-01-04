import asyncio
import aiohttp
import sqlite3
import time
import re
import random
import string
import signal
import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= 🌐 HEALTH CHECK SERVER =================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🚀 SMM Bot is Alive and Running!", 200

def run_web():
    # Cloud platforms provide PORT env variable
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# ================= ⚙️ CONFIGURATION =================
BOT_TOKEN = "7963420197:AAGkT11vdj3rhmbS2AHYw1wF9nE94ngQ1EA"
ADMIN_ID = 7840042951

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000"
]

TEST_URL = "https://fameviso.com/free-instagram-views/"
TIMEOUT = 6

# ================= 🗄️ DATABASE SYSTEM =================
db = sqlite3.connect("proxy_pool.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS proxies (proxy TEXT PRIMARY KEY, last_ok INTEGER)")
db.commit()

def get_random_proxy():
    cur.execute("SELECT proxy FROM proxies ORDER BY RANDOM() LIMIT 1")
    r = cur.fetchone()
    return r[0] if r else None

def remove_dead_proxy(proxy):
    cur.execute("DELETE FROM proxies WHERE proxy = ?", (proxy,))
    db.commit()

# ================= 🛰️ PROXY HUNTER ENGINE =================
async def fetch_source(session, url):
    try:
        async with session.get(url, timeout=10) as r:
            return await r.text()
    except: return ""

async def test_proxy(session, proxy):
    try:
        async with session.get(TEST_URL, proxy=f"http://{proxy}", timeout=TIMEOUT) as r:
            text = await r.text()
            return "csrf_token" in text
    except: return False

async def proxy_worker():
    try:
        async with aiohttp.ClientSession() as session:
            while True:
                texts = await asyncio.gather(*[fetch_source(session, u) for u in PROXY_SOURCES])
                all_proxies = []
                for t in texts:
                    for line in re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', t):
                        all_proxies.append(line.strip())

                random.shuffle(all_proxies)
                for i in range(0, len(all_proxies), 50):
                    batch = all_proxies[i:i + 50]
                    for proxy in batch:
                        if await test_proxy(session, proxy):
                            cur.execute("INSERT OR REPLACE INTO proxies VALUES (?, ?)", (proxy, int(time.time())))
                            db.commit()
                    await asyncio.sleep(20)
                await asyncio.sleep(600)
    except asyncio.CancelledError: pass

# ================= 💥 TASK BYPASS ATTACK ENGINE =================
async def run_attack(url, proxy):
    clean_url = url.split('?')[0]
    if not clean_url.endswith('/'): clean_url += '/'
    
    boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    ua = f"Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.{random.randint(100,999)} Mobile Safari/537.36"
    ext_ua = f"Fingerprint: fp_{int(time.time()*1000)} | User-agent: {ua}"

    headers = {
        "authority": "fameviso.com",
        "content-type": f"multipart/form-data; boundary={boundary}",
        "user-agent": ua,
        "x-requested-with": "XMLHttpRequest",
        "origin": "https://fameviso.com",
        "referer": "https://fameviso.com/free-instagram-views/"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(TEST_URL, proxy=f"http://{proxy}", timeout=8) as r:
                html = await r.text()
                csrf = re.search(r'name="csrf_token" value="(.*?)"', html).group(1)

            base_payload = (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{clean_url}\r\n"
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n"
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"extended_user_agent\"\r\n\r\n{ext_ua}\r\n"
            )

            data1 = base_payload + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n"
            async with session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                    data=data1, headers=headers, proxy=f"http://{proxy}", timeout=8) as r:
                res1 = await r.json()

            if res1.get("status") == "tasks":
                token = res1.get("request_token")
                for task in res1.get('tasks', []):
                    task_id = task['id']
                    task_data = (
                        f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                        f"--{boundary}\r\nContent-Disposition: form-data; name=\"task_id\"\r\n\r\n{task_id}\r\n"
                        f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n"
                        f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ntask_finish\r\n"
                        f"--{boundary}--\r\n"
                    )
                    await session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                       data=task_data, headers=headers, proxy=f"http://{proxy}", timeout=8)
                
                await asyncio.sleep(2)
                data2 = base_payload + (
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n"
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n"
                    f"--{boundary}--\r\n"
                )
                async with session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                        data=data2, headers=headers, proxy=f"http://{proxy}", timeout=8) as r:
                    final_res = await r.text()
                    return "success" in final_res.lower()
            
            elif res1.get("status") in ["success", "proceed"]:
                return True
                
        except: return False
    return False

# ================= 🤖 TELEGRAM HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **SMM MASTER V14 (ULTIMATE)**\nToken Updated Successfully!\nDrop your Instagram Reel link below!")

async def proxies_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    cur.execute("SELECT COUNT(*) FROM proxies")
    count = cur.fetchone()[0]
    await update.message.reply_text(f"📊 **ADMIN STATUS**\nActive Proxies in DB: `{count}`", parse_mode="Markdown")

async def handle_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "instagram.com" not in url: return
    
    status_msg = await update.message.reply_text("🛸 **Initializing Bypass Engine...**")
    
    success = False
    for attempt in range(1, 11):
        proxy = get_random_proxy()
        if not proxy: break
        await status_msg.edit_text(f"🛰️ Attempt {attempt}/10\nNode: `{proxy}`\nStatus: Bypassing Tasks...")
        
        if await run_attack(url, proxy):
            success = True
            break
        else: remove_dead_proxy(proxy)
    
    if success: await status_msg.edit_text("✅ **MISSION ACCOMPLISHED**\nViews are dispatched!")
    else: await status_msg.edit_text("❌ **FAILED**\nAll nodes rejected the request.")

# ================= ⚙️ MAIN EXECUTION =================
async def main():
    Thread(target=run_web, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("proxies", proxies_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_dispatch))

    proxy_task = asyncio.create_task(proxy_worker())

    async with app:
        await app.initialize(); await app.start()
        print("🚀 BOT IS LIVE WITH NEW TOKEN")
        await app.updater.start_polling()
        
        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: stop_event.set())
        
        await stop_event.wait()
        proxy_task.cancel(); await app.updater.stop(); await app.stop(); await app.shutdown()

if __name__ == "__main__":
    try: asyncio.run(main())
    except (KeyboardInterrupt, SystemExit): pass
