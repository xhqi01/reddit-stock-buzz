import os
import re
import smtplib
import threading
from datetime import datetime
from collections import Counter
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import praw
import yfinance as yf
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder=".")

# ── KNOWN TICKERS ─────────────────────────────────────────────────────────────
# Common tickers mentioned on WSB/Reddit — expand as needed
KNOWN_TICKERS = {
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AMD",
    "NFLX", "BABA", "UBER", "LYFT", "SNAP", "TWTR", "PLTR", "RBLX", "RIVN",
    "GME", "AMC", "BB", "NOK", "BBBY", "SNDL", "CLOV", "WISH", "SPCE", "HOOD",
    "COIN", "SOFI", "LCID", "NIO", "XPEV", "LI", "BIDU", "JD", "PDD",
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "ARKK", "SQQQ", "TQQQ",
    "INTC", "QCOM", "MU", "AVGO", "TSM", "ASML", "SMCI", "ARM",
    "JPM", "BAC", "GS", "MS", "WFC", "C", "V", "MA", "PYPL",
    "SHOP", "SQ", "AFRM", "UPST", "OPEN", "Z", "ABNB", "DASH",
    "DIS", "NFLX", "WMT", "TGT", "COST", "AMZN", "ETSY",
    "F", "GM", "FORD", "RIVN", "LCID", "TSLA",
    "PFE", "MRNA", "JNJ", "ABBV", "LLY", "BMY",
    "XOM", "CVX", "OXY", "SLB", "HAL",
    "GLD", "SLV", "USO", "UNG",
}

# Words to exclude (common false positives)
EXCLUDE_WORDS = {
    "A", "I", "AM", "PM", "US", "UK", "EU", "IT", "BE", "DO", "GO", "NO",
    "OR", "IF", "AT", "BY", "TO", "OF", "ON", "IN", "IS", "RE", "DD",
    "WSB", "YOL", "OTC", "IPO", "ETF", "CEO", "CFO", "CTO", "SEC",
    "FDA", "FED", "GDP", "IMF", "AI", "ML", "EV", "AR", "VR",
    "ATH", "ATL", "IMO", "EPS", "PE", "PS", "PB", "ROI", "YTD",
}

# ── REDDIT SCRAPER ─────────────────────────────────────────────────────────────
def get_reddit_client(client_id, client_secret):
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent="wsb-tracker:v1.0 (by /u/anonymous)"
    )

def extract_tickers(text):
    """Extract stock tickers from text using regex + known tickers list."""
    # Match $TICKER or standalone UPPERCASE words 2-5 chars
    dollar_tickers = re.findall(r'\$([A-Z]{1,5})', text)
    word_tickers   = re.findall(r'\b([A-Z]{2,5})\b', text)
    all_found      = set(dollar_tickers + word_tickers)
    return {t for t in all_found if t in KNOWN_TICKERS and t not in EXCLUDE_WORDS}

def scrape_subreddits(subreddits, client_id, client_secret, post_limit=25):
    reddit  = get_reddit_client(client_id, client_secret)
    results = []
    ticker_counter = Counter()
    post_data = {}

    for sub_name in subreddits:
        try:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.hot(limit=post_limit):
                text    = f"{post.title} {post.selftext}"
                tickers = extract_tickers(text)

                for ticker in tickers:
                    ticker_counter[ticker] += 1
                    if ticker not in post_data:
                        post_data[ticker] = []
                    post_data[ticker].append({
                        "title":  post.title,
                        "url":    f"https://reddit.com{post.permalink}",
                        "score":  post.score,
                        "sub":    sub_name,
                    })
        except Exception as e:
            results.append({"error": f"r/{sub_name}: {str(e)}"})

    return ticker_counter, post_data

def get_price_data(tickers):
    price_data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist  = stock.history(period="5d")
            if len(hist) >= 2:
                today  = hist["Close"].iloc[-1]
                prev   = hist["Close"].iloc[-2]
                change = round(((today - prev) / prev) * 100, 2)
                price_data[ticker] = {
                    "price":  round(today, 2),
                    "change": change,
                }
        except:
            pass
    return price_data

