import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

def get_v40_report():
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("🚨 Secrets 설정 에러")
        return

    report = f"🛡️ *[V40 데일리 센트리]*\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    TARGETS = ['FCX', 'ERO', 'SCCO', 'IWM', 'HG=F', 'SI=F']
    
    for symbol in TARGETS:
        try:
            df = yf.download(symbol, period="60d", interval="1d", progress=False)
            if df.empty: continue
            
            # RSI 직접 계산 (외부 라이브러리 의존성 제거)
            df['RSI'] = calculate_rsi(df['Close'])
            
            price = df['Close'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            
            status = "⚪ 대기"
            if 30 <= rsi <= 55: status = "🟡 눌림목"
            elif rsi > 70: status = "⚠️ 과열"
            
            report += f"\n📌 *{symbol}*: ${price:.2f}\n   └ RSI: {rsi:.1f} | {status}\n"
        except Exception as e:
            print(f"❌ {symbol} 에러: {e}")
            continue

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": report, "parse_mode": "Markdown"}
    requests.post(url, data=payload)
    print("🚀 보고서 전송 시도 완료")

if __name__ == "__main__":
    get_v40_report()
