import os
import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# --- [초기값 선언: NameError 방지용 Shortcut 방지] ---
vacuum_msg = "└ 🚦 유동성 데이터 연산 실패\n"
oracle_res = "✅ 특이 붕괴 없음\n"

def calculate_rsi(series, period=14):
    try:
        delta = series.diff()
        up = delta.clip(lower=0); down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=period - 1, adjust=False).mean()
        ema_down = down.ewm(com=period - 1, adjust=False).mean()
        rs = ema_up / (ema_down + 1e-10)
        return 100 - (100 / (1 + rs))
    except: return pd.Series([50.0] * len(series)) # 에러 시 중립값

def calculate_mfi(df, period=14):
    try:
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        rmf = tp * df['Volume']
        up_mf = pd.Series(0.0, index=df.index); dn_mf = pd.Series(0.0, index=df.index)
        up_mf[tp > tp.shift(1)] = rmf[tp > tp.shift(1)]
        dn_mf[tp < tp.shift(1)] = rmf[tp < tp.shift(1)]
        m_r = up_mf.rolling(window=period).sum() / (dn_mf.rolling(window=period).sum() + 1e-10)
        return 100 - (100 / (1 + m_r))
    except: return pd.Series([50.0] * len(df)) # 에러 시 중립값

def get_v40_report():
    global vacuum_msg, oracle_res # 전역 변수 참조 명시
    
    observatories = ['SPY', 'XLK', 'SMH', 'XLB', 'XLE', 'COPX', 'GDX', '^IRX', 'BIL']
    hunting_targets = ['SI=F', 'HG=F', 'ERO', 'FCX', 'SCCO', 'PSLV', 'CEF']
    core_sectors = ['FCX', 'SCCO', 'PSLV', 'PPL', 'DTE', 'ASTS', 'SI=F', 'COPX']

    file_name = 'KIM_DIRECTOR_HUNTING_V40_REPORT.xlsx'
    excel_tickers = []
    if os.path.exists(file_name):
        try:
            xls = pd.ExcelFile(file_name)
            for sheet in xls.sheet_names:
                df_sheet = pd.read_excel(file_name, sheet_name=sheet)
                if 'Symbol' in df_sheet.columns:
                    excel_tickers.extend(df_sheet['Symbol'].dropna().unique().tolist())
        except Exception as e:
            print(f"Excel Load Error: {e}")
    
    actual_prey = list(set([t for t in hunting_targets + excel_tickers if str(t) not in observatories]))
    all_symbols = list(set(actual_prey + observatories))

    kings = []
    downgrades = []
    market_data = {}

    # 2. 전수 조사 실행
    for symbol in all_symbols:
        try:
            time.sleep(0.5)
            # 404 에러 종목 방어: threads=False 및 정교한 예외처리
            df = yf.download(symbol, period="300d", interval="1d", progress=False, auto_adjust=True, threads=False)
            
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

            market_data[symbol] = {'df': df, 'price': curr_price, 'rsi': curr_rsi, 'mfi': curr_mfi, 'change': (curr_price-prev_price)/prev_price}

            if symbol in actual_prey:
                # [V-Energy 하한선: 70% 미만 필터]
                if v_energy < 70 and curr_price > ma200: continue

                if (curr_price > ma200) and (prev_price <= ma_series.iloc[-2]):
                    if ma200_slope > 0:
                        kings.append({'symbol': symbol, 'energy': v_energy, 'core': symbol in core_sectors})
                elif (curr_price < ma200) and (prev_price >= ma_series.iloc[-2]):
                    downgrades.append(symbol)
        except Exception as e:
            print(f"Skipping {symbol} due to error: {e}")
            continue

    # 3. [복구] 이면 분석 연산
    try:
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
    except: pass

    # 4. [복구] 오라클 연산
    try:
        silver = market_data.get('SI=F') or market_data.get('PSLV')
        rate_change = market_data.get('^IRX', {}).get('change', 0)
        if silver and silver['rsi'] > 60 and silver['mfi'] > 60:
            oracle_res = "🌀 유동성 중첩: 실물 강세\n" if rate_change <= 0 else "⚡ 붕괴: 악성 인플레\n"
    except: pass

    # 5. 리포트 조립 및 과열 필터
    kings = sorted(kings, key=lambda x: x['energy'], reverse=True)
    overheat_msg = "🚨 *[시장 과열: 사냥 금지]*\n" if len(kings) > 10 else ""
    display_kings = kings[:3] if len(kings) > 10 else kings
    
    true_kings_report = ""
    for k in display_kings:
        mark = "🚀" if k['core'] else "💎"
        true_kings_report += f"{mark} {k['symbol']}: 에너지 {k['energy']:.1f} 돌파\n"

    report_1 = (
        f"🛡 *[V40 1회차: 전략 기상도]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n"
        f"🌀 *[유동성 지수]*\n{vacuum_msg}\n"
        f"🔮 *[Oracle]*\n{oracle_res}\n"
        f"⚠️ *[신분 변동]*\n{overheat_msg}"
        f"👑 *[진성 승격]*\n{true_kings_report if true_kings_report else '진성 승격 없음'}\n\n"
        f"💀 *[강등]*: {', '.join(downgrades[:5])} 외 {max(0, len(downgrades)-5)}종"
    )

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": report_1, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_report()
