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

def run_v40_layered_sentry():
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: return
    target_file = files[0]
    special_watch = ['SLV', 'SCCO', 'FCX']

    try:
        xls = pd.ExcelFile(target_file)
        df_fortress = pd.read_excel(xls, sheet_name=1) # 시트2
        df_new_human = pd.read_excel(xls, sheet_name=2) # 시트3
        
        all_syms = list(set(list(df_fortress['Symbol'].dropna()) + list(df_new_human['Symbol'].dropna()) + special_watch))
        raw = yf.download(all_syms, period="100d", group_by='ticker', progress=False, threads=True)
        
        report = f"🛡️ **[V40-C 3층 레이어 보고]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"

        # --- [1단계: 목돈 요새 - 생존 확인] ---
        emergency = ""
        for sym in list(set(list(df_fortress['Symbol'].dropna()) + special_watch)):
            data = raw[sym]
            curr = float(data['Close'].iloc[-1])
            low_60 = data['Low'].tail(60).min()
            if curr <= low_60 * 1.05: # 마지노선 5% 근접 시
                emergency += f"⚠️ {sym}: 현재 $ {round(curr, 2)} (마지노선 {round(low_60, 2)})\n"
        if emergency: report += "\n🏰 **[1층: 요새 긴급상황]**\n" + emergency
        else: report += "\n🏰 **[1층: 요새]** 이상 무 (생존 확인 완료)\n"

        # --- [2단계: 신인류 - 매집 전장] ---
        # 여기는 '더 담아도 되는지'가 핵심
        human_report = ""
        for sym in df_new_human['Symbol'].dropna().unique():
            data = raw[sym]
            curr = float(data['Close'].iloc[-1])
            atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
            support = data['Low'].tail(60).min()
            core_max = support + (atr * 2.0)
            
            if support <= curr <= core_max:
                human_report += f"💎 {sym}: $ {round(curr, 2)} (매집권 ~{round(core_max, 1)})\n"
        
        if human_report: report += "\n🧬 **[2층: 신인류 매집기회]**\n" + human_report

        # --- [3단계: 단타 Tactical - 사격 지점] ---
        # 여기는 '얼마에 팔지'가 핵심 (허수 방지: 거래량 20% 이상 증가 종목만 선별 가능하나 일단 가격 위주)
        tactical_report = ""
        for sym in df_new_human['Symbol'].dropna().unique():
            data = raw[sym]
            curr = float(data['Close'].iloc[-1])
            atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
            target = curr + (atr * 2.5) # 목표가 설정
            
            # 단타는 현재가가 매수권에 있으면서 에너지가 있는 놈들만
            support = data['Low'].tail(60).min()
            if support <= curr <= (support + (atr * 1.5)): # 좀 더 타이트하게
                tactical_report += f"🎯 {sym}: 목표가 **$ {round(target, 2)}** (익절 준비)\n"

        if tactical_report: report += "\n🎯 **[3층: 단타 사격 지령]**\n" + tactical_report

        send_telegram(report)

    except Exception as e:
        send_telegram(f"⚠️ 에러: {str(e)}")

if __name__ == "__main__":
    run_v40_layered_sentry()
