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

def calculate_mfi(df, period=14):
    """MFI(Money Flow Index): 거래량이 실린 진짜 에너지를 측정"""
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    rmf = tp * df['Volume']
    up_mf = pd.Series(0.0, index=df.index)
    dn_mf = pd.Series(0.0, index=df.index)
    
    up_mf[tp > tp.shift(1)] = rmf[tp > tp.shift(1)]
    dn_mf[tp < tp.shift(1)] = rmf[tp < tp.shift(1)]
    
    m_r = up_mf.rolling(window=period).sum() / dn_mf.rolling(window=period).sum()
    return 100 - (100 / (1 + m_r))

def calculate_atr(df, period=14):
    """ATR(Average True Range): 채찍의 파괴력(진폭)을 측정"""
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
            df = yf.download(symbol, period="250d", interval="1d", progress=False)
            if len(df) < 200: continue
            
            # 지표 계산
            c_today = df['Close'].iloc[-1]
            c_yesterday = df['Close'].iloc[-2]
            rsi = calculate_rsi(df['Close']).iloc[-1]
            mfi = calculate_mfi(df).iloc[-1]
            atr = calculate_atr(df).iloc[-1]
            atr_ratio = (atr / c_today) * 100 # 가격 대비 변동폭(%)
            
            # 데이터 저장
            market_data[symbol] = {
                'rsi': rsi, 'mfi': mfi, 'atr_p': atr_ratio,
                'change': (c_today - c_yesterday) / c_yesterday
            }

            # 기존 신분/요새 로직 (유지)
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            is_human_today = c_today > ma200
            is_human_yesterday = c_yesterday > df['Close'].rolling(200).mean().iloc[-2]

            if is_human_today != is_human_yesterday:
                status = "👑 [승격]" if is_human_today else "💀 [강등]"
                alerts += f"- {symbol}: {status}!\n"; found_alert = True
            if is_human_today:
                if 30 <= rsi <= 55:
                    hits += f"- {symbol}: RSI {rsi:.1f} ✅\n"; found_hit = True
                else:
                    tracking += f"- {symbol}: RSI {rsi:.1f}\n"
        except: continue

    # 3. [WFC 오라클 3.0: 3중 연동 붕괴 로직]
    rate_trend = market_data.get('^IRX', {}).get('change', 0)
    silver = market_data.get('SI=F', {'rsi':0, 'mfi':0, 'atr_p':0})
    
    oracle_log = ""
    # 붕괴 트리거: RSI 60초과(온도) AND MFI 60초과(무게)
    if silver['rsi'] > 60 and silver['mfi'] > 60:
        if rate_trend > 0:
            oracle_log = "⚡ *붕괴:* [악성 인플레이션] 확정\n"
            oracle_log += f"└ 🔍 근거: RSI({silver['rsi']:.1f}) & MFI({silver['mfi']:.1f}) 동반 과열\n"
            oracle_log += f"└ 🌊 파급력: ATR {silver['atr_p']:.1f}% (전파 중)\n"
            oracle_log += "└ ❌ 삭제: '금리 인하' 및 '기술주 반등' 시나리오\n"
        else:
            oracle_log = "🌀 *유동성 중첩:* [실체 있는 상승] 관측\n"
            oracle_log += f"└ 🔍 근거: 금리 하락 중 거래량 수반(MFI {silver['mfi']:.1f}) 원자재 폭주\n"
            oracle_log += "└ ✅ 유지: '돈의 힘' 시나리오 강화\n"
    
    # 가짜 광기 체크: 가격(RSI)만 오르고 거래량(MFI)은 죽었을 때
    elif silver['rsi'] > 60 and silver['mfi'] <= 50:
        oracle_log = "⚠️ *가짜 붕괴 경보:* [허수 과열] 포착\n"
        oracle_log += f"└ 🔍 근거: RSI({silver['rsi']:.1f})는 높으나 자금 유입(MFI) 미비\n"
        oracle_log += "└ 💡 판단: 세력의 설거지 혹은 단순 노이즈 (시나리오 삭제 보류)\n"
    
    else:
        oracle_log = "✅ 특이 붕괴 없음 (인과율 안정적)\n"
    
    oracle_section += oracle_log

    # 4. 보고서 발송
    if not found_alert: alerts += "특이사항 없음\n"
    if not found_hit: hits += "현재 요새 구간 종목 없음\n"
    final_msg = f"🛡 *[V40 전략 리포트]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n" + alerts + hits + tracking + oracle_section
    
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_report()
