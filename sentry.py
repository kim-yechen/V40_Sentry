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
        df_fortress = pd.read_excel(xls, sheet_name=1) # 1층 (시트2)
        df_new_human = pd.read_excel(xls, sheet_name=2) # 2,3층 (시트3)
        
        all_syms = list(set(list(df_fortress['Symbol'].dropna()) + list(df_new_human['Symbol'].dropna()) + special_watch))
        # 퀀텀 분석을 위해 200일 데이터 확보
        raw = yf.download(all_syms, period="200d", group_by='ticker', progress=False, threads=True)
        
        report = f"🛡️ **[V40-C 정예 복합 지령]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"

        # --- [1층: 요새 (무소식이 희소식)] ---
        emergency = ""
        for sym in list(set(list(df_fortress['Symbol'].dropna()) + special_watch)):
            data = raw[sym]
            curr = float(data['Close'].iloc[-1])
            low_60 = data['Low'].tail(60).min()
            dist = (curr / low_60 - 1) * 100
            if dist <= 5.0: # 마지노선 5% 이내만 긴급 보고
                emergency += f"🚨 {sym}: $ {curr:.2f} (마지노선 {dist:.1f}% 남음)\n"
        
        if emergency: report += "\n🏰 **[1층: 요새 긴급대응]**\n" + emergency
        else: report += "\n🏰 **[1층: 요새]** 모든 전선 이상 무 (평온)\n"

        # --- [2, 3층 통합 분석 엔진] ---
        human_report = ""
        tactical_pool = []
        
        for sym in df_new_human['Symbol'].dropna().unique():
            try:
                data = raw[sym]
                if len(data) < 130: continue
                close = data['Close']
                vol = data['Volume']
                returns = close.pct_change()
                curr_price = float(close.iloc[-1])

                # 퀀텀 수식 (EDI 압착)
                v_energy = (vol.pct_change().rolling(10).std() * returns.rolling(10).std() * 10000).fillna(0)
                price_vol = returns.rolling(120).std()
                edi = v_energy.rolling(120).mean() / (price_vol + 1e-9)
                
                # 타점 및 목표가 산정
                support = data['Low'].tail(60).min()
                atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
                core_max = support + (atr * 2.0) # 매집 적정가 상한선
                target = curr_price + (atr * 3.5) # 통계적 목표가
                
                # 거래대금 필터 (하루 50만불 미만 잡주 제외)
                if (vol.iloc[-1] * curr_price) < 500000: continue

                # [2층 보고용]: 매집 구간에 있는 놈들
                if support <= curr_price <= core_max:
                    human_report += f"💎 {sym}: $ {curr_price:.2f} (적정가 ~{core_max:.1f})\n"

                # [3층 후보군]: EDI 400 이상 압착주
                if edi.iloc[-1] > 400:
                    tactical_pool.append({
                        'sym': sym, 'curr': curr_price, 'target': target,
                        'edi': edi.iloc[-1], 'upside': ((target/curr_price)-1)*100
                    })
            except: continue

        # --- [2층 무전 출력] ---
        if human_report:
            report += "\n🧬 **[2층: 신인류 매집 적정가]**\n" + "\n".join(human_report.split("\n")[:10]) # 너무 많으면 상위 10개만

        # --- [3층 무전 출력 (퀀텀 TOP 5)] ---
        elite_5 = sorted(tactical_pool, key=lambda x: x['edi'], reverse=True)[:5]
        if elite_5:
            report += "\n🚀 **[3층: 퀀텀 압착 TOP 5 (3개월)]**\n"
            report += "`종목   | 현재가 | 목표가(기대치)`\n"
            for t in elite_5:
                report += f"🔋 `{t['sym']:<6} | {t['curr']:>6.2f} | {t['target']:>6.2f} (+{t['upside']:.1f}%)`\n"

        # [Full Process] 저장 후 전송
        pd.DataFrame(tactical_pool).to_excel("V40_FINAL_TACTICAL.xlsx", index=False)
        send_telegram(report)

    except Exception as e:
        send_telegram(f"⚠️ 에러: {str(e)}")

if __name__ == "__main__":
    run_v40_final_layered_sentry()
