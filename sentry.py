import os
import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0); down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / (ema_down + 1e-10)
    return 100 - (100 / (1 + rs))

def calculate_mfi(df, period=14):
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    rmf = tp * df['Volume']
    up_mf = pd.Series(0.0, index=df.index); dn_mf = pd.Series(0.0, index=df.index)
    up_mf[tp > tp.shift(1)] = rmf[tp > tp.shift(1)]
    dn_mf[tp < tp.shift(1)] = rmf[tp < tp.shift(1)]
    m_r = up_mf.rolling(window=period).sum() / (dn_mf.rolling(window=period).sum() + 1e-10)
    return 100 - (100 / (1 + m_r))

def get_v40_report():
    # 1. 역할 분담
    observatories = ['SPY', 'XLK', 'SMH', 'XLB', 'XLE', 'COPX', 'GDX', '^IRX', 'BIL']
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
            market_data[symbol] = {
                'df': df, 
                'price': float(close.iloc[-1]), 
                'rsi': float(calculate_rsi(close).iloc[-1]), 
                'mfi': float(calculate_mfi(df).iloc[-1]), 
                'change': float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2])
            }

            if symbol in actual_prey:
                ma200 = close.rolling(200).mean().iloc[-1]
                prev_ma = close.rolling(200).mean().iloc[-2]
                if (market_data[symbol]['price'] > ma200) != (float(close.iloc[-2]) > prev_ma):
                    alerts += f"- {symbol}: {'👑 [승격]' if market_data[symbol]['price'] > ma200 else '💀 [강등]'}!\n"; found_alert = True
                if market_data[symbol]['price'] > ma200:
                    if 30 <= market_data[symbol]['rsi'] <= 55:
                        hits += f"- {symbol}: RSI {market_data[symbol]['rsi']:.1f} ✅\n"; found_hit = True
                    else: tracking += f"- {symbol}: RSI {market_data[symbol]['rsi']:.1f}\n"
        except Exception: continue

    # 3. [이면 분석] 유동성 전이 지수
    vacuum_msg = "\n🌀 *[유동성 진공/전이 지수]*\n"
    if 'SPY' in market_data:
        spy_c = market_data['SPY']['df']['Close']
        for sec in ['XLK', 'SMH', 'XLB', 'COPX', 'GDX']:
            if sec in market_data:
                rs_ratio = market_data[sec]['df']['Close'] / spy_c
                rs_scores[sec] = (rs_ratio.iloc[-1] - rs_ratio.iloc[-5]) / rs_ratio.iloc[-5] * 100
        
        tech_rs = (rs_scores.get('XLK', 0) + rs_scores.get('SMH', 0)) / 2
        real_rs = (rs_scores.get('XLB', 0) + rs_scores.get('COPX', 0) + rs_scores.get('GDX', 0)) / 3
        status = "🚀 전이 포착" if tech_rs < 0 and real_rs > 0 else "⚠️ 블랙홀" if tech_rs > 0 and real_rs < 0 else "🚦 혼조"
        vacuum_msg += f"└ {status}: (T:{tech_rs:.1f}% / R:{real_rs:.1f}%)\n"

    # 4. [오라클] 최종 판정
    oracle_section = "\n🔮 *[V40 오라클]*\n"
    silver = market_data.get('SI=F') or market_data.get('SLV')
    rate_change_val = market_data.get('^IRX', {}).get('change')
    if rate_change_val is None and 'BIL' in market_data: rate_change_val = market_data['BIL']['change'] * -1

    if silver and rate_change_val is not None:
        s_rsi = silver['rsi']
        if s_rsi > 60 and silver['mfi'] > 60:
            status = "⚡ *붕괴:* [악성 인플레]" if rate_change_val > 0 else "🌀 *유동성 중첩:* [실물 강세]"
            oracle_section += f"{status}\n└ 근거: 에너지 임계점 돌파\n"
        else: oracle_section += "✅ 특이 붕괴 없음\n"
    else: oracle_section += "❓ 데이터 부족으로 분석 불가\n"

    # 5. 메시지 최종 조립 (함수 내부로 정렬 완료!)
    if not found_alert:
        alerts += "특이사항 없음\n"
    if not found_hit:
        hits += "현재 요새 구간 종목 없음\n"
    
    report_parts = [
        f"🛡 *[V40 전략 리포트]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n",
        alerts, hits, tracking, vacuum_msg, oracle_section
    ]
    final_msg = "\n".join(report_parts)
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
        res = requests.post(url, data=payload, timeout=10)
        if res.status_code != 200:
            payload["parse_mode"] = ""
            requests.post(url, data=payload)
    except Exception as e:
        print(f"발송 실패: {e}")

# 마지막 실행 구문 (반드시 포함되어야 함)
if __name__ == "__main__":
    get_v40_report()
