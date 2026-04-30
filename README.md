# AlmatyVIbeChecker

# 🏙 Almaty Vibe Analyzer

> AI-powered Telegram bot that analyzes the daily mood of Almaty city using multi-agent architecture and RAG.

## 📌 About

**Almaty Vibe Analyzer** is a final project for the course **CSS 118 — AI and Prompt Engineering** at SDU University.

The system collects real-time data from multiple sources, stores it using a RAG pipeline, and uses an LLM to generate a daily "vibe report" of Almaty — what's happening in the city, how the weather is, what events are on, and where to go today.

---

## 🤖 How It Works

```
4 Agents → RAG (JSON DB) → LLM (LLaMA 3.3 70B) → Telegram Bot
```

1. **Agents** collect data from real sources
2. **RAG** saves data to `vibe_db.json` and retrieves it for the LLM
3. **LLM** generates a live city report based on real data
4. **Telegram Bot** sends the report to subscribers daily at 9:00 AM

---

## 🧠 Agents

| Agent | Source | Data |
|-------|--------|------|
| Weather Agent | OpenWeatherMap API | Temperature, humidity, wind |
| Places Agent | 2GIS API | Popular cafes, parks, restaurants |
| News Agent | Tengrinews.kz + NewsAPI | Local news headlines |
| Events Agent | Ticketon.kz | Concerts, shows, events |
| Traffic Agent | 2GIS API | Road congestion level |
| AQI Agent | OpenWeatherMap API | Air quality index |
| Exchange Agent | ExchangeRate API | USD, EUR, RUB to KZT |

---

## 📱 Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Subscribe to daily reports |
| `/vibe` | Get today's city vibe report |
| `/traffic` | Check road congestion |
| `/aqi` | Check air quality |
| `/exchange` | Check currency rates |
| `/recommend` | Get personalized recommendation |
| `/stop` | Unsubscribe |

After `/recommend` — just type your request freely, e.g. `хочу погулять` or `куда сходить с детьми`

---

## 🛠 Tech Stack

- **Language:** Python 3.11
- **LLM:** LLaMA 3.3 70B via Groq API
- **RAG:** Custom JSON-based retrieval pipeline
- **Parsing:** BeautifulSoup4 + lxml
- **Bot:** pyTelegramBotAPI
- **Hosting:** Railway
- **Scheduler:** schedule + threading

---

## 📚 Course Topics Covered

| Week | Topic | Used In |
|------|-------|---------|
| Week 1 | Python basics | Entire codebase |
| Week 5 | NLP | News and review text processing |
| Week 6 | LLM & Transformers | LLaMA via Groq |
| Week 9-11 | Prompt Engineering | Structured prompts for report generation |
| Week 12 | RAG | JSON-based retrieval pipeline |
| Week 13 | LLM Automation | Daily scheduled reports |
| Week 14 | AI Agents | Multi-agent architecture |

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/almaty-vibe-bot
cd almaty-vibe-bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set environment variables
```bash
TWOGIS_KEY=your_2gis_key
WEATHER_KEY=your_openweathermap_key
GROQ_KEY=your_groq_key
TELEGRAM_TOKEN=your_telegram_bot_token
NEWSAPI_KEY=your_newsapi_key  # optional
```

### 4. Run
```bash
python main.py
```

---

## 🚀 Deploy on Railway

1. Push code to GitHub
2. Connect repo to [Railway](https://railway.app)
3. Add environment variables in Railway → Variables
4. Railway auto-deploys and runs 24/7

---

## 📁 Project Structure

```
almaty-vibe-bot/
├── main.py          # Main file — all agents, RAG, bot
├── requirements.txt # Dependencies
├── vibe_db.json     # RAG database (auto-generated)
└── README.md        # This file
```

---

## 🔑 APIs Used

- [2GIS API](https://dev.2gis.ru) — places and traffic
- [OpenWeatherMap API](https://openweathermap.org/api) — weather and air quality
- [NewsAPI](https://newsapi.org) — news articles
- [Groq API](https://console.groq.com) — LLM inference
- [ExchangeRate API](https://exchangerate-api.com) — currency rates
- Tengrinews.kz — web scraping
- Ticketon.kz — web scraping

---

## 👤 Author

SDU University — CSS 118 AI and Prompt Engineering — Spring 2026
