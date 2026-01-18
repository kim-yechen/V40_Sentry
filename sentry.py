import os, yfinance as yf, pandas as pd, requests, time
from datetime import datetime

# --- [환경 변수: 형님의 금고] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
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
    # 1. 대상 징집
    hunting_targets = ['VERO', 'IREN', 'ASTS', 'FCX', 'SCCO', 'PSLV', 'SI=F', 'COPX', 'MARA', 'CLSK']
    file_name = 'KIM_DIRECTOR_V40_ULTIMATE_REPORT.xlsx'
    
    if os.path.exists(file_name):
        try:
            xls = pd.ExcelFile(file_name)
            for sheet in xls.sheet_names:
                df_sheet = pd.read_excel(file_name, sheet_name=sheet)
                if 'Symbol' in df_sheet.columns:
                    hunting_targets.extend(df_sheet['Symbol'].dropna().unique().tolist())
            hunting_targets = list(set(hunting_targets))
        except: pass

    # 2. 분석 시작
    try: market_ref = yf.download("SPY", period="20d", progress=False)['Close'].pct_change().sum()
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
            if mdd >= -12 and energy >= 75 and alpha > 0: shield_a.append(res)
            elif -30 <= mdd < -12 and energy >= 70: spear_b.append(res)
            elif mdd < -35 or energy < 40: danger_c.append(res)
        except: continue

    # --- [3. 무전 발송 로직: 형님이 말씀하신 그 부분] ---
    header = f"🛡️ **[V40-C 파수꾼 보고]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"
    status_msg = f"📊 감시 종목: {len(hunting_targets)}개\n"
    found_any = False
    report_body = ""

    if shield_a:
        found_any = True
        for t in sorted(shield_a, key=lambda x: x['Energy'], reverse=True)[:3]:
            report_body += f"\n🚨 *[A: 방패 입고]*\n🎯 {t['Symbol']} (E:{t['Energy']:.1f} / A:{t['Alpha']:.2%})\n"

    if spear_b:
        found_any = True
        for t in sorted(spear_b, key=lambda x: x['Energy'], reverse=True)[:3]:
            report_body += f"\n⚔️ *[B: 창의 탄생]*\n🎯 {t['Symbol']} (E:{t['Energy']:.1f})\n"

    if not found_any:
        report_body = "\n✅ **현재 진성 승격 종목 없음**\n시장 관망을 유지하십시오."

    if danger_c:
        report_body += f"\n\n💀 *[⚠️ 리밸런싱]*: {', '.join([d['Symbol'] for d in danger_c[:5]])}"

    send_telegram(header + status_msg + report_body)

if __name__ == "__main__":
    get_v40_tactical_report()
