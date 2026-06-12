import requests
import os

def kirim_pesan_telegram(pesan: str, chat_id: str = None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Gunakan default dari Railway jika user belum mengatur ID
    if not chat_id:
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            # Kirim pesan ke Telegram
            response = requests.post(url, json={"chat_id": str(chat_id).strip(), "text": pesan})
            
            # Jika Telegram menolak (kode bukan 200 OK), cetak alasan aslinya!
            if response.status_code != 200:
                print(f"\n--- ❌ TELEGRAM ERROR ---")
                print(f"Chat ID: {chat_id}")
                print(f"Alasan: {response.text}")
                print(f"-------------------------\n")
                
            return response.status_code == 200
        except Exception as e:
            print(f"Gagal koneksi ke Telegram: {e}")
            return False
    else:
        print("TELEGRAM ERROR: Token atau Chat ID kosong!")
        
    return False