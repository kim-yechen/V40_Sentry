import os, yfinance as yf, pandas as pd, requests, numpy as np
from datetime import datetime

# --- [환경 변수: 형님의 금고] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: 
        print(text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_target_prices(df):
    """[신규 로직] 단타용 사격/퇴각 지점 계산"""
    try:
        curr_price = float(df['Close'].iloc[-1])
        high_20 = df['High'].rolling(20).max().iloc[-1]
        low_20 = df['Low'].rolling(20).min().iloc[-1]
        atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]

        # 1. 진입가(Buy): 전고점 돌파 확인 혹은 현재가
        # 2. 목표가(Target): 현재가 대비 +ATR의 2배 (단기 에너지 분출 한계선)
        # 3. 손절가(Stop): 현재가 대비 -ATR의 1.5배 (단타 생명선)
        target_price = curr_price + (atr * 2)
        stop_loss = curr_price - (atr * 1.5)
        expected_profit = ((target_price / curr_price) - 1) * 100
        
        return round(curr_price, 2), round(target_price, 2), round(stop_loss, 2), round(expected_profit, 1)
    except: return 0, 0, 0, 0

def check_squeeze(df, window=20):
    try:
        std = df['Close'].rolling(window=window).std()
        mean = df['Close'].rolling(window=window).mean()
        bb_width = (std * 4) / mean
        is_squeezing = bb_width.iloc[-1] < bb_width.rolling(window=window).mean().iloc[-1]
        return is_squeezing
    except: return False

def calculate_real_alpha(df, market_df):
    try:
        stock_ret = df['Close'].tail(5).pct_change().sum()
        market_ret = market_df.tail(5).pct_change().sum()
        vol_confirm = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]
        return (stock_ret - market_ret), vol_confirm
    except: return 0.0, False

def get_v40_quantum_sentry():
    # 형님, 파일명은 최신 업데이트된 리포트로 고정했습니다.
    file_name = 'KIM_DIRECTOR_V40_ULTIMATE_REPORT.xlsx' 
    if not os.path.exists(file_name):
        print(f"❌ {file_name} 파일이 없습니다.")
        return

    try:
        # Spear_B_Active 시트가 단타(B그룹)의 핵심입니다.
        v2_data = pd.read_excel(file_name, sheet_name='Spear_B_Active')
        target_info = v2_data.set_index('Symbol')[['Grade', 'Nature']].to_dict('index')
        hunting_targets = list(target_info.keys())
    except:
        print("❌ 시트 로드 실패. Spear_B_Active 시트를 확인하십시오.")
        return

    market_df = yf.download("SPY", period="30d", progress=False, auto_adjust=True)['Close']
    squeezing_gold, exploding_spear, danger_zone = [], [], []

    for symbol in hunting_targets:
        try:
            df = yf.download(symbol, period="100d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 30: continue
            
            curr_price, target, stop, profit = get_target_prices(df)
            alpha, vol_ok = calculate_real_alpha(df, market_df)
            is_squeezed = check_squeeze(df)
            
            res = {'Symbol': symbol, 'Price': curr_price, 'Target': target, 'Stop': stop, 'Profit': profit, 'Alpha': alpha}

            # B그룹(Spear)은 무조건 단타 기준 적용
            if alpha > 0 and vol_ok:
                exploding_spear.append(res)
            elif is_squeezed:
                squeezing_gold.append(res)
        except: continue

    # 4. 형님 전용 실전 무전
    header = f"🚨 **[V40-Tactical 단타 무전]**\n"
    report_body = ""

    if exploding_spear:
        report_body += f"\n🔥 **[지금 사격: 에너진 분출]**"
        for t in exploding_spear[:5]:
            report_body += (f"\n📍 **{t['Symbol']}**\n   - 사격가: ${t['Price']}\n   - 목표가: ${t['Target']} (**+{t['Profit']}%** 예상)\n   - 퇴각선: ${t['Stop']}")

    if squeezing_gold:
        report_body += f"\n\n💎 **[매복 중: 에너지 압착]**"
        for t in squeezing_gold[:3]:
            report_body += f"\n📍 {t['Symbol']} (준비금 확보 - 발발 대기)"

    if not report_body:
        report_body = "\n✅ 시장 에너지가 과열 상태입니다. 무지성 사격 금지."

    send_telegram(header + report_body)

if __name__ == "__main__":
    get_v40_quantum_sentry()
