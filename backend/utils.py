import os
import urllib.request
import urllib.parse
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def kirim_pesan_telegram(pesan: str, chat_id: str = None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not chat_id:
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": chat_id, "text": pesan})
            return True
        except Exception as e:
            print("Gagal mengirim Telegram:", e)
            return False
    return False