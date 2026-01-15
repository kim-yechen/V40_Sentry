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
    # 1. 대상 확보 (기존 로직 유지)
    observatories = ['SPY', 'XLK', 'SMH', 'XLB', 'XLE', 'COPX', 'GDX', '^IRX', 'BIL']
    hunting_targets = ['SI=F', 'HG=F', 'ERO', 'FCX', 'SCCO', 'PSLV', 'CEF']
    
    file_name = 'KIM_DIRECTOR_HUNTING_V40_REPORT.xlsx'
    excel_tickers = []
    if os.path.exists(file_name):
        xls = pd.ExcelFile(file_name)
        for sheet in xls.sheet_names:
            df_sheet = pd.read_excel(file_name, sheet_name=sheet)
            if 'Symbol' in df_sheet.columns:
                excel_tickers.extend(df_sheet['Symbol'].dropna().unique().tolist())
    
    actual_prey = list(set([t for t in hunting_targets + excel_tickers if str(t) not in observatories]))
    all_symbols = list(set(actual_prey + observatories))

    alerts = ""; hits = ""; tracking = ""
    market_data = {}
    found_alert = False; found_hit = False

    # 2. 전수 조사 실행 (수정 포인트: market_data에 모든 지표 엄격히 저장)
    for symbol in all_symbols:
        try:
            time.sleep(0.4)
            df = yf.download(symbol, period="300d", interval="1d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            close = df['Close']
            ma_series = close.rolling(200).mean()
            ma200 = ma_series.iloc[-1]
            ma200_slope = ma200 - ma_series.iloc[-5]
            
            curr_price = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            curr_rsi = float(calculate_rsi(close).iloc[-1])
            curr_mfi = float(calculate_mfi(df).iloc[-1])
            change = (curr_price - prev_price) / prev_price

            # [데이터 저장 - 기상도 연산용]
            market_data[symbol] = {'df': df, 'price': curr_price, 'rsi': curr_rsi, 'mfi': curr_mfi, 'change': change}

            # [Negative Check] 이상 급변동 필터
            if abs(change) > 0.3: 
                alerts += f"- {symbol}: ⚠️ 이상 급변동 감지 (검증 필요)\n"
                found_alert = True
                continue

            if symbol in actual_prey:
                # [신분 변동 판정 - 형님 로직 그대로]
                if (curr_price > ma200) and (prev_price <= ma_series.iloc[-2]):
                    status = "👑 [진성 승격]" if ma200_slope > 0 else "✨ [기술적 승격]"
                    alerts += f"- {symbol}: {status}!\n"
                    found_alert = True
                elif (curr_price < ma200) and (prev_price >= ma_series.iloc[-2]):
                    alerts += f"- {symbol}: 💀 [강등]\n"
                    found_alert = True
                
                # [사냥 구간 판정]
                if curr_price > ma200:
                    disparity = (curr_price - ma200) / ma200
                    if 30 <= curr_rsi <= 55:
                        hits += f"- {symbol}: RSI {curr_rsi:.1f} ✅ [요새]\n"; found_hit = True
                    elif 55 < curr_rsi <= 65 and disparity <= 0.05:
                        hits += f"- {symbol}: RSI {curr_rsi:.1f} 🔥 [초입]\n"; found_hit = True
                    else:
                        tracking += f"- {symbol}: RSI {curr_rsi:.1f}\n"
        except: continue

    # 3. [복구] 이면 분석 (기상도용)
    vacuum_msg = "└ 🚦 데이터 부족으로 연산 불가\n"
    if 'SPY' in market_data:
        spy_c = market_data['SPY']['df']['Close']
        rs_scores = {}
        for sec in ['XLK', 'SMH', 'XLB', 'COPX', 'GDX']:
            if sec in market_data:
                ratio = market_data[sec]['df']['Close'] / spy_c
                rs_scores[sec] = (ratio.iloc[-1] - ratio.iloc[-5]) / ratio.iloc[-5] * 100
        
        if rs_scores:
            t_rs = (rs_scores.get('XLK', 0) + rs_scores.get('SMH', 0)) / 2
            r_rs = (rs_scores.get('XLB', 0) + rs_scores.get('COPX', 0) + rs_scores.get('GDX', 0)) / 3
            v_status = "🚀 전이 포착" if t_rs < 0 and r_rs > 0 else "🚦 혼조"
            vacuum_msg = f"└ {v_status}: (T:{t_rs:.1f}% / R:{r_rs:.1f}%)\n"

    # 4. [복구] 오라클 (기상도용)
    silver = market_data.get('SI=F') or market_data.get('PSLV')
    rate_change = market_data.get('^IRX', {}).get('change', 0)
    oracle_res = "✅ 특이 붕괴 없음\n"
    if silver and silver['rsi'] > 60 and silver['mfi'] > 60:
        oracle_res = "🌀 유동성 중첩: 실물 강세\n" if rate_change <= 0 else "⚡ 붕괴: 악성 인플레\n"

    # 5. 리포트 조립 (형님이 원하신 전체 나열 방식)
    report_1 = (
        f"🛡 *[V40 1회차: 전략 기상도]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n"
        f"🌀 *[유동성 진공/전이 지수]*\n{vacuum_msg}\n"
        f"🔮 *[V40 오라클]*\n{oracle_res}\n"
        f"⚠️ *[신분 변동 감지!]*\n{alerts if found_alert else '특이사항 없음'}"
    )

    report_2 = (
        f"🏟 *[V40 2회차: 실전 사냥 보고]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n"
        f"🏟 *[오늘의 요새 & 초입]*\n{hits if found_hit else '구간 종목 없음'}\n"
        f"🔍 *[신인류: 추적 및 관망]*\n{tracking}"
    )

    # 발송
    for msg in [report_1, report_2]:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        time.sleep(2)

if __name__ == "__main__":
    get_v40_report()
