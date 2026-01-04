import asyncio, requests, re, random, threading, time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIG ---
TOKEN = "7963420197:AAEBVLY-Ym_P387FEkkp4kA2bVcEPzUg72M"
proxy_pool = [] 

class ProxyHunter:
    def __init__(self):
        self.sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"
        ]

    def scrape_and_test(self):
        global proxy_pool
        while True:
            raw_ips = []
            for url in self.sources:
                try:
                    r = requests.get(url, timeout=5)
                    raw_ips.extend(re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', r.text))
                except: continue
            
            unique_ips = list(set(raw_ips))
            random.shuffle(unique_ips)
            
            valid = []
            # Sirf fast proxies filter karein
            for ip in unique_ips[:200]: 
                try:
                    proxies = {"http": f"http://{ip}", "https": f"http://{ip}"}
                    # 1.5 second timeout taaki sirf super-fast proxies pool mein aayein
                    with requests.get("https://fameviso.com/free-instagram-views/", proxies=proxies, timeout=1.5) as res:
                        if res.status_code == 200:
                            valid.append(ip)
                            if len(valid) >= 30: break 
                except: continue
            
            if valid: 
                proxy_pool = valid
                print(f"🔥 Pool Updated: {len(proxy_pool)} Ultra-Fast Proxies Ready.")
            time.sleep(120) # Pool update every 2 mins

hunter = ProxyHunter()

async def single_attack(url, proxy):
    ua = f"Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.{random.randint(100,999)}"
    boundary = "----WebKitFormBoundary" + "".join(random.choices("abcdef0123456789", k=16))
    session = requests.Session()
    # Kam timeout taaki "ProxyError" hone pe bot fauran dusri try kare
    session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    
    try:
        land = session.get("https://fameviso.com/free-instagram-views/", headers={"User-Agent": ua}, timeout=3)
        csrf = re.search(r'name="csrf_token" value="(.*?)"', land.text).group(1)
        
        payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n{csrf}\r\n"
                   f"--{boundary}\r\nContent-Disposition: form-data; name=\"service\"\r\n\r\n8061\r\n"
                   f"--{boundary}\r\nContent-Disposition: form-data; name=\"photoLink\"\r\n\r\n{url}\r\n"
                   f"--{boundary}\r\nContent-Disposition: form-data; name=\"viewsQuantity\"\r\n\r\n250\r\n"
                   f"--{boundary}\r\nContent-Disposition: form-data; name=\"action_type\"\r\n\r\ninitial_request\r\n--{boundary}--\r\n")
        
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": ua}
        r1 = session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", data=payload, headers=headers, timeout=4)
        
        if r1.json().get("status") == "proceed":
            token = r1.json().get("request_token")
            await asyncio.sleep(2)
            
            payload2 = payload.replace("initial_request", "verify_request").replace(f"--{boundary}--", f"--{boundary}\r\nContent-Disposition: form-data; name=\"request_token\"\r\n\r\n{token}\r\n--{boundary}--\r\n")
            r2 = session.post("https://fameviso.com/themes/vision/part/free-instagram-views/submitForm.php", data=payload2, headers=headers, timeout=4)
            return "success" in r2.text.lower()
    except: return False
    return False

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "instagram.com" not in url: return

    if not proxy_pool:
        return await update.message.reply_text("⏳ System Warming Up... Wait 20 seconds.")

    msg = await update.message.reply_text("🚀 **Initiating Multi-Node Attack...**")
    
    success = False
    # Max 10 attempts (different proxies) taaki guarantee success ho
    for attempt in range(1, 11):
        target_proxy = random.choice(proxy_pool)
        await msg.edit_text(f"🛰️ **Attempt {attempt}/10**\nNode: `{target_proxy}`\nStatus: Testing Bypass...")
        
        if await single_attack(url, target_proxy):
            success = True
            break
        # Agar fail ho toh list se hata do taaki repeat na ho
        if target_proxy in proxy_pool: proxy_pool.remove(target_proxy)

    if success:
        await msg.edit_text(f"✅ **Mission Accomplished!**\nViews are dispatched via premium node.")
    else:
        await msg.edit_text("❌ **All nodes timed out.** Server busy or link invalid.")

# --- EXECUTION ---
if __name__ == '__main__':
    threading.Thread(target=hunter.scrape_and_test, daemon=True).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Drop the Instagram Link!")))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    print("SMM BEAST V10 IS READY")
    bot.run_polling()
