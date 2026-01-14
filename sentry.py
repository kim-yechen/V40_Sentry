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

def calculate_atr(df, period=14):
    tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift(1)).abs(), (df['Low']-df['Close'].shift(1)).abs()], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def get_v40_report():
    # SLV와 BIL을 감시 대상에 공식 추가 (대체 경로용)
    fixed_targets = ['ERO', 'FCX', 'SCCO', 'SI=F', 'HG=F', 'AAPL', 'NVDA', 'TSLA', '^IRX', 'SLV', 'BIL'] 
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

    alerts = "⚠️ *[신분 변동 감지!]*\n"; hits = "\n🏟 *[오늘의 요새 (적정가 매수)]*\n"
    tracking = "\n🔍 *[신인류: 추적 및 관망]*\n"
    oracle_section = "\n🔮 *[V40 오라클: 3중 스위치 분석]*\n"
    
    found_alert = False; found_hit = False
    market_data = {}

    for symbol in targets:
        try:
            time.sleep(0.5)
            df = yf.download(symbol, period="250d", interval="1d", progress=False)
            if df is None or len(df) < 200: continue
            
            c_today = df['Close'].iloc[-1]; c_yesterday = df['Close'].iloc[-2]
            rsi = calculate_rsi(df['Close']).iloc[-1]
            mfi = calculate_mfi(df).iloc[-1]
            atr = calculate_atr(df).iloc[-1]
            
            market_data[symbol] = {
                'price': c_today, 'rsi': rsi, 'mfi': mfi, 
                'atr_p': (atr / c_today) * 100,
                'change': (c_today - c_yesterday) / c_yesterday
            }

            # 기존 신분/요새 로직
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            if (c_today > ma200) != (c_yesterday > df['Close'].rolling(200).mean().iloc[-2]):
                alerts += f"- {symbol}: {'👑 [승격]' if c_today > ma200 else '💀 [강등]'}!\n"; found_alert = True
            if c_today > ma200:
                if 30 <= rsi <= 55: hits += f"- {symbol}: RSI {rsi:.1f} ✅\n"; found_hit = True
                else: tracking += f"- {symbol}: RSI {rsi:.1f}\n"
        except: continue

    # --- [WFC 오라클 3.8: 대체 경로 및 보정 로직] ---
    # 1. 은(Silver) 데이터 확정
    silver_final = None
    if 'SI=F' in market_data:
        silver_final = market_data['SI=F']
        silver_final['source'] = "선물(SI=F)"
    elif 'SLV' in market_data:
        # SI=F 누락 시 형님의 1.02 보정값 적용
        silver_final = market_data['SLV'].copy()
        silver_final['rsi'] *= 1.02 # 보정값 적용
        silver_final['source'] = "ETF(SLV) * 1.02 보정"
        # Negative Check: 5% 괴리 셧다운 (이미 보정값이 2%이므로 극단적 상황 감지)
        if silver_final['rsi'] > 95: # RSI가 보정으로 인해 비정상적으로 높을 때 등
             silver_final['panic'] = True

    # 2. 금리(Yield) 데이터 확정
    rate_change = 0
    rate_source = "데이터 없음"
    if '^IRX' in market_data:
        rate_change = market_data['^IRX']['change']
        rate_source = "국채(^IRX)"
    elif 'BIL' in market_data:
        # BIL 가격 하락 = 금리 상승 (역산 -1)
        rate_change = market_data['BIL']['change'] * -1
        rate_source = "초단기채(BIL) 역산"

    # 3. 최종 오라클 판정
    if silver_final and rate_source != "데이터 없음":
        if silver_final.get('panic'):
            oracle_section += "🚨 *시스템 셧다운:* [뱅크런 전조] 관측\n"
            oracle_section += "└ 🔍 근거: 실물-종이 자산 괴리율 임계점 돌파\n"
        else:
            if silver_final['rsi'] > 60 and silver_final['mfi'] > 60:
                status = "⚡ *붕괴:* [악성 인플레이션]" if rate_change > 0 else "🌀 *유동성 중첩:* [실체 있는 상승]"
                oracle_section += f"{status}\n"
                oracle_section += f"└ 근거: {silver_final['source']} 기반 분석\n"
                oracle_section += f"└ 지표: RSI {silver_final['rsi']:.1f} / MFI {silver_final['mfi']:.1f}\n"
            elif silver_final['rsi'] > 60 and silver_final['mfi'] <= 50:
                oracle_section += "⚠️ *가짜 붕괴 경보:* [허수 과열]\n"
                oracle_section += f"└ 근거: {silver_final['source']} 과열 대비 자금유입 저조\n"
            else:
                oracle_section += "✅ 특이 붕괴 없음 (인과율 안정적)\n"
    else:
        oracle_section += "❓ *분석 불가:* SI/SLV 및 IRX/BIL 전체 데이터 누락\n"

    # 최종 보고서 발송
    if not found_alert: alerts += "특이사항 없음\n"
    if not found_hit: hits += "현재 요새 구간 종목 없음\n"
    final_msg = f"🛡 *[V40 전략 리포트]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n" + alerts + hits + tracking + oracle_section
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_report()
