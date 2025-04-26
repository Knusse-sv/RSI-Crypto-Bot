
import time
import requests
import hmac
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime

API_KEY = 'YOUR_BINANCE_API_KEY'
API_SECRET = 'YOUR_BINANCE_API_SECRET'
BASE_URL = 'https://api.binance.com'

SYMBOL = 'BTCUSDT'
INTERVAL = '1h'
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_QUANTITY = 0.001  # Adjust based on your balance

def get_klines(symbol, interval, limit=100):
    url = f'{BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data)
    df = df.iloc[:, 0:6]
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    df['close'] = df['close'].astype(float)
    return df

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def create_order(side, quantity, symbol=SYMBOL):
    timestamp = int(time.time() * 1000)
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': quantity,
        'timestamp': timestamp
    }
    query_string = '&'.join([f"{key}={params[key]}" for key in params])
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature
    headers = {'X-MBX-APIKEY': API_KEY}
    url = f"{BASE_URL}/api/v3/order"
    response = requests.post(url, headers=headers, params=params)
    print(response.json())

def run_bot():
    df = get_klines(SYMBOL, INTERVAL)
    rsi = calculate_rsi(df['close'])
    latest_rsi = rsi.iloc[-1]
    print(f"[{datetime.now()}] RSI: {latest_rsi:.2f}")

    if latest_rsi < RSI_OVERSOLD:
        print("RSI indicates OVERSOLD – Buying!")
        create_order('BUY', TRADE_QUANTITY)
    elif latest_rsi > RSI_OVERBOUGHT:
        print("RSI indicates OVERBOUGHT – Selling!")
        create_order('SELL', TRADE_QUANTITY)
    else:
        print("No trade condition met.")

if __name__ == "__main__":
    while True:
        try:
            run_bot()
            time.sleep(3600)  # Run every hour
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)
