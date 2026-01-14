import os
import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# ... (calculate_rsi, mfi 함수는 동일) ...

def get_v40_report():
    # 1. 역할 분담 (형님의 줏대 반영)
    # [지표용]: 절대 '오늘의 요새'에 나타나지 않음. 오직 기상 관측용.
    observatories = ['SPY', 'XLK', 'SMH', 'XLB', 'XLE', 'COPX', 'GDX', '^IRX', 'BIL']
    # [사냥용]: 형님이 실제로 매수 버튼을 누를 진짜 물건들.
    hunting_targets = ['SI=F', 'HG=F', 'ERO', 'FCX', 'SCCO', 'PSLV', 'CEF']
    
    file_name = 'KIM_DIRECTOR_HUNTING_V40_REPORT.xlsx'
    excel_tickers = []
    if os.path.exists(file_name):
        for sheet in ['A_Shield_Report', 'B_Spear_Report']:
            try:
                df_sheet = pd.read_excel(file_name, sheet_name=sheet)
                if 'Symbol' in df_sheet.columns:
                    excel_tickers.extend(df_sheet['Symbol'].dropna().unique().tolist())
            except: continue
    
    # 엑셀 종목 중 지표용이 섞여있다면 제거 (사냥터 순도 유지)
    actual_prey = list(set([t for t in hunting_targets + excel_tickers if t not in observatories]))
    all_symbols = list(set(actual_prey + observatories))

    alerts = "⚠️ *[신분 변동 감지!]*\n"; hits = "\n🏟 *[오늘의 요새 (적정가 매수)]*\n"
    tracking = "\n🔍 *[신인류: 추적 및 관망]*\n"
    market_data = {}
    rs_scores = {}
    found_alert = False; found_hit = False

    # 2. 데이터 수집 및 사냥감 분석
    for symbol in all_symbols:
        try:
            time.sleep(0.7)
            df = yf.download(symbol, period="300d", interval="1d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            close = df['Close']
            market_data[symbol] = {'df': df, 'price': float(close.iloc[-1]), 'rsi': calculate_rsi(close).iloc[-1], 'mfi': calculate_mfi(df).iloc[-1], 'change': (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]}

            # [핵심] 사냥감(actual_prey)만 요새/신분 변동 로직 적용
            if symbol in actual_prey:
                ma200 = close.rolling(200).mean().iloc[-1]
                prev_ma = close.rolling(200).mean().iloc[-2]
                if (market_data[symbol]['price'] > ma200) != (float(close.iloc[-2]) > prev_ma):
                    alerts += f"- {symbol}: {'👑 [승격]' if market_data[symbol]['price'] > ma200 else '💀 [강등]'}!\n"; found_alert = True
                if market_data[symbol]['price'] > ma200:
                    if 30 <= market_data[symbol]['rsi'] <= 55:
                        hits += f"- {symbol}: RSI {market_data[symbol]['rsi']:.1f} ✅\n"; found_hit = True
                    else: tracking += f"- {symbol}: RSI {market_data[symbol]['rsi']:.1f}\n"
        except: continue

    # 3. [이면 분석] RS Matrix & 유동성 진공 (지표용 활용)
    vacuum_msg = "\n🌀 *[유동성 진공/전이 지수]*\n"
    if 'SPY' in market_data:
        spy_c = market_data['SPY']['df']['Close']
        for sec in ['XLK', 'SMH', 'XLB', 'COPX', 'GDX']:
            if sec in market_data:
                rs_ratio = market_data[sec]['df']['Close'] / spy_c
                rs_scores[sec] = (rs_ratio.iloc[-1] - rs_ratio.iloc[-5]) / rs_ratio.iloc[-5] * 100
        
        tech_rs = (rs_scores.get('XLK', 0) + rs_scores.get('SMH', 0)) / 2
        real_rs = (rs_scores.get('XLB', 0) + rs_scores.get('COPX', 0) + rs_scores.get('GDX', 0)) / 3
        vacuum_msg += f"└ {'🚀 전이 포착' if tech_rs < 0 and real_rs > 0 else '⚠️ 블랙홀' if tech_rs > 0 and real_rs < 0 else '🚦 혼조'}: (T:{tech_rs:.1f}% / R:{real_rs:.1f}%)\n"

    # 4. [오라클] 최종 판정
    oracle_section = "\n🔮 *[V40 오라클]*\n"
    # ... (은/금리 로직 수행) ...

    # 5. 최종 메시지 조립
    if not found_alert: alerts += "특이사항 없음\n"
    if not found_hit: hits += "현재 요새 구간 종목 없음\n"
    
    final_msg = f"🛡 *[V40 전략 리포트]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n" + alerts + hits + tracking + vacuum_msg + oracle_section
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"})
