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
    # 4000자 단위 분할 발송 (안전장치)
    for i in range(0, len(text), 4000):
        requests.post(url, data={"chat_id": CHAT_ID, "text": text[i:i+4000], "parse_mode": "Markdown"}, timeout=20)

def run_v40_sniping():
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: return
    target_file = files[0]

    special_watch = ['SLV', 'SCCO', 'FCX']

    try:
        xls = pd.ExcelFile(target_file)
        df_acc = pd.read_excel(xls, sheet_name=1)    # 시트2: 목돈
        df_human = pd.read_excel(xls, sheet_name=2)  # 시트3: 신인류
        
        all_syms = list(set(list(df_acc['Symbol'].dropna()) + list(df_human['Symbol'].dropna()) + special_watch))

        # 일괄 다운로드
        raw = yf.download(all_syms, period="100d", group_by='ticker', progress=False, threads=True)
        
        report = f"🛡️ **[V40-C 진성 요새 선별 지령]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"
        
        # 1. 시트2 & 특수종목 (위험 상황만 무전)
        emergency = ""
        for sym in list(set(list(df_acc['Symbol'].dropna()) + special_watch)):
            try:
                data = raw[sym]
                curr = float(data['Close'].iloc[-1])
                low_60 = data['Low'].tail(60).min()
                if curr <= low_60 * 1.05:
                    emergency += f"⚠️ {sym}: $ {round(curr, 2)} (바닥권 근접)\n"
            except: continue
        if emergency: report += "\n🔥 **[긴급 수비]**\n" + emergency

        # 2. 시트3 (현재 사도 되는 놈들만 선별)
        report += "\n🎯 **[단타/매집 사격 개시]**\n"
        report += "`종목   | 현재가 | 매수범위 | 목표가`\n"

        target_count = 0
        results = []
        for sym in df_human['Symbol'].dropna().unique():
            try:
                data = raw[sym]
                if data.empty: continue
                curr = float(data['Close'].iloc[-1])
                atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
                support = data['Low'].tail(60).min()
                
                core_max = support + (atr * 2.0)
                target = curr + (atr * 2.5)
                
                # [선별] 매수 범위 안에 들어온 놈들만 무전 보냄
                if support <= curr <= core_max:
                    report += f"💎 `{sym:<6} | {curr:>6.2f} | ~{core_max:>5.1f} | {target:>6.2f}`\n"
                    target_count += 1
                
                results.append({"Sym": sym, "Price": curr, "Target": target})
            except: continue

        if target_count == 0:
            report += "⚪ 현재 매수 범위에 들어온 종목이 없습니다.\n"

        # 파일 저장은 전체 다 하고, 무전은 선별된 놈들만!
        pd.DataFrame(results).to_excel("V40_DAILY_TACTICAL.xlsx", index=False)
        send_telegram(report)

    except Exception as e:
        send_telegram(f"⚠️ 에러: {str(e)}")

if __name__ == "__main__":
    run_v40_sniping()
