import asyncio, requests, re, random, threading, time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIG ---
TOKEN = "7963420197:AAGtGASUJo9viBUFa_fuhVtWAo53eRioplY"
proxy_pool = [] # Yahan valid proxies khud load hongi

class ProxyHunter:
    def __init__(self):
        self.sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt"
        ]

    def scrape_and_test(self):
        global proxy_pool
        while True:
            print("🔎 Hunter is searching for fresh proxies...")
            raw_ips = []
            for url in self.sources:
                try:
                    r = requests.get(url, timeout=10)
                    if r.status_code == 200:
                        raw_ips.extend(re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', r.text))
                except: continue
            
            # Filter unique and test top 50
            unique_ips = list(set(raw_ips))
            random.shuffle(unique_ips)
            
            valid = []
            for ip in unique_ips[:100]:
                try:
                    # Fameviso test (Real validation)
                    test_proxy = {"http": f"http://{ip}", "https": f"http://{ip}"}
                    with requests.get("https://fameviso.com/free-instagram-views/", proxies=test_proxy, timeout=3) as res:
                        if res.status_code == 200 and "csrf_token" in res.text:
                            valid.append(ip)
                            if len(valid) >= 15: break # 15 live proxies are enough
                except: continue
            
            proxy_pool = valid
            print(f"✅ Hunter Pool Updated: {len(proxy_pool)} High-Speed Proxies Ready.")
            time.sleep(300) # Re-scrape every 5 minutes

hunter = ProxyHunter()

async def attack_logic(url):
    if not proxy_pool: return False, "Proxies are being warmed up. Wait 1 min."
    
    proxy = random.choice(proxy_pool)
    session = requests.Session()
    session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    
    ua = f"Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.{random.randint(100,999)}"
    boundary = "----WebKitFormBoundary" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=16))
    
    try:
        # 1. Fetch CSRF
        land = session.get("https://fameviso.com/free-instagram-views/", headers={"User-Agent": ua}, timeout=10)
        csrf = re.search(r'name="csrf_token" value="(.*?)"', land.text).group(1)
        
        # 2. Initial Request
        payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                   f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                   f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{url}\r\n"
                   f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n"
                   f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n"
                   f"--{boundary}--\r\n")
        
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": ua}
        r1 = session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", data=payload, headers=headers, timeout=10)
        
        if r1.json().get("status") == "proceed":
            token = r1.json().get("request_token")
            await asyncio.sleep(2) # Anti-spam delay
            
            # 3. Final Verification
            payload2 = payload.replace("initial_request", "verify_request").replace(f"--{boundary}--", f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n--{boundary}--\r\n")
            r2 = session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", data=payload2, headers=headers, timeout=10)
            
            if "success" in r2.text.lower():
                return True, proxy
    except Exception as e:
        return False, str(e)
    return False, "Server Rejected"

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 **SMM Hunter V9 Active!**\nSend me an Instagram Reel link to start.")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "instagram.com" not in url: return
    
    msg = await update.message.reply_text("🔎 **Searching for a clean proxy node...**")
    
    success, detail = await attack_logic(url)
    if success:
        await msg.edit_text(f"✅ **Views Dispatched!**\nNode: `{detail}`", parse_mode="Markdown")
    else:
        await msg.edit_text(f"❌ **Failed:** {detail}\nTrying again with another node...")

if __name__ == '__main__':
    # Start Hunter in background
    threading.Thread(target=hunter.scrape_and_test, daemon=True).start()
    
    # Start Bot
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    
    print("🚀 SMM BEAST IS RUNNING...")
    app.run_polling()
            
