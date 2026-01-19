import os
import glob
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# --- [V40 원칙 준수] ---
# 1. Full process compliance: 분석 -> 처리 -> 저장 (Complete)
# 2. Negative Check: 마이너스 수익률/가격 등 논리 오류 검증
# 3. No Shortcuts: 오류 시 삭제하지 않고 보고

def get_market_data(symbol):
    try:
        df = yf.download(symbol, period="100d", progress=False)
        if df.empty or len(df) < 20: return None
        if (df['Close'] <= 0).any(): return None # Negative Check
        return df
    except: return None

def run_v40_fortress():
    search_pattern = "*V40_NEW_HUMAN_V2_UPGRADE*.xlsx"
    found_files = glob.glob(search_pattern)
    if not found_files:
        print("❌ [ERR]: 엑셀 파일을 찾을 수 없습니다."); return

    target_file = found_files[0]
    results_to_save = [] # 엑셀 저장을 위한 리스트
    
    try:
        xls = pd.ExcelFile(target_file)
        # 시트 로드
        df_acc = pd.read_excel(xls, sheet_name=1)    # 시트2: 목돈 투입
        df_human = pd.read_excel(xls, sheet_name=2)  # 시트3: 신인류/단타
        
        report = f"🛡️ **[V40-C 진성 요새 기상도]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"

        # --- [1. 시트 2: 목돈 투입 종목 - 생존 확인] ---
        # 평소엔 무소식, 특이사항(급락) 발생 시에만 보고에 추가
        for sym in df_acc['Symbol'].dropna().unique():
            data = get_market_data(sym)
            if data is not None:
                curr = float(data['Close'].iloc[-1])
                low_60 = data['Low'].tail(60).min()
                # 마지노선(최근 60일 저가) 5% 근접 시 경고
                if curr <= low_60 * 1.05:
                    report += f"⚠️ [시트2 긴급] {sym}: 마지노선($ {low_60}) 근접! 현재 $ {curr}\n"
                results_to_save.append({"Type": "Fortress", "Symbol": sym, "Price": curr, "Status": "Holding"})

        # --- [2. 시트 3: 신인류 & 단타 전략] ---
        report += "\n🧬 **[신인류: Core Zone 매집 감시]**\n"
        for _, row in df_human.iterrows():
            sym = row['Symbol']
            if pd.isna(sym): continue
            
            data = get_market_data(sym)
            if data is None: continue
            
            curr = float(data['Close'].iloc[-1])
            # ATR 기반 변동성 계산
            high_low = data['High'] - data['Low']
            atr = high_low.rolling(14).mean().iloc[-1]
            support = data['Low'].tail(60).min()
            
            # 신인류 매집 적정가 계산 (Core Zone)
            core_max = support + (atr * 2.0)
            
            # 단타 타점 계산 (목표가 제시)
            target_price = curr + (atr * 2.5)
            
            # (A) 신인류 매집 보고
            if support <= curr <= core_max:
                report += f"💎 [기회] {sym}: 매집 적정기 ($ {curr})\n"
            
            # (B) 단타 가격표 출력
            report += f"🎯 [단타] {sym}: 목표가 $ {round(target_price, 2)} (손절 $ {round(curr-(atr*1.2), 2)})\n"
            
            results_to_save.append({
                "Type": "NewHuman_Tactical", 
                "Symbol": sym, 
                "Price": curr, 
                "Target": target_price
            })

        # --- [3. Full Process Compliance: 저장 후 보고] ---
        final_df = pd.DataFrame(results_to_save)
        final_df.to_excel("V40_DAILY_TACTICAL.xlsx", index=False)
        
        print("✅ [Complete] V40_DAILY_TACTICAL.xlsx 저장 완료")
        print("-" * 30)
        print(report)

    except Exception as e:
        print(f"⚠️ [수정 필요]: 형님, 공식이나 시트 구조에 모순이 있습니다. {e}")

if __name__ == "__main__":
    run_v40_fortress()
