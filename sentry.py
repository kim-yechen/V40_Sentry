import os
import glob
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime

# --- [V40 원칙 준수] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for i in range(0, len(text), 4000):
        requests.post(url, data={"chat_id": CHAT_ID, "text": text[i:i+4000], "parse_mode": "Markdown"}, timeout=20)

def run_v40_final_layered_sentry():
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: return
    target_file = files[0]
    special_watch = ['SLV', 'SCCO', 'FCX']

    try:
        xls = pd.ExcelFile(target_file)
        df_fortress = pd.read_excel(xls, sheet_name=1) 
        df_new_human = pd.read_excel(xls, sheet_name=2) 
        
        all_syms = list(set(list(df_fortress['Symbol'].dropna()) + list(df_new_human['Symbol'].dropna()) + special_watch))
        raw = yf.download(all_syms, period="200d", group_by='ticker', progress=False, threads=True)
        
        report = f"🛡️ **[V40-C 정예 복합 지령]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"

        # --- [1층: 요새 (이상 무 요약 기능 추가)] ---
        emergency = ""
        for sym in list(set(list(df_fortress['Symbol'].dropna()) + special_watch)):
            data = raw[sym]
            curr = float(data['Close'].iloc[-1])
            low_60 = data['Low'].tail(60).min()
            dist = (curr / low_60 - 1) * 100
            if dist <= 5.0:
                emergency += f"🚨 {sym}: $ {curr:.2f} ({dist:.1f}% 남음)\n"
        
        if emergency: report += "\n🏰 **[1층: 요새 긴급대응]**\n" + emergency
        else: report += "\n🏰 **[1층: 요새]** 전선 이상 무\n"

        # --- [2, 3층 통합 분석 엔진] ---
        human_pool = []
        tactical_pool = []
        
        for sym in df_new_human['Symbol'].dropna().unique():
            try:
                data = raw[sym]
                if len(data) < 130: continue
                close, vol = data['Close'], data['Volume']
                returns = close.pct_change()
                curr_price = float(close.iloc[-1])

                # 퀀텀 수식 (EDI)
                v_energy = (vol.pct_change().rolling(10).std() * returns.rolling(10).std() * 10000).fillna(0)
                edi = (v_energy.rolling(120).mean() / (returns.rolling(120).std() + 1e-9)).iloc[-1]
                
                # 타점 및 목표가
                support = data['Low'].tail(60).min()
                atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
                core_max = support + (atr * 2.0)
                target = curr_price + (atr * 3.5)
                
                # 거래대금 필터 (바이오주 갇힘 방지: 하루 100만불 이상으로 강화)
                if (vol.iloc[-1] * curr_price) < 1000000: continue

                # [2층 신인류 Pool]: 매집가 범위 안 + EDI 300 이상
                if support <= curr_price <= core_max and edi > 300:
                    human_pool.append({'sym': sym, 'curr': curr_price, 'core': core_max, 'edi': edi})

                # [3층 단타 Pool]: EDI 450 이상 폭발 대기
                if edi > 450:
                    tactical_pool.append({'sym': sym, 'curr': curr_price, 'target': target, 'edi': edi, 'upside': ((target/curr_price)-1)*100})
            except: continue

        # --- [2층 출력: EDI가 높은 정예 5선] ---
        if human_pool:
            report += "\n🧬 **[2층: 신인류 정예 매집 5선]**\n"
            for h in sorted(human_pool, key=lambda x: x['edi'], reverse=True)[:5]:
                report += f"💎 {h['sym']}: $ {h['curr']:.2f} (적정가 ~{h['core']:.1f} | 🔋{int(h['edi'])})\n"

        # --- [3층 출력: 퀀텀 TOP 5] ---
        if tactical_pool:
            report += "\n🚀 **[3층: 퀀텀 압착 TOP 5]**\n"
            for t in sorted(tactical_pool, key=lambda x: x['edi'], reverse=True)[:5]:
                report += f"🔋 `{t['sym']:<6} | {t['curr']:>6.2f} | 목표 {t['target']:>6.2f} (+{t['upside']:.1f}%)`\n"

        # [Full Process Compliance]
        pd.DataFrame(human_pool + tactical_pool).to_excel("V40_FINAL_TACTICAL.xlsx", index=False)
        send_telegram(report)

    except Exception as e:
        send_telegram(f"⚠️ 에러: {str(e)}")

if __name__ == "__main__":
    run_v40_final_layered_sentry()
