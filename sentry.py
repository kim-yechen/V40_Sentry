import os
import yfinance as yf
import pandas_ta as ta
import requests
import pandas as pd
from datetime import datetime

# 깃허브 금고(Secrets)에서 정보를 가져옵니다
# [네거티브 체크] 데이터가 없어서 터지는 것을 방지하기 위해 .get()을 사용합니다.
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def get_v40_report():
    # 1. 열쇠 검사 (이게 18번 줄 근처에서 터지는 걸 막아줍니다)
    if not TELEGRAM_TOKEN or not CHAT_ID:
        error_msg = f"🚨 [설정 에러] 열쇠가 부족합니다!\nTOKEN 존재여부: {bool(TELEGRAM_TOKEN)}\nID 존재여부: {bool(CHAT_ID)}"
        print(error_msg)
        return

    print("🚀 V40 분석 엔진 가동 중...")
    report = f"🛡️ *[V40 데일리 센트리]*\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    TARGETS = ['FCX', 'ERO', 'SCCO', 'IWM', 'HG=F', 'SI=F']
    
    for symbol in TARGETS:
        try:
            # 데이터 수집 (Negative Check: 데이터가 비었는지 확인)
            df = yf.download(symbol, period="60d", interval="1d", progress=False)
            if df.empty or len(df) < 14: continue
            
            # 지표 계산
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            price = df['Close'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            
            # 상태 판독
            status = "⚪ 대기"
            if 30 <= rsi <= 55: status = "🟡 눌림목"
            elif rsi > 70: status = "⚠️ 과열"
            
            report += f"\n📌 *{symbol}*: ${price:.2f}\n   └ RSI: {rsi:.1f} | {status}\n"
        except Exception as e:
            print(f"❌ {symbol} 분석 중 에러: {e}")
            continue

    # 2. 텔레그램 발송
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": report, "parse_mode": "Markdown"}
    
    try:
        res = requests.post(url, data=payload)
        if res.status_code == 200:
            print("✅ 형님 폰으로 보고서 전송 성공!")
        else:
            print(f"❌ 전송 실패! 서버 응답: {res.text}")
    except Exception as e:
        print(f"❌ 통신 에러 발생: {e}")

if __name__ == "__main__":
    get_v40_report()
