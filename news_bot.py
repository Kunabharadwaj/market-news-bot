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
    "🇮🇳 Economic Times Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "🇮🇳 MoneyControl":          "https://www.moneycontrol.com/rss/latestnews.xml",
    "🌍 Reuters Business":        "https://feeds.reuters.com/reuters/businessNews",
    "🌍 Yahoo Finance":           "https://finance.yahoo.com/news/rssindex",
}

def fetch_headlines(max_per_feed=5):
    stories = []
    for source, url in FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_per_feed]:
            stories.append(f"[{source}] {entry.title}")
    return stories

def summarise_with_groq(headlines: list[str]) -> str:
    client = Groq(api_key=GROQ_API_KEY)
    bullet_list = "\n".join(f"- {h}" for h in headlines)
    prompt = f"""You are a financial analyst assistant.
Below are today's top business/market news headlines from Indian and global sources.
Summarise the key themes in 8-10 bullet points. Flag anything relevant to:
- Indian stock market (NSE/BSE)
- Global market sentiment
- Macro/economic signals
- Sectors: Banking, IT, Energy, Auto

Headlines:
{bullet_list}

Format: Use emoji bullet points. End with a 2-line "💡 Investor Takeaway" section."""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
    )
    return response.choices[0].message.content

def send_telegram(message: str):
    date_str = datetime.now().strftime("%d %b %Y, %I:%M %p IST")
    full_msg = f"📰 *Market News Digest — {date_str}*\n\n{message}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": full_msg,
        "parse_mode": "Markdown"
    })

if __name__ == "__main__":
    print("Fetching headlines...")
    headlines = fetch_headlines()
    print(f"Got {len(headlines)} headlines. Summarising...")
    summary = summarise_with_groq(headlines)
    print("Sending to Telegram...")
    send_telegram(summary)
    print("Done ✅")
