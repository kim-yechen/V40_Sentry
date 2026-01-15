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
    # 1. 전수 조사 대상 (엑셀 뒤지기)
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

    # 2. 전수 조사 실행 (추세/기울기/안착 로직 탑재)
    for symbol in all_symbols:
        try:
            time.sleep(0.5)
            df = yf.download(symbol, period="300d", interval="1d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            close = df['Close']
            ma_series = close.rolling(200).mean()
            ma200 = ma_series.iloc[-1]
            ma200_slope = ma200 - ma_series.iloc[-5] # 5일 기울기
            
            curr_price = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            curr_rsi = float(calculate_rsi(close).iloc[-1])
            curr_mfi = float(calculate_mfi(df).iloc[-1])
            change = (curr_price - prev_price) / prev_price

            # [Negative Check] 데이터 상식 검증
            if abs(change) > 0.3: 
                alerts += f"- {symbol}: ⚠️ 이상 급변동 감지 (검증 필요)\n"
                continue

            if symbol in actual_prey:
                # 3일 안착 여부 확인
                stay_confirm = (close.tail(3) > ma_series.tail(3)).all()
                
                # [개선된 신분 변동] 단순 돌파가 아닌 '추세 확정'
                if (curr_price > ma200) and (prev_price <= ma_series.iloc[-2]):
                    if ma200_slope > 0:
                        alerts += f"- {symbol}: 👑 [진성 승격] (기울기 우상향 컨펌)\n"
                    else:
                        alerts += f"- {symbol}: ✨ [기술적 승격] (단기 반등 주의)\n"
                    found_alert = True
                elif (curr_price < ma200) and (prev_price >= ma_series.iloc[-2]):
                    alerts += f"- {symbol}: 💀 [강등]\n"
                    found_alert = True
                
                # [개선된 사냥 구간] 요새 + 대세 상승 초입
                if curr_price > ma200:
                    disparity = (curr_price - ma200) / ma200 # 괴리율
                    if 30 <= curr_rsi <= 55:
                        hits += f"- {symbol}: RSI {curr_rsi:.1f} ✅ [요새 구간]\n"; found_hit = True
                    elif 55 < curr_rsi <= 65 and disparity <= 0.05: # 대세 상승 초입 필터
                        hits += f"- {symbol}: RSI {curr_rsi:.1f} 🔥 [추세 추종 가능]\n"; found_hit = True
                    else:
                        tracking += f"- {symbol}: RSI {curr_rsi:.1f}\n"

            # 기상도용 데이터 저장
            market_data[symbol] = {'df': df, 'price': curr_price, 'rsi': curr_rsi, 'mfi': curr_mfi, 'change': change}
        except: continue

    # (3, 4번 기상도/오라클 로직 생략 - 기존과 동일하게 유지하되 메시지만 2개로 분리)
    # ... (생략된 부분: vacuum_msg, oracle_res 조립) ...

    # 메시지 발송
    report_1 = f"🛡 *[V40 1회차: 전략 기상도]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n⚠️ *[신분 변동 감지!]*\n{alerts if found_alert else '특이사항 없음'}"
    report_2 = f"🏟 *[V40 2회차: 실전 사냥 보고]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n🏟 *[오늘의 요새]*\n{hits if found_hit else '구간 종목 없음'}\n\n🔍 *[추적/관망]*\n{tracking}"

    for msg in [report_1, report_2]:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        time.sleep(2)

if __name__ == "__main__":
    get_v40_report()
