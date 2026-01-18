import os, yfinance as yf, pandas as pd, requests, time
from datetime import datetime

# --- [1. 환경 변수: 이미 완벽함] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        # 마크다운 문법 오류 방지를 위해 최소한의 파싱만 사용
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def calculate_indicators(df):
    try:
        delta = df['Close'].diff()
        up = delta.clip(lower=0); down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rsi = 100 - (100 / (1 + (ema_up / (ema_down + 1e-10))))
        
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        rmf = tp * df['Volume']
        up_mf = pd.Series(0.0, index=df.index); dn_mf = pd.Series(0.0, index=df.index)
        up_mf[tp > tp.shift(1)] = rmf[tp > tp.shift(1)]
        dn_mf[tp < tp.shift(1)] = rmf[tp < tp.shift(1)]
        mfi = 100 - (100 / (1 + (up_mf.rolling(14).sum() / (dn_mf.rolling(14).sum() + 1e-10))))
        return rsi.iloc[-1], mfi.iloc[-1]
    except: return 50.0, 50.0

def get_v40_tactical_report():
    print("📡 [V40-C] 실시간 파수꾼 기동...")
    
    # 1. 엑셀 연동 (형님이 올린 파일에서 종목 추출)
    hunting_targets = ['VERO', 'IREN', 'ASTS', 'FCX', 'SCCO'] # 기본 감시망
    file_name = 'KIM_DIRECTOR_V40_ULTIMATE_REPORT.xlsx'
    
    if os.path.exists(file_name):
        try:
            # 모든 시트를 뒤져서 'Symbol' 컬럼의 종목을 다 가져옴
            xls = pd.ExcelFile(file_name)
            for sheet in xls.sheet_names:
                df_sheet = pd.read_excel(file_name, sheet_name=sheet)
                if 'Symbol' in df_sheet.columns:
                    hunting_targets.extend(df_sheet['Symbol'].dropna().unique().tolist())
            hunting_targets = list(set(hunting_targets)) # 중복 제거
            print(f"✅ 엑셀 데이터 연동 성공: {len(hunting_targets)}개 종목 감시 시작")
        except Exception as e:
            print(f"⚠️ 엑셀 로드 실패 (기본 종목으로 진행): {e}")

    # 시장 기준점 (SPY)
    try:
        market_ref = yf.download("SPY", period="20d", progress=False)['Close'].pct_change().sum()
    except: market_ref = 0

    shield_a, spear_b, danger_c = [], [], []

    for symbol in hunting_targets:
        try:
            df = yf.download(symbol, period="250d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 200: continue
            
            curr_price = float(df['Close'].iloc[-1])
            peak_250 = df['Close'].max()
            mdd = ((curr_price - peak_250) / peak_250) * 100
            rsi, mfi = calculate_indicators(df)
            energy = (mfi * 0.6) + (rsi * 0.4)
            alpha = (df['Close'].tail(5).pct_change().sum()) - market_ref
            
            res = {'Symbol': symbol, 'MDD': mdd, 'Energy': energy, 'Alpha': alpha}

            # --- [V40-C 전술 판정] ---
            if mdd >= -12 and energy >= 75 and alpha > 0:
                shield_a.append(res)
            elif -30 <= mdd < -12 and energy >= 70:
                spear_b.append(res)
            elif mdd < -35 or energy < 40:
                danger_c.append(res)
        except: continue

    # --- [무전 발송] ---
    if shield_a:
        for t in sorted(shield_a, key=lambda x: x['Energy'], reverse=True)[:3]:
            send_telegram(f"🚨 *[V40-A: 방패 입고]*\n🎯 종목: {t['Symbol']}\n🛡️ 상태: [기관급 수급] MDD {t['MDD']:.1f}%\n💰 한도: *1,050만 원*\n💬 지침: 형님, 본진 투입 적기입니다.")

    if spear_b:
        for t in sorted(spear_b, key=lambda x: x['Energy'], reverse=True)[:3]:
            send_telegram(f"⚔️ *[V40-B: 창의 탄생]*\n🎯 종목: {t['Symbol']}\n🔥 성질: [신인류] 에너지 {t['Energy']:.1f}\n💰 한도: *200만 원*\n💬 지침: 잉여소득으로 개수 늘리십시오.")

    if danger_c:
        msg = "💀 *[V40-⚠️: 리밸런싱 경고]*\n❌ 대상: " + ", ".join([d['Symbol'] for d in danger_c[:5]]) + "\n💬 지침: 형님, 이놈들 바람 빠졌습니다. 회군하십시오."
        send_telegram(msg)

if __name__ == "__main__":
    get_v40_tactical_report()
