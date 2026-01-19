import os, yfinance as yf, pandas as pd, requests, numpy as np
import glob
from datetime import datetime

# --- [환경 변수] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: 
        print(f"📡 [DEBUG]:\n{text}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_target_prices(df):
    try:
        curr_price = float(df['Close'].iloc[-1])
        # ATR(평균 변동폭) 기반 단타 타점 산출
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        atr = np.max(ranges, axis=1).rolling(14).mean().iloc[-1]

        target_price = curr_price + (atr * 2)
        stop_loss = curr_price - (atr * 1.5)
        expected_profit = ((target_price / curr_price) - 1) * 100
        return round(curr_price, 2), round(target_price, 2), round(stop_loss, 2), round(expected_profit, 1)
    except: return 0, 0, 0, 0

def run_sentry():
    # 1. 형님이 주신 파일명 패턴으로 강제 추적
    # 'V40_NEW_HUMAN_V2_UPGRADE'가 포함된 모든 엑셀 파일을 찾습니다.
    search_pattern = "*V40_NEW_HUMAN_V2_UPGRADE*.xlsx"
    found_files = glob.glob(search_pattern)
    
    if not found_files:
        print(f"❌ 파일을 못 찾았습니다. 리스트: {os.listdir('.')}")
        return
    
    target_file = found_files[0]
    print(f"✅ 형님 파일 포착: {target_file}")

    try:
        # 2. Spear_B_Active 시트 강제 로드
        df_spear = pd.read_excel(target_file, sheet_name='Spear_B_Active', engine='openpyxl')
        hunting_targets = df_spear['Symbol'].dropna().unique().tolist()
    except Exception as e:
        print(f"❌ 시트 로드 실패: {e}")
        return

    market_df = yf.download("SPY", period="30d", progress=False)['Close']
    exploding_spear = []

    print(f"📡 {len(hunting_targets)}개 타겟 분석 중...")

    for symbol in hunting_targets:
        try:
            df = yf.download(symbol, period="60d", progress=False)
            if df.empty or len(df) < 20: continue
            
            # 알파(시장대비 강도) 및 거래량 확인
            stock_ret = df['Close'].tail(5).pct_change().sum()
            market_ret = market_df.tail(5).pct_change().sum()
            vol_ok = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]

            # 사격 기준: 알파 우위 & 거래량 폭발
            if (stock_ret - market_ret) > 0.02 and vol_ok:
                curr, target, stop, profit = get_target_prices(df)
                exploding_spear.append({
                    'Symbol': symbol, 'Price': curr, 'Target': target, 'Stop': stop, 'Profit': profit
                })
        except: continue

    # 3. 텔레그램 무전 생성
    header = f"🚨 **[V40-Tactical 장 마감 무전]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"
    body = ""

    if exploding_spear:
        exploding_spear = sorted(exploding_spear, key=lambda x: x['Profit'], reverse=True)
        body += "🔥 **[내일 사격: 에너진 분출]**\n"
        for t in exploding_spear[:5]:
            body += f"\n📍 **{t['Symbol']}**\n   - 진입: ${t['Price']}\n   - **목표: ${t['Target']} (+{t['Profit']}%)**\n   - **손절: ${t['Stop']}**\n"
    else:
        body = "\n✅ 현재 사격 조건에 맞는 놈이 없습니다. 현금 보존하십시오."

    send_telegram(header + body)

if __name__ == "__main__":
    run_sentry()
