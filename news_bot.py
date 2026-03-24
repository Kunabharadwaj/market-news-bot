import feedparser
import requests
import os
from groq import Groq
from datetime import datetime

# --- Config from env ---
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

# --- RSS Feeds ---
FEEDS = {
    # 🇮🇳 Indian Market
    "🇮🇳 Economic Times Markets":   "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "🇮🇳 Economic Times Economy":   "https://economictimes.indiatimes.com/economy/rssfeeds/1373380680.cms",
    "🇮🇳 MoneyControl":             "https://www.moneycontrol.com/rss/latestnews.xml",
    "🇮🇳 LiveMint Markets":         "https://www.livemint.com/rss/markets",
    "🇮🇳 BSE India News":           "https://www.bseindia.com/xml-data/corpfiling/AttachLive/rss.xml",

    # 🌍 Global Markets
    "🌍 Reuters Business":          "https://feeds.reuters.com/reuters/businessNews",
    "🌍 Yahoo Finance":             "https://finance.yahoo.com/news/rssindex",
    "🌍 Investing.com":             "https://www.investing.com/rss/news.rss",
    "🌍 MarketWatch":               "https://feeds.marketwatch.com/marketwatch/topstories/",

    # 🛢️ Commodities / Macro
    "🛢️ Oilprice.com":             "https://oilprice.com/rss/main",
}

def fetch_headlines(max_per_feed=5):
    stories = []
    for source, url in FEEDS.items():
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries[:max_per_feed]:
                if hasattr(entry, "title") and entry.title.strip():
                    stories.append(f"[{source}] {entry.title.strip()}")
                    count += 1
            print(f"  ✅ {source}: {count} headlines")
        except Exception as e:
            print(f"  ⚠️  Failed to fetch {source}: {e}")
    return stories

def summarise_with_groq(headlines: list[str]) -> str:
    client = Groq(api_key=GROQ_API_KEY)
    bullet_list = "\n".join(f"- {h}" for h in headlines)

    prompt = f"""You are a senior financial analyst covering Indian and global markets.

Analyse the following headlines and produce a structured briefing:

📊 **Market Themes** (5-6 bullets)
- Key trends across Indian (NSE/BSE) and global markets
- Note any overnight US/Asia moves that may impact Indian open

🏭 **Sector Spotlight** (3-4 bullets)
- Call out sectors under pressure or outperforming
- Include: IT, Banking, FMCG, Auto, Energy, Metals, Pharma if relevant

🌐 **Macro & Policy Watch** (2-3 bullets)
- RBI, Fed, inflation, currency (INR/USD), oil prices
- Any regulatory or government policy signals

⚠️ **Risk Flags** (1-2 bullets)
- Geopolitical, earnings surprises, or sentiment shifts to watch

💡 **Investor Takeaway** (2 lines max)
- Concise actionable insight for a retail investor in Indian equities

Rules:
- Use emoji bullets throughout
- Be direct, no filler
- Flag BREAKING or HIGH IMPACT items with 🔴
- Tone: professional but readable

Headlines:
{bullet_list}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
    )
    return response.choices[0].message.content

def send_telegram(message: str):
    date_str = datetime.now().strftime("%d %b %Y, %I:%M %p IST")
    full_msg = f"📰 *Market News Digest — {date_str}*\n\n{message}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": full_msg,
        "parse_mode": "Markdown"
    })
    print(f"Telegram response: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("Fetching headlines...")
    headlines = fetch_headlines()
    print(f"\nGot {len(headlines)} headlines total. Summarising...")
    summary = summarise_with_groq(headlines)
    print("Sending to Telegram...")
    send_telegram(summary)
    print("Done ✅")
