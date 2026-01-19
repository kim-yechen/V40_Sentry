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

def run_v40_quantum_sentry():
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: return
    target_file = files[0]
    special_watch = ['SLV', 'SCCO', 'FCX']

    try:
        xls = pd.ExcelFile(target_file)
        df_fortress = pd.read_excel(xls, sheet_name=1) 
        df_new_human = pd.read_excel(xls, sheet_name=2) 
        
        all_syms = list(set(list(df_fortress['Symbol'].dropna()) + list(df_new_human['Symbol'].dropna()) + special_watch))
        # 3개월 타임라인 분석을 위해 데이터를 200일치 넉넉히 가져옵니다.
        raw = yf.download(all_syms, period="200d", group_by='ticker', progress=False, threads=True)
        
        report = f"🛡️ **[V40-C 퀀텀 압착 지령]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"

        # --- [1층: 요새 긴급상황] ---
        # (생략: 위와 동일한 로직으로 마지노선 5% 이내 종목 보고)

        # --- [2, 3층: 퀀텀 압착 엔진 가동] ---
        tactical_pool = []
        for sym in df_new_human['Symbol'].dropna().unique():
            try:
                data = raw[sym]
                if len(data) < 130: continue
                
                close = data['Close']
                vol = data['Volume']
                returns = close.pct_change()

                # [V40 핵심 수식 주입]
                # 1. V-Energy (거래량 에너지 강도)
                v_energy = (vol.pct_change().rolling(10).std() * returns.rolling(10).std() * 10000).fillna(0)
                # 2. EDI (압착 지수: 에너지가 주가 변동성보다 얼마나 큰가)
                price_vol = returns.rolling(120).std()
                edi = v_energy.rolling(120).mean() / (price_vol + 1e-9)
                # 3. 위상차 (Corr: 가격과 에너지의 역행 여부)
                corr = close.rolling(20).corr(v_energy)

                curr_price = float(close.iloc[-1])
                curr_edi = edi.iloc[-1]
                curr_corr = corr.iloc[-1]
                
                # 타점 분석: 바닥권 확인
                support = data['Low'].tail(60).min()
                atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
                target = curr_price + (atr * 3.5) # 3개월 목표이므로 더 높게 설정

                # [필터 조건]: 
                # 1. EDI가 400 이상 (압착 진행 중)
                # 2. 현재가가 바닥에서 너무 멀어지지 않았을 것 (미발발 상태)
                if curr_edi > 400 and curr_price <= (support + (atr * 2.0)):
                    tactical_pool.append({
                        'sym': sym, 'curr': curr_price, 'target': target,
                        'edi': curr_edi, 'corr': curr_corr,
                        'upside': ((target / curr_price) - 1) * 100
                    })
            except: continue

        # 압착 강도(EDI)가 높은 순으로 TOP 5 선정 (발사 직전 에너지가 큰 놈들)
        elite_5 = sorted(tactical_pool, key=lambda x: x['edi'], reverse=True)[:5]

        if elite_5:
            report += "\n🚀 **[3개월 내 폭발 예상 TOP 5]**\n"
            report += "`종목   | 현재가 | 압착강도 | 목표가`\n"
            for t in elite_5:
                # 에너지가 응축되었음을 표시하는 아이콘
                report += f"🔋 `{t['sym']:<6} | {t['curr']:>6.2f} | {int(t['edi']):>6} | {t['target']:>6.2f}`\n"
        else:
            report += "\n⚪ 현재 에너지가 응축된 종목이 발견되지 않았습니다.\n"

        # [Full Process Compliance]
        pd.DataFrame(tactical_pool).to_excel("V40_QUANTUM_REPORT.xlsx", index=False)
        send_telegram(report)

    except Exception as e:
        send_telegram(f"⚠️ 에러: {str(e)}")

if __name__ == "__main__":
    run_v40_quantum_sentry()
