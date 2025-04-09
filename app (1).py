import requests
import yfinance as yf
from textblob import TextBlob
from datetime import datetime
import pandas as pd
import streamlit as st
import os

NEWS_API_KEY = os.getenv("NEWSAPI_KEY")

keyword_asset_map = {
    "oil": ["CL=F", "XLE", "USD/CAD"],
    "gold": ["GC=F", "XAUUSD=X"],
    "fed": ["USDJPY=X", "^GSPC", "GC=F"],
    "inflation": ["USD=X", "GC=F", "BTC-USD"],
    "china": ["AUDUSD=X", "HG=F", "^GSPC"],
    "russia": ["CL=F", "NG=F", "GC=F"],
    "btc": ["BTC-USD"],
    "ethereum": ["ETH-USD"],
    "nasdaq": ["^IXIC"],
    "interest rates": ["USDJPY=X", "EURUSD=X", "GC=F"]
}

def fetch_news():
    url = f"https://newsapi.org/v2/everything?q=finance+OR+economy+OR+crypto+OR+stocks&from={datetime.now().date()}&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    articles = response.json().get("articles", [])
    return articles[:10]

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_indicators(ticker):
    try:
        data = yf.download(ticker, period="5d", interval="1h")
        if data.empty:
            print(f"No data for {ticker}")
            return None

        data['RSI'] = compute_rsi(data['Close'])
        data['MACD'] = data['Close'].ewm(span=12).mean() - data['Close'].ewm(span=26).mean()
        data['EMA_10'] = data['Close'].ewm(span=10).mean()

        latest = data.iloc[-1]
        rsi = round(latest['RSI'], 2)
        macd = round(latest['MACD'], 2)
        trend = latest['EMA_10'] - data['EMA_10'].iloc[-5]

        return {
            'price': round(latest['Close'], 2),
            'rsi': rsi,
            'macd': macd,
            'trend': round(trend, 2)
        }
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def analyze_articles(articles):
    trade_opportunities = []
    for article in articles:
        title = article['title']
        blob = TextBlob(title)
        sentiment = blob.sentiment.polarity

        matched_assets = set()
        for keyword in keyword_asset_map:
            if keyword in title.lower():
                matched_assets.update(keyword_asset_map[keyword])

        print(f"Article: {title}")
        print(f"Matched Assets: {matched_assets}")

        for asset in matched_assets:
            indicators = compute_indicators(asset)
            if indicators is None:
                continue

            score = sentiment * 0.5
            if indicators['rsi'] < 30:
                score += 0.2
            elif indicators['rsi'] > 70:
                score -= 0.2

            if indicators['macd'] > 0:
                score += 0.2
            else:
                score -= 0.2

            if indicators['trend'] > 0:
                score += 0.1
            else:
                score -= 0.1

            total_score = round(score * 100)
            direction = "BUY" if score > 0 else "SELL"

            trade_opportunities.append({
                "asset": asset,
                "headline": title,
                "sentiment": round(sentiment, 2),
                "rsi": indicators['rsi'],
                "macd": indicators['macd'],
                "trend": indicators['trend'],
                "score": abs(total_score),
                "direction": direction
            })

    return sorted(trade_opportunities, key=lambda x: x['score'], reverse=True)

# Streamlit UI
st.set_page_config(page_title="Live Trade Signal Feed", layout="wide")
st.title("📈 Smart Trade Opportunity Feed")

min_score = st.slider("Minimum Confidence Score to Display", 0, 100, 0)

with st.spinner("Fetching live data and analyzing..."):
    articles = fetch_news()
    opportunities = analyze_articles(articles)

if opportunities:
    filtered = [opp for opp in opportunities if opp['score'] >= min_score]
    buys = [opp for opp in filtered if opp['direction'] == "BUY"]
    sells = [opp for opp in filtered if opp['direction'] == "SELL"]

    if buys:
        st.subheader("🟢 Buy Opportunities")
        for opp in buys:
            st.markdown(f"### [BUY] {opp['asset']} — {opp['score']}% Confidence")
            st.markdown(f"**News:** {opp['headline']}")
            st.markdown(f"- Sentiment: `{opp['sentiment']}`\n- RSI: `{opp['rsi']}`\n- MACD: `{opp['macd']}`\n- Trend: `{opp['trend']}`")
            if opp['rsi'] < 20 or opp['rsi'] > 80:
                st.markdown(f"🧨 **Extreme RSI: {opp['rsi']}**")
            st.markdown("---")

    if sells:
        st.subheader("🔴 Sell Opportunities")
        for opp in sells:
            st.markdown(f"### [SELL] {opp['asset']} — {opp['score']}% Confidence")
            st.markdown(f"**News:** {opp['headline']}")
            st.markdown(f"- Sentiment: `{opp['sentiment']}`\n- RSI: `{opp['rsi']}`\n- MACD: `{opp['macd']}`\n- Trend: `{opp['trend']}`")
            if opp['rsi'] < 20 or opp['rsi'] > 80:
                st.markdown(f"🧨 **Extreme RSI: {opp['rsi']}**")
            st.markdown("---")

    if not buys and not sells:
        st.info("No opportunities meet your current filter. Try adjusting the minimum confidence.")
else:
    st.warning("No trade opportunities currently ranked. Please try again soon.")
