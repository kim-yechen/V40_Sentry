import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0); down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

def get_v40_brutal_test():
    # 형님의 주력 종목들
    targets = ['ERO', 'FCX', 'SCCO', 'SLV', 'SPY'] 
    
    report_body = "📊 *[무조건 강제 노출 리포트]*\n\n"
    
    for symbol in targets:
        try:
            df = yf.download(symbol, period="250d", interval="1d", progress=False)
            if df.empty:
                report_body += f"❌ {symbol}: 데이터 못 불러옴\n"
                continue
            
            c_today = float(df['Close'].iloc[-1])
            ma200 = float(df['Close'].rolling(200).mean().iloc[-1])
            rsi = float(calculate_rsi(df['Close']).iloc[-1])
            
            status = "👑 신인류" if c_today > ma200 else "🌪️ 바람"
            
            # 조건 없이 그냥 다 때려 넣습니다.
            report_body += f"📍 *{symbol}* ({status})\n"
            report_body += f"  - 현재가: {c_today:.2f}\n"
            report_body += f"  - 200일선: {ma200:.2f}\n"
            report_body += f"  - RSI: {rsi:.1f}\n\n"
            
        except Exception as e:
            report_body += f"❌ {symbol}: 에러({str(e)})\n"

    # 텔레그램 전송
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": report_body, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_brutal_test()
