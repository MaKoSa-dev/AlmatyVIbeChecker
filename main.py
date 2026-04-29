import os
import requests
import json
import os
from bs4 import BeautifulSoup
from openai import OpenAI
import telebot
from telebot.types import Message
import schedule
import time
import threading
from datetime import datetime
TWOGIS_KEY     = os.getenv("TWOGIS_KEY")
WEATHER_KEY    = os.getenv("WEATHER_KEY")
NEWSAPI_KEY    = os.getenv("NEWSAPI_KEY", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
DB_FILE = "vibe_db.json"

llm = OpenAI(api_key=OPENROUTER_KEY, base_url="https://openrouter.ai/api/v1")

def save_to_db(date: str, data: dict):
    db = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
    db[date] = data
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"✅ Данные сохранены в {DB_FILE}")

def get_from_db(date: str) -> dict:
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    return db.get(date, {})

#Погода
def run_weather_agent() -> str:
    r = requests.get("https://api.openweathermap.org/data/2.5/weather", params={
        "q": "Almaty,KZ", "appid": WEATHER_KEY, "units": "metric", "lang": "ru"
    })
    if r.status_code != 200:
        return "Погода недоступна"
    d = r.json()
    return (
        f"Погода: {d['weather'][0]['description']}, "
        f"{d['main']['temp']}°C (ощущается {d['main']['feels_like']}°C), "
        f"влажность {d['main']['humidity']}%, ветер {d['wind']['speed']} м/с"
    )

#2gis
def run_2gis_agent() -> str:
    parts = []
    for cat in ["кафе", "парк", "ресторан"]:
        r = requests.get("https://catalog.api.2gis.com/3.0/items", params={
            "q": cat, "location": "76.9286,43.2567",
            "radius": 10000, "page_size": 3,
            "fields": "items.reviews,items.point", "key": TWOGIS_KEY
        })
        if r.status_code != 200:
            continue
        for p in r.json().get("result", {}).get("items", []):
            rating = p.get("reviews", {}).get("rating", "")
            name = p.get("name", "")
            addr = p.get("address_name", "")
            parts.append(f"{name} ({cat}){f', рейтинг {rating}' if rating else ''} — {addr}")
    return "Популярные места: " + "; ".join(parts) if parts else "Данные 2GIS недоступны"

