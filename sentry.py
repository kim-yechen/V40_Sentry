import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def get_v40_report():
    # 1. 엑셀 파일 읽기 (모든 시트 통합)
    file_name = 'KIM_DIRECTOR_HUNTING_V40_REPORT.xlsx'
    if not os.path.exists(file_name):
        print(f"🚨 파일을 찾을 수 없습니다: {file_name}")
        return

    all_tickers = []
    # 형님이 말씀하신 시트들을 하나씩 읽습니다.
    for sheet in ['A_Shield_Report', 'B_Spear_Report', 'Full_Energy_Map']:
        try:
            df_sheet = pd.read_excel(file_name, sheet_name=sheet)
            if 'Symbol' in df_sheet.columns:
                all_tickers.extend(df_sheet['Symbol'].dropna().unique().tolist())
        except:
            continue
    
    targets = list(set(all_tickers)) # 중복 제거
    
    hits = "🛡️ *[오늘의 요세 후보]*\n"
    alerts = "⚠️ *[신분 변동 감지!]*\n"
    
    # [1+1-1 준수] 분석 로직 가동
    for symbol in targets:
        try:
            symbol = str(symbol).strip().replace('.', '-')
            df = yf.download(symbol, period="250d", interval="1d", progress=False)
            if len(df) < 200: continue
            
            c_today = df['Close'].iloc[-1]
            c_yesterday = df['Close'].iloc[-2]
            ma200_today = df['Close'].rolling(200).mean().iloc[-1]
            ma200_yesterday = df['Close'].rolling(200).mean().iloc[-2]
            
            # RSI 계산 (EMA 방식)
            delta = df['Close'].diff()
            up = delta.clip(lower=0); down = -1 * delta.clip(upper=0)
            ema_up = up.ewm(com=13, adjust=False).mean()
            ema_down = down.ewm(com=13, adjust=False).mean()
            rsi = (100 - (100 / (1 + (ema_up / ema_down)))).iloc[-1]

            is_human_today = c_today > ma200_today
            is_human_yesterday = c_yesterday > ma200_yesterday

            # 승격/강등 로직
            if is_human_today and not is_human_yesterday:
                alerts += f"✨ {symbol}: [바람] → *[신인류]* 승격!\n"
            elif not is_human_today and is_human_yesterday:
                alerts += f"🚨 {symbol}: [신인류] → *[강등]* (주의)\n"

            # 요세 후보 로직
            if is_human_today and 30 <= rsi <= 55:
                hits += f"✅ {symbol} (신인류): RSI {rsi:.1f}. (기회)\n"

        except: continue

    final_msg = f"🛡️ *[V40 전략 리포트]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n" + alerts + "\n" + hits
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_report()
