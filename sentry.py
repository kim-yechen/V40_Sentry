import os, yfinance as yf, pandas as pd, requests, numpy as np
from datetime import datetime

# --- [환경 변수] ---
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
    try:
        curr_price = float(df['Close'].iloc[-1])
        # ATR 계산으로 목표가/손절가 산출
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]

        target_price = curr_price + (atr * 2)
        stop_loss = curr_price - (atr * 1.5)
        expected_profit = ((target_price / curr_price) - 1) * 100
        return round(curr_price, 2), round(target_price, 2), round(stop_loss, 2), round(expected_profit, 1)
    except: return 0, 0, 0, 0

def get_v40_quantum_sentry():
    file_name = 'KIM_DIRECTOR_V40_ULTIMATE_REPORT.xlsx' 
    if not os.path.exists(file_name):
        print(f"❌ {file_name} 파일 없음")
        return

    try:
        # 형님 엑셀 시트 로드 - 컬럼명 오인식 방지 위해 index_col 미사용
        df_spear = pd.read_excel(file_name, sheet_name='Spear_B_Active')
        # 실제 존재하는 컬럼인 'Symbol'만 추출
        hunting_targets = df_spear['Symbol'].dropna().unique().tolist()
        print(f"📡 {len(hunting_targets)}개 종목 추적 시작...")
    except Exception as e:
        print(f"❌ 시트 로드 실패: {e}")
        return

    market_df = yf.download("SPY", period="30d", progress=False, auto_adjust=True)['Close']
    exploding_spear = []

    # 분석 시작
    for symbol in hunting_targets:
        try:
            df = yf.download(symbol, period="60d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 20: continue
            
            # 알파 및 거래량 확인
            stock_ret = df['Close'].tail(5).pct_change().sum()
            market_ret = market_df.tail(5).pct_change().sum()
            vol_ok = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]

            # 쏠 놈만 골라내기 (알파 > 0 & 거래량 확증)
            if (stock_ret - market_ret) > 0.02 and vol_ok:
                curr, target, stop, profit = get_target_prices(df)
                exploding_spear.append({
                    'Symbol': symbol, 'Price': curr, 'Target': target, 'Stop': stop, 'Profit': profit
                })
        except: continue

    # 텔레그램 발송 로직
    header = f"🚨 **[V40-Tactical 실전 무전]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"
    body = ""

    if exploding_spear:
        # 예상 수익률 높은 순으로 정렬
        exploding_spear = sorted(exploding_spear, key=lambda x: x['Profit'], reverse=True)
        body += "🔥 **[지금 사격: 에너지 분출 종목]**\n"
        for t in exploding_spear[:5]: # 상위 5개만 보고
            body += f"\n📍 **{t['Symbol']}**\n   - 진입: ${t['Price']} / **목표: ${t['Target']} (+{t['Profit']}%)**\n   - 손절: ${t['Stop']}\n"
    else:
        body = "\n✅ 현재 사격 조건(알파/거래량) 충족 종목 없음. 매복 유지하십시오."

    send_telegram(header + body)

if __name__ == "__main__":
    get_v40_quantum_sentry()
