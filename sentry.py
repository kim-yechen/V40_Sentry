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

def get_v40_report():
    # 1. 대상 종목 설정 (기존 동일)
    fixed_targets = ['ERO', 'FCX', 'SCCO', 'SI=F', 'HG=F', 'AAPL', 'NVDA', 'TSLA'] 
    file_name = 'KIM_DIRECTOR_HUNTING_V40_REPORT.xlsx'
    excel_tickers = []
    if os.path.exists(file_name):
        for sheet in ['A_Shield_Report', 'B_Spear_Report', 'Full_Energy_Map']:
            try:
                df_sheet = pd.read_excel(file_name, sheet_name=sheet)
                if 'Symbol' in df_sheet.columns:
                    excel_tickers.extend(df_sheet['Symbol'].dropna().unique().tolist())
            except: continue
    targets = list(set(fixed_targets + excel_tickers))

    # --- 보고서 변수 초기화 ---
    alerts = "⚠️ *[신분 변동 감지!]*\n"
    hits = "\n🏟 *[오늘의 요새 (적정가 매수)]*\n"
    tracking = "\n🔍 *[신인류: 추적 및 관망]*\n"
    oracle_section = "\n🔮 *[V40 오라클: 시나리오 붕괴 관측]*\n" # 추가된 섹션
    
    found_alert = False; found_hit = False
    
    # 오라클 분석용 임시 저장소
    market_data = {}

    # 2. 전수 조사
    for symbol in targets:
        try:
            symbol = str(symbol).strip().replace('.', '-')
            df = yf.download(symbol, period="250d", interval="1d", progress=False)
            if len(df) < 200: continue
            
            c_today = df['Close'].iloc[-1]; c_yesterday = df['Close'].iloc[-2]
            ma200_today = df['Close'].rolling(200).mean().iloc[-1]
            ma200_yesterday = df['Close'].rolling(200).mean().iloc[-2]
            rsi = calculate_rsi(df['Close']).iloc[-1]
            
            market_data[symbol] = rsi # 오라클용 데이터 수집

            is_human_today = c_today > ma200_today
            is_human_yesterday = c_yesterday > ma200_yesterday

            if is_human_today != is_human_yesterday:
                status = "👑 [바람→신인류] 승격" if is_human_today else "💀 [신인류→위험] 강등"
                alerts += f"- {symbol}: {status}!\n"
                found_alert = True

            if is_human_today:
                if 30 <= rsi <= 55:
                    hits += f"- {symbol}: RSI {rsi:.1f} ✅\n"
                    found_hit = True
                else:
                    tracking += f"- {symbol}: RSI {rsi:.1f}\n"
        except: continue

    # 3. [WFC 오라클 로직 실행] - 형님의 제약 조건을 코드로 먼저 구현
    # 시나리오: [은/구리 폭등] -> [금리 인하 시나리오 삭제]
    silver_rsi = market_data.get('SI=F', 0)
    copper_rsi = market_data.get('HG=F', 0)
    
    if silver_rsi > 60 or copper_rsi > 60:
        oracle_section += "⚡ *붕괴 발생:* 원자재(은/구리) 과열 확정\n"
        oracle_section += "└ ❌ 삭제된 미래: '연착륙 및 금리 인하' 시나리오\n"
        oracle_section += "└ 💡 조언: 인플레 재점화 대응 준비 필요\n"
    else:
        oracle_section += "✅ 특이 붕괴 없음 (모든 미래 중첩 중)\n"

    # 4. 최종 메시지 조립
    if not found_alert: alerts += "특이사항 없음\n"
    if not found_hit: hits += "현재 요새 구간 종목 없음\n"

    final_msg = f"🛡 *[V40 전략 리포트]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n" + alerts + hits + tracking + oracle_section
    
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_report()