#Новости
def run_news_agent() -> str:
    parts = []
    try:
        r = requests.get("https://tengrinews.kz/almaty/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        for item in soup.find_all("a", class_="content-main-item-title", limit=3):
            title = item.get_text(strip=True)
            if title:
                parts.append(title)
    except:
        pass

    if NEWSAPI_KEY:
        try:
            r = requests.get("https://newsapi.org/v2/everything", params={
                "q": "Алматы", "language": "ru",
                "sortBy": "publishedAt", "pageSize": 3, "apiKey": NEWSAPI_KEY
            })
            for a in r.json().get("articles", []):
                if a.get("title"):
                    parts.append(a["title"])
        except:
            pass

    return "Новости: " + "; ".join(parts[:5]) if parts else "Новости недоступны"

#События
def run_events_agent() -> str:
    parts = []
    try:
        r = requests.get("https://ticketon.kz/almaty", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        titles = soup.find_all("a", class_=lambda c: c and "title" in c.lower(), limit=5)
        if not titles:
            titles = soup.find_all("h2", limit=5)
        for t in titles:
            title = t.get_text(strip=True)[:60]
            if title and len(title) > 5:
                parts.append(title)
    except:
        pass
    return "События: " + "; ".join(parts) if parts else "События недоступны"

#Репорт
def generate_vibe_report() -> str:
    today = datetime.now().strftime("%d.%m.%Y")
    print(f"Собираю данные за {today}...")

    cached = get_from_db(today)
    if cached:
        print("Использую кэшированные данные из базы")
        data = cached
    else:
        print("Запускаю агентов...")
        data = {
            "weather": run_weather_agent(),
            "places":  run_2gis_agent(),
            "news":    run_news_agent(),
            "events":  run_events_agent(),
        }
        save_to_db(today, data)

    context = "\n".join([
        f"🌤 {data['weather']}",
        f"📍 {data['places']}",
        f"📰 {data['news']}",
        f"🎭 {data['events']}",
    ])

    prompt = f"""Ты — городской аналитик Алматы. На основе данных ниже напиши короткий живой вайб-репорт города на {today}.

Данные:
{context}

Требования:
- Длина: 4-6 предложений
- Тон: живой, как у городского блогера
- Упомяни погоду, атмосферу, топ-место, пробки и событие
- В конце поставь эмодзи-оценку (например: 🌤 7/10)
- Пиши на русском языке"""

    response = llm.chat.completions.create(
        model="meta-llama/llama-4-scout:free",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

#tg bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)
subscribers = set()

@bot.message_handler(commands=["start"])
def cmd_start(message: Message):
    subscribers.add(message.chat.id)
    bot.reply_to(message,
        "👋 Привет! Я *Almaty Vibe Bot*\n\n"
        "Каждый день в 9:00 я буду присылать вайб-репорт города 🌆\n\n"
        "Команды:\n"
        "/vibe — репорт прямо сейчас\n"
        "/stop — отписаться",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=["vibe"])
def cmd_vibe(message: Message):
    bot.reply_to(message, "⏳ Собираю данные по городу...")
    try:
        report = generate_vibe_report()
        bot.reply_to(message, f"🏙 *Вайб Алматы сегодня:*\n\n{report}", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=["stop"])
def cmd_stop(message: Message):
    subscribers.discard(message.chat.id)
    bot.reply_to(message, "Отписался. Напиши /start чтобы подписаться снова.")
@bot.message_handler(commands=["traffic"])
 
@bot.message_handler(commands=["aqi"])
def cmd_aqi(message: Message):
    bot.reply_to(message, "⏳ Проверяю воздух...")
    try:
        report = run_aqi_agent()
        bot.reply_to(message, f"🌫 {report}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
 
 
@bot.message_handler(commands=["exchange"])
def cmd_exchange(message: Message):
    bot.reply_to(message, "⏳ Проверяю курсы...")
    try:
        report = run_exchange_agent()
        bot.reply_to(message, f"💰 *Курс валют к тенге:*\n\n{report}", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
 
 
@bot.message_handler(commands=["recommend"])
def cmd_recommend(message: Message):
    bot.reply_to(message, "Напиши своё настроение или запрос, например:\n\n"
        "• хочу погулять\n"
        "• ищу кафе с wi-fi\n"
        "• куда сходить с детьми\n"
        "• хочу активного отдыха")
 
 
@bot.message_handler(func=lambda m: not m.text.startswith("/"))
def handle_recommend(message: Message):
    bot.reply_to(message, "⏳ Думаю над рекомендацией...")
    try:
        # Берём последние данные из базы
        from datetime import datetime
        today = datetime.now().strftime("%d.%m.%Y")
        data = get_from_db(today)
 
        context = ""
        if data:
            context = f"""
Текущие данные по Алматы:
- {data.get('weather', '')}
- {data.get('events', '')}
- {data.get('places', '')}
"""
 
        prompt = f"""Ты — личный гид по Алматы. Пользователь написал: "{message.text}"
 
{context}
 
Дай конкретный и живой совет что делать в Алматы прямо сейчас. 
Упомяни реальные места, районы или события если знаешь.
Длина: 3-4 предложения. Пиши на русском."""
 
        response = llm.chat.completions.create(
            model="deepseek/deepseek-chat-v3-5:free",
            messages=[{"role": "user", "content": prompt}]
        )
        bot.reply_to(message, f"🗺 {response.choices[0].message.content}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
def cmd_traffic(message: Message):
    bot.reply_to(message, "⏳ Проверяю дороги...")
    try:
        report = run_traffic_agent()
        bot.reply_to(message, f"🚗 {report}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
def send_daily_report():
    if not subscribers:
        return
    print(f"Отправляю репорт {len(subscribers)} подписчикам...")
    try:
        report = generate_vibe_report()
        for chat_id in subscribers:
            bot.send_message(chat_id,
                f"🌅 *Доброе утро! Вайб Алматы на сегодня:*\n\n{report}",
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Ошибка рассылки: {e}")

#/traffic
def run_traffic_agent() -> str:
    url = "https://catalog.api.2gis.com/3.0/traffic"
    params = {
        "location": "76.9286,43.2567",
        "key": TWOGIS_KEY
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return "Данные о пробках недоступны"
    
    data = r.json()
    level = data.get("traffic_level", {})
    score = level.get("score", 0)
    
    if score <= 3:
        status = "🟢 Свободно"
    elif score <= 6:
        status = "🟡 Умеренные пробки"
    else:
        status = "🔴 Серьёзные пробки"
    
    return f"Пробки в Алматы: {status} (уровень {score}/10)"

#Воздух
def run_aqi_agent() -> str:
    r = requests.get("https://api.openweathermap.org/data/2.5/air_pollution", params={
        "lat": "43.2567",
        "lon": "76.9286",
        "appid": WEATHER_KEY
    })
    if r.status_code != 200:
        return "Данные о воздухе недоступны"
 
    aqi = r.json()["list"][0]["main"]["aqi"]
    levels = {
        1: "🟢 Отличный — дышите полной грудью!",
        2: "🟡 Хороший — всё в порядке",
        3: "🟠 Умеренный — чувствительным людям осторожно",
        4: "🔴 Плохой — лучше меньше времени на улице",
        5: "🟣 Очень плохой — оставайтесь дома"
    }
    return f"Качество воздуха в Алматы: {levels.get(aqi, 'Нет данных')} (индекс {aqi}/5)"
 
 
# Валюта
def run_exchange_agent() -> str:
    r = requests.get("https://api.exchangerate-api.com/v4/latest/KZT")
    if r.status_code != 200:
        return "Курс валют недоступен"
 
    rates = r.json().get("rates", {})
    usd = round(1 / rates.get("USD", 0), 2) if rates.get("USD") else "—"
    rub = round(1 / rates.get("RUB", 0), 2) if rates.get("RUB") else "—"
    eur = round(1 / rates.get("EUR", 0), 2) if rates.get("EUR") else "—"
 
    return (
        f"💵 1 USD = {usd} тенге\n"
        f"💶 1 EUR = {eur} тенге\n"
        f"🇷🇺 1 RUB = {rub} тенге"
    )
 
@bot.message_handler(commands=["traffic"])
def cmd_traffic(message: Message):
    bot.reply_to(message, "⏳ Проверяю дороги...")
    try:
        report = run_traffic_agent()
        bot.reply_to(message, f"🚗 {report}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

def run_scheduler():
    schedule.every().day.at("09:00").do(send_daily_report)
    while True:
        schedule.run_pending()
        time.sleep(60)

#Старт
if __name__ == "__main__":
    print("🚀 Almaty Vibe Bot запущен!")
    print("Напиши боту /start в Telegram\n")
    threading.Thread(target=run_scheduler, daemon=True).start()
    bot.infinity_polling()
