import asyncio
import aiohttp
import sqlite3
import time
import re
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= CONFIG =================
BOT_TOKEN = "7963420197:AAFCX4ck230hEFheWleMgdLI3tuSLzYgQao"
ADMIN_ID = 7840042951

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000"
]

TEST_URL = "https://fameviso.com/free-instagram-views/" # Directly testing on target
TIMEOUT = 5
BATCH_SIZE = 50          
SLEEP_AFTER_BATCH = 30  
SLEEP_AFTER_CYCLE = 10 * 60 
# ========================================

# ================= DATABASE =================
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
# ==========================================

# ================= PROXY ENGINE =================
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
    async with aiohttp.ClientSession() as session:
        while True:
            texts = await asyncio.gather(*[fetch_source(session, u) for u in PROXY_SOURCES])
            all_proxies = []
            for t in texts:
                for line in re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', t):
                    all_proxies.append(line.strip())

            for i in range(0, len(all_proxies), BATCH_SIZE):
                batch = all_proxies[i:i + BATCH_SIZE]
                for proxy in batch:
                    if await test_proxy(session, proxy):
                        cur.execute("INSERT OR REPLACE INTO proxies VALUES (?, ?)", (proxy, int(time.time())))
                        db.commit()
                await asyncio.sleep(SLEEP_AFTER_BATCH)
            await asyncio.sleep(SLEEP_AFTER_CYCLE)

# ================= ATTACK ENGINE =================
async def run_attack(url, proxy):
    clean_url = url.split('?')[0]
    if not clean_url.endswith('/'): clean_url += '/'
    
    ua = f"Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.{random.randint(100,999)}"
    boundary = "----WebKitFormBoundary" + "".join(random.choices("abcdef0123456789", k=16))
    
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": ua}
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Get Token
            async with session.get(TEST_URL, proxy=f"http://{proxy}", timeout=6) as r:
                html = await r.text()
                csrf = re.search(r'name="csrf_token" value="(.*?)"', html).group(1)

            payload_base = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{clean_url}\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n"
                            f"--{boundary}\r\nContent-Disposition: form-data; name=\"extended_user_agent\"\r\n\r\nInternal_Bot_V11\r\n")

            # Step 2: Initial Request
            p1 = payload_base + f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n"
            async with session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                    data=p1, headers=headers, proxy=f"http://{proxy}", timeout=6) as r:
                res1 = await r.json()
                
            if res1.get("status") == "proceed":
                token = res1.get("request_token")
                await asyncio.sleep(2) # Security delay
                
                # Step 3: Verify
                p2 = payload_base + f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n" + \
                     f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\nverify_request\r\n--{boundary}--\r\n"
                async with session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", 
                                        data=p2, headers=headers, proxy=f"http://{proxy}", timeout=6) as r:
                    final_text = await r.text()
                    return "success" in final_text.lower()
        except:
            return False
    return False

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **SMM MASTER V11 ONLINE**\n\nSend me an Instagram Reel link to start dispatching views.")

async def proxies_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    cur.execute("SELECT COUNT(*) FROM proxies")
    count = cur.fetchone()[0]
    await update.message.reply_text(f"📊 **System Status**\nLive Proxies in DB: `{count}`\nBatch Size: `{BATCH_SIZE}`", parse_mode="Markdown")

async def handle_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "instagram.com" not in url: return

    status_msg = await update.message.reply_text("🔎 **Searching for a working proxy node...**")
    
    success = False
    for attempt in range(1, 8): # 7 Retries
        proxy = get_random_proxy()
        if not proxy:
            await status_msg.edit_text("❌ No proxies available in database. Warming up...")
            return

        await status_msg.edit_text(f"🛰️ **Attempt {attempt}/7**\nNode: `{proxy}`\nStatus: Bypassing...")
        
        if await run_attack(url, proxy):
            success = True
            break
        else:
            remove_dead_proxy(proxy) # Clean DB on failure

    if success:
        await status_msg.edit_text("✅ **MISSION ACCOMPLISHED**\n250+ Views have been dispatched successfully!")
    else:
        await status_msg.edit_text("❌ **FAILED**\nAll attempts failed. Server might be rate-limiting. Try later.")

# ================= MAIN =================
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("proxies", proxies_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_dispatch))

    asyncio.create_task(proxy_worker())
    print("🚀 BOT STARTED SUCCESSFULLY")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
