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
    rs = ema_up / (ema_down + 1e-10) # 0 나누기 방지
    return 100 - (100 / (1 + rs))

def calculate_mfi(df, period=14):
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    rmf = tp * df['Volume']
    up_mf = pd.Series(0.0, index=df.index)
    dn_mf = pd.Series(0.0, index=df.index)
    up_mf[tp > tp.shift(1)] = rmf[tp > tp.shift(1)]
    dn_mf[tp < tp.shift(1)] = rmf[tp < tp.shift(1)]
    
    pos_sum = up_mf.rolling(window=period).sum()
    neg_sum = dn_mf.rolling(window=period).sum()
    m_r = pos_sum / (neg_sum + 1e-10) # Negative Check: 0 나누기 방지
    return 100 - (100 / (1 + m_r))

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_cp = (df['High'] - df['Close'].shift(1)).abs()
    low_cp = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def get_v40_report():
    fixed_targets = ['ERO', 'FCX', 'SCCO', 'SI=F', 'HG=F', 'AAPL', 'NVDA', 'TSLA', '^IRX'] 
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
            # 깃허브 무료 환경을 위한 타임 슬립 (야후 차단 방지)
            time.sleep(0.5) 
            df = yf.download(symbol, period="250d", interval="1d", progress=False)
            
            # [Negative Check] 데이터가 너무 적거나 누락된 경우 스킵
            if df is None or len(df) < 200:
                print(f"Data missing for {symbol}")
                continue
            
            # 지표 계산 최적화
            close = df['Close']
            ma200 = close.rolling(200).mean()
            rsi = calculate_rsi(close).iloc[-1]
            mfi = calculate_mfi(df).iloc[-1]
            atr = calculate_atr(df).iloc[-1]
            c_today = close.iloc[-1]
            c_yesterday = close.iloc[-2]
            
            market_data[symbol] = {
                'rsi': rsi, 'mfi': mfi, 'atr_p': (atr / c_today) * 100,
                'change': (c_today - c_yesterday) / c_yesterday
            }

            # 신분 변동 로직
            is_human_today = c_today > ma200.iloc[-1]
            is_human_yesterday = c_yesterday > ma200.iloc[-2]

            if is_human_today != is_human_yesterday:
                status = "👑 [승격]" if is_human_today else "💀 [강등]"
                alerts += f f"- {symbol}: {status}!\n"; found_alert = True
            
            if is_human_today:
                if 30 <= rsi <= 55:
                    hits += f"- {symbol}: RSI {rsi:.1f} ✅\n"; found_hit = True
                else:
                    tracking += f"- {symbol}: RSI {rsi:.1f}\n"
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            continue

    # [오라클 분석] - 데이터 존재 여부 확인 후 실행
    if 'SI=F' in market_data and '^IRX' in market_data:
        rate_trend = market_data['^IRX']['change']
        silver = market_data['SI=F']
        
        if silver['rsi'] > 60 and silver['mfi'] > 60:
            if rate_trend > 0:
                oracle_section += "⚡ *붕괴:* [악성 인플레이션] 확정\n"
                oracle_section += f"└ 근거: RSI {silver['rsi']:.1f} / MFI {silver['mfi']:.1f} / ATR {silver['atr_p']:.1f}%\n"
            else:
                oracle_section += "🌀 *유동성 중첩:* [실체 있는 상승]\n"
                oracle_section += f"└ 근거: 금리 하락 중 대량 자금 유입\n"
        elif silver['rsi'] > 60 and silver['mfi'] <= 50:
            oracle_section += "⚠️ *가짜 붕괴 경보:* [허수 과열]\n"
            oracle_section += f"└ 근거: RSI {silver['rsi']:.1f} 대비 MFI {silver['mfi']:.1f} 저조\n"
        else:
            oracle_section += "✅ 특이 붕괴 없음\n"
    else:
        oracle_section += "❓ *분석 불가:* 핵심 지표(SI/IRX) 데이터 누락\n"

    # 최종 발송
    if not found_alert: alerts += "특이사항 없음\n"
    if not found_hit: hits += "현재 요새 구간 종목 없음\n"
    final_msg = f"🛡 *[V40 전략 리포트]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n" + alerts + hits + tracking + oracle_section
    
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_report()
