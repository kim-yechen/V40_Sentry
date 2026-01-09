import os
import yfinance as yf
import pandas as pd
import requests  # <-- 요놈이 빠졌었습니다. 죄송합니다!
from datetime import datetime

# 텔레그램 설정값 불러오기
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0); down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

def get_v40_test_report():
    # 테스트용 핵심 종목 5개
    targets = ['ERO', 'FCX', 'SCCO', 'SLV', 'SPY'] 
    
    alerts = "⚠️ *[테스트: 신분 변동 체크]*\n"
    hits = "\n🏟️ *[테스트: 모든 신인류 강제 노출]*\n"
    tracking = "\n🔍 *[추적 및 관망]*\n"
    
    for symbol in targets:
        try:
            # 데이터 수집 (Negative Check: 250일치)
            df = yf.download(symbol, period="250d", interval="1d", progress=False)
            if df.empty: continue
            
            c_today = df['Close'].iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rsi = calculate_rsi(df['Close']).iloc[-1]

            # 테스트를 위해 기준을 대폭 완화 (RSI 90 이하 모두 출력)
            if c_today > ma200:
                hits += f"- {symbol}: RSI {rsi:.1f} (작동 확인) ✅\n"
            else:
                tracking += f"- {symbol}: RSI {rsi:.1f} (200일선 아래)\n"
        except Exception as e:
            print(f"❌ {symbol} 분석 중 오류: {e}")

    final_msg = "🧪 *[시스템 생존 확인 테스트]*\n" + alerts + hits + tracking
    
    # 텔레그램 전송
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_test_report()
