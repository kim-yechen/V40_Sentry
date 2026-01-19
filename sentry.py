import os
import glob
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime

# --- [환경 변수] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ [Secrets Error] 토큰/ID 없음"); return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # 텔레그램 글자수 제한(4000자) 대응을 위한 분할 전송
    if len(text) > 4000:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            requests.post(url, data={"chat_id": CHAT_ID, "text": chunk, "parse_mode": "Markdown"}, timeout=15)
    else:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    print("✅ [SUCCESS] 무전 발송 완료")

def run_v40_sentry_final():
    print(f"🚀 [START] V40-C 가동")
    
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: return
    target_file = files[0]

    special_watch = ['SLV', 'SCCO', 'FCX']

    try:
        xls = pd.ExcelFile(target_file)
        # 시트별 데이터 로드
        df_acc = pd.read_excel(xls, sheet_name=1)
        df_human = pd.read_excel(xls, sheet_name=2)
        
        s2_syms = list(df_acc['Symbol'].dropna().unique())
        s3_syms = list(df_human['Symbol'].dropna().unique())
        all_syms = list(set(s2_syms + s3_syms + special_watch))

        # 데이터 일괄 다운로드
        raw = yf.download(all_syms, period="100d", group_by='ticker', progress=False, threads=True)
        
        header = f"🛡️ **[V40-C 진성 요새 기상도]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"
        
        # 1. 시트2 & 특별종목 (긴급 상황만 추출)
        emergency_body = "🚨 **[긴급: 마지노선 근접]**\n"
        has_emergency = False
        results = []

        for sym in list(set(s2_syms + special_watch)):
            try:
                data = raw[sym]
                if data.empty: continue
                curr = float(data['Close'].iloc[-1])
                low_60 = data['Low'].tail(60).min()
                if curr <= low_60 * 1.05:
                    emergency_body += f"- {sym}: $ {round(curr, 2)} (바닥: {round(low_60, 2)})\n"
                    has_emergency = True
                results.append({"Sym": sym, "Price": curr, "Type": "Fortress"})
            except: continue
        
        # 2. 신인류 & 단타 (매집 기회 위주로 압축)
        human_body = "\n🧬 **[신인류: 핵심 전장]**\n"
        for sym in s3_syms:
            try:
                data = raw[sym]
                if data.empty: continue
                curr = float(data['Close'].iloc[-1])
                atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
                support = data['Low'].tail(60).min()
                
                core_max = support + (atr * 2.0)
                target = curr + (atr * 2.5)
                
                if support <= curr <= core_max:
                    human_body += f"💎 [기회] {sym}: $ {round(curr, 2)}\n"
                
                # 단타는 보고서가 너무 길어지면 빼고 엑셀에만 저장 (원칙 준수)
                results.append({"Sym": sym, "Price": curr, "Target": target, "Type": "NewHuman"})
            except: continue

        # 최종 보고서 조합
        full_report = header + (emergency_body if has_emergency else "✅ 시트2: 특이사항 없음\n") + human_body

        # 엑셀 저장 (Full Process Compliance)
        pd.DataFrame(results).to_excel("V40_DAILY_TACTICAL.xlsx", index=False)
        print("✅ [FILE] 저장 완료")
        
        # 무전 발송
        send_telegram(full_report)

    except Exception as e:
        send_telegram(f"⚠️ 에러 발생: {str(e)}")

if __name__ == "__main__":
    run_v40_sentry_final()
