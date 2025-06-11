import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import json
import os

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Кэш для хранения данных
CACHE_FILE = "tiktok_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def get_tiktok_user_data(username):
    cache = load_cache()
    if username in cache:
        return cache[username]
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36")
    
    # РАБОЧИЕ ПРОКСИ (обновить при блокировке)
    PROXIES = [
        "http://45.142.28.21:8000",
        "http://193.149.225.128:80",
        "http://88.198.50.103:8080"
    ]
    
    user_data = {}
    driver = None
    
    for proxy in PROXIES:
        try:
            chrome_options.add_argument(f"--proxy-server={proxy}")
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            driver.get(f"https://www.tiktok.com/@{username}")
            time.sleep(4)  # Критично для загрузки контента
            
            # Проверка на 404
            if "Couldn't find this account" in driver.page_source:
                user_data = {"error": "Аккаунт не существует"}
                break
            
            # Парсинг данных
            user_data["full_name"] = driver.find_element(By.CSS_SELECTOR, 'h1[data-e2e="user-title"]').text
            user_data["bio"] = driver.find_element(By.CSS_SELECTOR, 'h2[data-e2e="user-bio"]').text
            user_data["following"] = driver.find_element(By.CSS_SELECTOR, 'strong[data-e2e="following-count"]').text
            user_data["followers"] = driver.find_element(By.CSS_SELECTOR, 'strong[data-e2e="followers-count"]').text
            user_data["likes"] = driver.find_element(By.CSS_SELECTOR, 'strong[data-e2e="likes-count"]').text
            user_data["private"] = "Да" if driver.find_elements(By.CSS_SELECTOR, 'span[data-e2e="private-account"]') else "Нет"
            
            # Проверка верификации
            user_data["verified"] = "Да" if driver.find_elements(By.CSS_SELECTOR, 'svg[aria-label="Verified account"]') else "Нет"
            
            # Сохранение в кэш
            cache[username] = user_data
            save_cache(cache)
            break
            
        except (NoSuchElementException, TimeoutException):
            logger.warning(f"Прокси {proxy} упал, пробую следующий...")
            continue
        except Exception as e:
            user_data = {"error": f"Ошибка: {str(e)}"}
        finally:
            if driver:
                driver.quit()
    
    return user_data

def tiktok_command(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Используйте: /tiktok <username>")
        return
    
    username = context.args[0].replace("@", "")
    update.message.reply_text(f"🕒 Ищу @{username}...")
    
    data = get_tiktok_user_data(username)
    
    if "error" in data:
        update.message.reply_text(f"❌ Ошибка: {data['error']}")
        return
    
    response = (
        f"👤 Имя: {data['full_name']}\n"
        f"📝 Bio: {data['bio']}\n"
        f"🔒 Приватный: {data['private']}\n"
        f"✅ Верифицирован: {data['verified']}\n"
        f"👥 Подписки: {data['following']}\n"
        f"❤️ Подписчики: {data['followers']}\n"
        f"🔥 Лайки: {data['likes']}"
    )
    update.message.reply_text(response)

def main():
    TOKEN = "7946251650:AAG0DvWmRYV5VBeZdWlxoaytN90PwVDYk34"  # Заменить на токен от @BotFather
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("tiktok", tiktok_command, pass_args=True))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
