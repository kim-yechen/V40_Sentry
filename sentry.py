import os
import glob
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime

# --- [V40 원칙 준수: 전 세계 통합 지령] ---
def run_v40_unlimited_global_engine():
    # 1. 파일 강제 로드 (V40 업그레이드 파일)
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: 
        print("❌ 파일을 찾을 수 없습니다."); return
    
    target_file = files[0]
    try:
        xls = pd.ExcelFile(target_file)
        # 1층(Shield), 2층(Spear), Full Spectrum 전 시트 티커 통합
        df_1 = pd.read_excel(xls, sheet_name=1) 
        df_2 = pd.read_excel(xls, sheet_name=2) 
        df_3 = pd.read_excel(xls, sheet_name=3) 
        
        # [핵심] 엑셀에 존재하는 모든 티커를 "있는 그대로" 추출 (유럽/아시아 전역 포함)
        # .KS, .KQ, .T, .HK, .DE, .L, .PA, .AS, .MI, .MA, .SW, .OL, .BR 등 무제한
        all_raw_syms = pd.concat([df_1['Symbol'], df_2['Symbol'], df_3['Symbol']]).dropna().unique()
        all_syms = [str(s).strip() for s in all_raw_syms]
        
        # 2. 전 세계 데이터 동시 다운로드 (티커 씹힘 방지)
        # 형님, 여기서 유럽/아시아 모든 티커가 야후 서버로 직결됩니다.
        raw = yf.download(all_syms, period="200d", group_by='ticker', progress=False, threads=True)
        
        report = f"🛡️ [V40-C 전 세계 무제한 통합 지령]\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"
        report += f"🌐 총 감시 종목: {len(all_syms)}개 전선 가동 중\n"

        # --- [데이터 분석 및 Negative Check] ---
        human_pool = []
        
        for sym in all_syms:
            try:
                data = raw[sym]
                if data.empty or len(data) < 100: continue
                
                close, vol = data['Close'], data['Volume']
                curr_price = float(close.iloc[-1])
                
                # 퀀텀 수식 (EDI) 적용
                returns = close.pct_change()
                v_energy = (vol.pct_change().rolling(10).std() * returns.rolling(10).std() * 10000).fillna(0)
                edi = (v_energy.rolling(120).mean() / (returns.rolling(120).std() + 1e-9)).iloc[-1]
                
                # 2층 신인류 타점 분석 (유럽/한국/일본 통합)
                support = data['Low'].tail(60).min()
                atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
                core_max = support + (atr * 2.2) # 포착 범위 살짝 조정
                
                if support <= curr_price <= core_max:
                    human_pool.append({'sym': sym, 'curr': curr_price, 'core': core_max, 'edi': edi})
            except: continue

        # --- [최종 출력: 국가별 정예병 보고] ---
        if human_pool:
            report += "\n🧬 [2층: 전 세계 신인류 정예 TOP 10]\n"
            # EDI(수급 에너지) 순으로 정렬하여 상위 10개 보고
            for h in sorted(human_pool, key=lambda x: x['edi'], reverse=True)[:10]:
                report += f"💎 {h['sym']}: {h['curr']:.2f} (적정가 ~{h['core']:.1f} | 🔋{int(h['edi'])})\n"

        # [Full Process Compliance] 무조건 저장 후 보고
        result_df = pd.DataFrame(human_pool)
        result_df.to_excel("V40_ALL_WORLD_FINAL.xlsx", index=False)
        
        print(report) # 텔레그램 전송 대신 우선 출력으로 확인

    except Exception as e:
        print(f"⚠️ 시스템 오류: {e}")

if __name__ == "__main__":
    run_v40_unlimited_global_engine()
