import os
import glob
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import sys
from datetime import datetime

# --- [환경 변수 확인] ---
# GitHub Actions에서 설정한 이름과 정확히 일치해야 합니다.
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ [ERR]: 텔레그램 토큰이나 CHAT_ID가 설정되지 않았습니다. (GitHub Secrets 확인 필요)")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        # 타임아웃을 늘리고 응답 결과를 출력해서 로그에서 확인 가능하게 함
        response = requests.post(url, data=payload, timeout=20)
        if response.status_code == 200:
            print("✅ 텔레그램 무전 발송 성공")
        else:
            print(f"❌ 텔레그램 발송 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 텔레그램 연결 오류: {e}")

def run_v40_final_sentry():
    search_pattern = "*V40_NEW_HUMAN_V2_UPGRADE*.xlsx"
    found_files = glob.glob(search_pattern)
    if not found_files:
        print("❌ [ERR]: 엑셀 파일을 찾을 수 없습니다."); return
    target_file = found_files[0]

    special_watch = ['SLV', 'SCCO', 'FCX']
    
    try:
        xls = pd.ExcelFile(target_file)
        df_acc = pd.read_excel(xls, sheet_name=1)    
        df_human = pd.read_excel(xls, sheet_name=2)  
        
        sheet2_symbols = list(df_acc['Symbol'].dropna().unique())
        sheet3_symbols = list(df_human['Symbol'].dropna().unique())
        all_symbols = list(set(sheet2_symbols + sheet3_symbols + special_watch))

        print(f"📡 {len(all_symbols)}개 종목 데이터 분석 중...")
        raw_data = yf.download(all_symbols, period="100d", group_by='ticker', progress=False, threads=True, timeout=30)

        report = f"🛡️ **[V40-C 진성 요새 기상도]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"
        results_to_save = []

        # --- [섹션 1: 시트2 & 특별종목(SLV/SCCO/FCX) 생존 확인] ---
        combined_watch = list(set(sheet2_symbols + special_watch))
        for sym in combined_watch:
            try:
                data = raw_data[sym] if len(all_symbols) > 1 else raw_data
                if data.empty: continue
                curr = float(data['Close'].iloc[-1])
                low_60 = data['Low'].tail(60).min()
                if curr <= low_60 * 1.05:
                    tag = "🚨 [긴급/미보유]" if sym in special_watch and sym not in sheet2_symbols else "⚠️ [시트2]"
                    report += f"{tag} {sym}: 마지노선($ {round(low_60, 2)}) 근접! 현재 $ {round(curr, 2)}\n"
                results_to_save.append({"Type": "Fortress", "Symbol": sym, "Price": curr})
            except: continue

        # --- [섹션 2: 신인류 & 단타 전략] ---
        report += "\n🧬 **[신인류/단타 현황]**\n"
        for sym in sheet3_symbols:
            try:
                data = raw_data[sym] if len(all_symbols) > 1 else raw_data
                if data.empty: continue
                curr = float(data['Close'].iloc[-1])
                atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
                support = data['Low'].tail(60).min()
                
                core_max = support + (atr * 2.0)
                target_price = curr + (atr * 2.5)
                
                if support <= curr <= core_max:
                    report += f"💎 [기회] {sym}: 매집 적정 ($ {round(curr, 2)})\n"
                
                report += f"🎯 [단타] {sym}: 목표 $ {round(target_price, 2)} (손절 $ {round(curr-(atr*1.2), 2)})\n"
                results_to_save.append({"Type": "Tactical", "Symbol": sym, "Price": curr, "Target": target_price})
            except: continue

        # --- [3. 원칙 준수: 저장 후 무전] ---
        # 데이터가 비어있어도 보고서는 나가야 하므로 체크
        if not results_to_save:
            report += "\n✅ 현재 특이사항 없습니다. 요새는 평온합니다."

        pd.DataFrame(results_to_save).to_excel("V40_DAILY_TACTICAL.xlsx", index=False)
        print("✅ [Complete] V40_DAILY_TACTICAL.xlsx 저장 완료")
        
        # 텔레그램 발송 전 로그 출력
        print("📡 텔레그램 무전 발송 시도...")
        send_telegram(report)

    except Exception as e:
        error_msg = f"⚠️ [수정 필요]: 형님, 분석 중 오류 발생. {e}"
        print(error_msg)
        send_telegram(error_msg)

if __name__ == "__main__":
    run_v40_final_sentry()
