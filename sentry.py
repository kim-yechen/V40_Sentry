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
    observatories = ['SPY', 'XLK', 'SMH', 'XLB', 'XLE', 'COPX', 'GDX', '^IRX', 'BIL']
    hunting_targets = ['SI=F', 'HG=F', 'ERO', 'FCX', 'SCCO', 'PSLV', 'CEF']
    core_sectors = ['FCX', 'SCCO', 'PSLV', 'PPL', 'DTE', 'ASTS', 'SI=F', 'COPX']

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

    # 분류용 리스트
    kings = [] # 👑 진성 승격 (에너지 70+ & 기울기+)
    downgrades = [] # 💀 강등
    hits = ""; tracking = ""; market_data = {}

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
            
            curr_price = float(close.iloc[-1]); prev_price = float(close.iloc[-2])
            curr_rsi = float(calculate_rsi(close).iloc[-1])
            curr_mfi = float(calculate_mfi(df).iloc[-1])
            v_energy = (curr_mfi * 0.6) + (curr_rsi * 0.4)

            market_data[symbol] = {'df': df, 'price': curr_price, 'rsi': curr_rsi, 'mfi': curr_mfi}

            if symbol in actual_prey:
                # [필터 1: 에너지 70% 미만은 리포트에서 영구 제명]
                if v_energy < 70 and curr_price > ma200: continue

                # [신분 판정]
                if (curr_price > ma200) and (prev_price <= ma_series.iloc[-2]):
                    if ma200_slope > 0:
                        kings.append({'symbol': symbol, 'energy': v_energy, 'core': symbol in core_sectors})
                elif (curr_price < ma200) and (prev_price >= ma_series.iloc[-2]):
                    downgrades.append(symbol)

                # [사냥 구간]
                if curr_price > ma200 and v_energy >= 70:
                    if 30 <= curr_rsi <= 55: hits += f"- {symbol}: E:{v_energy:.1f} ✅ [요새]\n"
                    elif 55 < curr_rsi <= 65: hits += f"- {symbol}: E:{v_energy:.1f} 🔥 [초입]\n"
        except: continue

    # 3. 이면 분석 (동일 유지)
    # ... (vacuum_msg, oracle_res 연산) ...

    # 4. [필터 2: 나열 금지 및 과열 로직]
    kings = sorted(kings, key=lambda x: x['energy'], reverse=True)
    king_count = len(kings)
    
    overheat_msg = ""
    if king_count > 10:
        overheat_msg = "🚨 *[시장 과열: 사냥 금지]* - 승격 종목 폭주 중\n"
        kings = kings[:3] # 최강 3개만 남김
    
    true_kings_report = ""
    for k in kings:
        mark = "🚀" if k['core'] else "💎"
        true_kings_report += f"{mark} {k['symbol']}: 에너지 {k['energy']:.1f} 돌파\n"

    # 5. 리포트 조립
    report_1 = (
        f"🛡 *[V40 1회차: 전략 기상도]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n"
        f"🌀 *[유동성 지수]*\n{vacuum_msg}\n"
        f"🔮 *[Oracle]*\n{oracle_res}\n"
        f"⚠️ *[신분 변동]*\n{overheat_msg}"
        f"👑 *[진성 승격]*\n{true_kings_report if kings else '진성 승격 없음'}\n\n"
        f"💀 *[강등]*: {', '.join(downgrades[:5])} 외 {max(0, len(downgrades)-5)}종"
    )

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": report_1, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_report()
