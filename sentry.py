import os
import glob
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# --- [V40 원칙 준수] ---
# 1. Full process compliance (분석+처리+저장=Complete)
# 2. Negative Check (기계적 오류 검증)
# 3. No Shortcuts (오류 시 즉시 보고)

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
    results_to_save = [] 
    
    # [형님 특별 지시] 엑셀에 없어도 무조건 감시할 종목 리스트
    special_watch = ['SLV', 'SCCO', 'FCX']
    
    try:
        xls = pd.ExcelFile(target_file)
        df_acc = pd.read_excel(xls, sheet_name=1)    
        df_human = pd.read_excel(xls, sheet_name=2)  
        
        report = f"🛡️ **[V40-C 진성 요새 기상도]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"

        # --- [1. 시트 2 및 특별 감시 종목 - 생존 확인] ---
        # 엑셀 시트2 종목 + 형님이 말씀하신 SLV, SCCO, FCX 통합
        combined_watch = list(df_acc['Symbol'].dropna().unique()) + special_watch
        combined_watch = list(set(combined_watch)) # 중복 제거

        for sym in combined_watch:
            data = get_market_data(sym)
            if data is not None:
                curr = float(data['Close'].iloc[-1])
                low_60 = data['Low'].tail(60).min()
                
                # 마지노선(최근 60일 저가) 5% 근접 시 경고
                if curr <= low_60 * 1.05:
                    tag = "🚨 [긴급/미보유분]" if sym in special_watch and sym not in df_acc['Symbol'].values else "⚠️ [시트2]"
                    report += f"{tag} {sym}: 마지노선($ {low_60}) 근접! 현재 $ {curr}\n"
                
                results_to_save.append({"Type": "Fortress_Watch", "Symbol": sym, "Price": curr, "Status": "Holding"})

        # --- [2. 시트 3: 신인류 & 단타 전략] ---
        report += "\n🧬 **[신인류: Core Zone 매집 감시]**\n"
        for _, row in df_human.iterrows():
            sym = row['Symbol']
            if pd.isna(sym): continue
            
            data = get_market_data(sym)
            if data is None: continue
            
            curr = float(data['Close'].iloc[-1])
            high_low = data['High'] - data['Low']
            atr = high_low.rolling(14).mean().iloc[-1]
            support = data['Low'].tail(60).min()
            
            core_max = support + (atr * 2.0)
            target_price = curr + (atr * 2.5)
            
            # (A) 신인류 매집 보고
            if support <= curr <= core_max:
                report += f"💎 [기회] {sym}: 매집 적정기 ($ {curr})\n"
            
            # (B) 단타 가격표
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
        print(f"⚠️ [수정 필요]: 형님, 로직에 오류가 있습니다. {e}")

if __name__ == "__main__":
    run_v40_fortress()
