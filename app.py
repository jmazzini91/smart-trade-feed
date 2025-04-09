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