# ── EMAIL ─────────────────────────────────────────────────────────────────────
def build_email(ticker_counter, post_data, price_data, subreddits):
    rows = ""
    for ticker, count in ticker_counter.most_common(20):
        pd    = price_data.get(ticker, {})
        price = pd.get("price", "—")
        chg   = pd.get("change", None)

        price_str = f"${price}" if price != "—" else "—"
        chg_color = "#2ecc71" if (chg or 0) >= 0 else "#e74c3c"
        chg_str   = f"{'+' if (chg or 0) >= 0 else ''}{chg}%" if chg is not None else "—"

        posts = post_data.get(ticker, [])[:2]
        post_links = " · ".join(
            f'<a href="{p["url"]}" style="color:#888;font-size:11px">{p["title"][:50]}…</a>'
            for p in posts
        )

        rows += f"""
        <tr style="border-bottom:1px solid #f0f0f0">
          <td style="padding:10px 12px;font-weight:700;font-size:14px">{ticker}</td>
          <td style="padding:10px 12px;text-align:center">
            <span style="background:#f0f0f0;padding:3px 10px;border-radius:12px;font-size:12px">{count}</span>
          </td>
          <td style="padding:10px 12px;font-size:13px">{price_str}</td>
          <td style="padding:10px 12px;color:{chg_color};font-size:13px">{chg_str}</td>
          <td style="padding:10px 12px">{post_links}</td>
        </tr>"""

    subs = ", ".join(f"r/{s}" for s in subreddits)
    return f"""
    <html><body style="font-family:monospace;background:#f7f6f3;padding:32px">
    <div style="max-width:640px;margin:0 auto;background:#fff;border:1px solid #ddd;padding:28px">
      <h2 style="margin:0 0 4px;font-size:15px">📊 Reddit Stock Buzz Report</h2>
      <p style="color:#888;font-size:12px;margin:0 0 20px">
        {subs} · {datetime.now().strftime("%Y-%m-%d %H:%M")} · top {len(ticker_counter)} tickers
      </p>
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead>
          <tr style="border-bottom:2px solid #eee;color:#aaa;font-size:10px;text-transform:uppercase">
            <th style="padding:8px 12px;text-align:left">Ticker</th>
            <th style="padding:8px 12px;text-align:center">Mentions</th>
            <th style="padding:8px 12px;text-align:left">Price</th>
            <th style="padding:8px 12px;text-align:left">1d Change</th>
            <th style="padding:8px 12px;text-align:left">Posts</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="font-size:11px;color:#bbb;margin-top:16px">
        reddit-buzz-tracker · not financial advice
      </p>
    </div>
    </body></html>"""

def send_email(sender, password, receiver, subject, body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = receiver
    msg.attach(MIMEText(body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(sender, password)
        s.sendmail(sender, receiver, msg.as_string())

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/scan", methods=["POST"])
def scan():
    data = request.json

    reddit_id     = data.get("reddit_id", "").strip()
    reddit_secret = data.get("reddit_secret", "").strip()
    subreddits    = data.get("subreddits", [])
    email_sender  = data.get("email_sender", "").strip()
    email_pass    = data.get("email_password", "").strip()
    email_recv    = data.get("email_receiver", "").strip()
    send_mail     = data.get("send_email", False)

    if not reddit_id or not reddit_secret:
        return jsonify({"error": "Reddit API credentials required."}), 400
    if not subreddits:
        return jsonify({"error": "Select at least one subreddit."}), 400

    try:
        ticker_counter, post_data = scrape_subreddits(subreddits, reddit_id, reddit_secret)
        top_tickers = [t for t, _ in ticker_counter.most_common(20)]
        price_data  = get_price_data(top_tickers)

        results = []
        for ticker, count in ticker_counter.most_common(20):
            pd = price_data.get(ticker, {})
            results.append({
                "ticker":   ticker,
                "mentions": count,
                "price":    pd.get("price"),
                "change":   pd.get("change"),
                "posts":    post_data.get(ticker, [])[:3],
            })

        if send_mail and email_sender and email_pass and email_recv:
            body    = build_email(ticker_counter, post_data, price_data, subreddits)
            subject = f"📊 Reddit Buzz: {', '.join(top_tickers[:5])}"
            threading.Thread(
                target=send_email,
                args=(email_sender, email_pass, email_recv, subject, body)
            ).start()

        return jsonify({"results": results, "scanned": subreddits})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
