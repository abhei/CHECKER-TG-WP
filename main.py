import re
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === TELEGRAM CHECKER ===
from telethon import TelegramClient, errors

# === WHATSAPP CHECKER ===
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ========================================================
# 🔐 YOUR CREDENTIALS (EMBEDDED)
# ========================================================
BOT_TOKEN = "8853669853:AAFAOmHJy0TuxA5sBvME5m_hs8OTYld_zw4"
API_ID = 37791113
API_HASH = "3e6197a0977b7782497a1dc90ed42ac6"

# Optional: Agar sirf tu hi bot use karna chahta hai toh uncomment karo
# MY_CHAT_ID = 7758954478

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========================================================
# TELEGRAM CHECK
# ========================================================
async def check_telegram(phone: str):
    client = TelegramClient('session', API_ID, API_HASH)
    try:
        await client.connect()
        await client.send_code_request(phone)
        await client.disconnect()
        return True, "✅ Telegram account EXISTS"
    except errors.PhoneNumberInvalidError:
        await client.disconnect()
        return False, "❌ Telegram account DOES NOT EXIST"
    except errors.FloodWaitError as e:
        await client.disconnect()
        return False, f"⏳ Rate limited by Telegram, wait {e.seconds}s"
    except Exception as e:
        await client.disconnect()
        return False, f"⚠️ Telegram error: {str(e)}"

# ========================================================
# WHATSAPP CHECK
# ========================================================
def check_whatsapp(phone: str):
    clean = re.sub(r'[^0-9]', '', phone)
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(f"https://wa.me/{clean}")
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page = driver.page_source.lower()
        driver.quit()

        if "this phone number is not on whatsapp" in page:
            return False, "❌ WhatsApp account DOES NOT EXIST"
        elif "continue to chat" in page or "open in whatsapp" in page:
            return True, "✅ WhatsApp account EXISTS"
        elif "download whatsapp" in page:
            return False, "❌ WhatsApp account NOT REGISTERED"
        else:
            return False, "❓ WhatsApp status UNKNOWN"
    except Exception as e:
        return False, f"⚠️ WhatsApp error: {str(e)}"

# ========================================================
# BOT COMMANDS
# ========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 CURY Account Checker Online!\n\n"
        "Send /check +911234567890\n"
        "to check if a number has Telegram & WhatsApp accounts."
    )

async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /check +911234567890")
        return

    phone = context.args[0]
    phone = re.sub(r'[\s\-()]', '', phone)
    if not phone.startswith('+'):
        phone = '+' + phone

    await update.message.reply_text(f"🔍 Checking {phone} ... (may take 5-15 sec)")

    # Run checks
    tele_ok, tele_msg = await check_telegram(phone)
    wa_ok, wa_msg = await asyncio.to_thread(check_whatsapp, phone)

    reply = (
        f"📱 Telegram: {tele_msg}\n"
        f"📱 WhatsApp: {wa_msg}\n\n"
        f"📊 Summary:\n"
        f"Telegram: {'✅ YES' if tele_ok else '❌ NO'}\n"
        f"WhatsApp: {'✅ YES' if wa_ok else '❌ NO'}"
    )
    await update.message.reply_text(reply)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Show welcome\n"
        "/check +91XXXXXXXXXX - Check number\n"
        "/help - Show this"
    )

# ========================================================
# MAIN
# ========================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    
    logger.info("🤖 CURY Bot is running...")
    print("✅ Bot is LIVE! Send /check +911234567890 in Telegram.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()