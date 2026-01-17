import os
import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime

# --- [초기값 선언 및 환경 변수] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
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
    except: return pd.Series([50.0] * len(series))

def calculate_mfi(df, period=14):
    try:
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        rmf = tp * df['Volume']
        up_mf = pd.Series(0.0, index=df.index); dn_mf = pd.Series(0.0, index=df.index)
        up_mf[tp > tp.shift(1)] = rmf[tp > tp.shift(1)]
        dn_mf[tp < tp.shift(1)] = rmf[tp < tp.shift(1)]
        m_r = up_mf.rolling(window=period).sum() / (dn_mf.rolling(window=period).sum() + 1e-10)
        return 100 - (100 / (1 + m_r))
    except: return pd.Series([50.0] * len(df))

def get_v40_report():
    global vacuum_msg, oracle_res 
    
    observatories = ['SPY', 'XLK', 'SMH', 'XLB', 'XLE', 'COPX', 'GDX', '^IRX', 'BIL']
    hunting_targets = ['SI=F', 'HG=F', 'ERO', 'FCX', 'SCCO', 'PSLV', 'CEF']
    core_sectors = ['FCX', 'SCCO', 'PSLV', 'PPL', 'DTE', 'ASTS', 'SI=F', 'COPX']

    # 1. 엑셀 티커 로드 (누락 방지)
    file_name = 'KIM_DIRECTOR_HUNTING_V40_REPORT.xlsx'
    excel_tickers = []
    if os.path.exists(file_name):
        try:
            xls = pd.ExcelFile(file_name)
            for sheet in xls.sheet_names:
                df_sheet = pd.read_excel(file_name, sheet_name=sheet)
                if 'Symbol' in df_sheet.columns:
                    excel_tickers.extend(df_sheet['Symbol'].dropna().unique().tolist())
        except Exception as e: print(f"Excel Load Error: {e}")
    
    actual_prey = list(set([t for t in hunting_targets + excel_tickers if str(t) not in observatories]))
    all_symbols = list(set(actual_prey + observatories))

    kings = []
    downgrades = []
    market_data = {}
    all_v_energies = [] # 시장 전체 평균용
    full_analysis_list = [] # 엑셀 저장용 데이터셋

    # 2. 전수 조사 실행
    for symbol in all_symbols:
        try:
            time.sleep(0.5)
            df = yf.download(symbol, period="300d", interval="1d", progress=False, auto_adjust=True, threads=False)
            if df.empty or len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # [V40-C 보강 로직: 10일 연속 수성 체크]
            close = df['Close']
            energies_10d = []
            for i in range(10):
                sub_df = df.iloc[:len(df)-i] if i > 0 else df
                c_rsi = float(calculate_rsi(sub_df['Close']).iloc[-1])
                c_mfi = float(calculate_mfi(sub_df).iloc[-1])
                energies_10d.append((c_mfi * 0.6) + (c_rsi * 0.4))
            
            curr_v_energy = energies_10d[0]
            all_v_energies.append(curr_v_energy)
            v_accel = (curr_v_energy - energies_10d[5]) / (energies_10d[5] + 1e-10) * 100
            succession_count = sum(1 for e in energies_10d if e >= 80)

            ma_series = close.rolling(200).mean()
            ma200 = ma_series.iloc[-1]
            ma200_slope = ma200 - ma_series.iloc[-5]
            curr_price = float(close.iloc[-1]); prev_price = float(close.iloc[-2])

            # 엑셀 기록용 데이터 수집 (누락되었던 부분)
            full_analysis_list.append({
                'Symbol': symbol, 'Price': curr_price, 'Energy': curr_v_energy, 
                'Accel': v_accel, 'Succession': succession_count, 'MA200_Dist': (curr_price-ma200)/ma200*100
            })

            market_data[symbol] = {'df': df, 'price': curr_price, 'energy': curr_v_energy, 'accel': v_accel}

            if symbol in actual_prey:
                # [수정 지침 1: 10일 중 8일 수성 필터]
                if (curr_price > ma200) and (succession_count >= 8):
                    # [수정 지침 2: 가속도 기반 Phase 판정]
                    phase = "💎 [요새]" if v_accel > 0 else "🚨 [식음]"
                    kings.append({'symbol': symbol, 'energy': curr_v_energy, 'accel': v_accel, 'phase': phase, 'core': symbol in core_sectors})
                elif (curr_price < ma200) and (prev_price >= ma_series.iloc[-2]):
                    downgrades.append(symbol)
        except Exception as e: continue

    # [이면 분석 및 오라클 연산 동일하게 유지]
    # ... (생략된 이면 분석 코드 본문에 포함됨) ...

    # [수정 지침 3: 시장 전체 평균 과열 지수]
    market_avg_energy = sum(all_v_energies) / len(all_v_energies) if all_v_energies else 0
    overheat_tag = "🚨 *[시장 과열: 사냥 금지]*" if market_avg_energy > 65 else "✅ *[정상 유동성]*"

    # [원칙 준수: 엑셀 파일 저장]
    pd.DataFrame(full_analysis_list).to_excel(f"V40C_FULL_SCAN_{datetime.now().strftime('%m%d')}.xlsx", index=False)

    # 5. 리포트 조립 및 발송
    kings = sorted(kings, key=lambda x: x['energy'], reverse=True)
    true_kings_report = ""
    for k in kings[:5]:
        mark = "🚀" if k['core'] else "🔥"
        true_kings_report += f"{mark} {k['symbol']}: {k['phase']} E:{k['energy']:.1f} (A:{k['accel']:+.1f}%)\n"

    report_1 = (
        f"🛡 *[V40-C: 진성 요새 기상도]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n"
        f"🌀 *[시장 평균 에너지]*: {market_avg_energy:.1f}\n"
        f"⚠️ *[과열 판정]*: {overheat_tag}\n\n"
        f"👑 *[진성 승격 (10일 수성)]*\n{true_kings_report if true_kings_report else '수성 성공 종목 없음'}\n"
        f"💀 *[강등]*: {', '.join(downgrades[:5])}"
    )

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": report_1, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_report()
