import os
import yfinance as yf
import pandas_ta as ta
import requests
import pandas as pd
from datetime import datetime

# 깃허브 금고(Secrets)에서 정보를 안전하게 꺼냅니다
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
TARGETS = ['FCX', 'ERO', 'SCCO', 'IWM', 'HG=F', 'SI=F']

def get_v40_report():
    report = f"🛡️ *[V40 데일리 센트리]*\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    for symbol in TARGETS:
        try:
            df = yf.download(symbol, period="60d", interval="1d", progress=False)
            if df.empty: continue
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd = ta.macd(df['Close'])
            df = pd.concat([df, macd], axis=1)
            
            price = df['Close'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            macd_line = df['MACD_12_26_9'].iloc[-1]
            macd_sig = df['MACDs_12_26_9'].iloc[-1]
            
            status = "⚪ 대기"
            if 30 <= rsi <= 55:
                status = "🟡 눌림목"
                if macd_line > macd_sig: status = "🔥 *[사격 적기]*"
            elif rsi > 70: status = "⚠️ 과열"
            
            report += f"\n📌 *{symbol}*: ${price:.2f}\n   └ RSI: {rsi:.1f} | {status}\n"
        except: continue

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": report, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

if __name__ == "__main__":
    get_v40_report()
