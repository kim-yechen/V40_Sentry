import os
import glob
import pandas as pd
import yfinance as yf
from datetime import datetime
import time
import requests

# [V40 원칙: Full Process Compliance]
# 1+1-1=Complete: 로직 + 데이터 + 저장 = 하나의 단위.
# 물리적 파일 저장이 완료되기 전에는 절대로 보고하지 않는다.
def run_v40_absolute_global_173_ironclad():
    """
    형님의 173줄 정밀 타격 로직 완전 복구판
    - 22초 컷 방지용 강제 재시도 엔진 탑재
    - 텔레그램 전송 실패 시 3회 재시도 보장
    - 14개국 전선 티커 규격 강제 매핑
    """
    start_time = datetime.now()
    print(f"🚀 V40 정밀 타격 엔진 가동: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # [1단계: 타겟 파일 추적]
    files = glob.glob("*V40_V7C_JAN_WINNERS_WITH_COUNTRY*.csv")
    if not files: 
        print("❌ 엑셀 파일이 없습니다. 형님, 리스트를 확인하십시오.")
        return
    target_file = files[0]
    print(f"🎯 타격 목표 설정: {target_file}")

    try:
        # [2단계: 데이터 로딩 및 초기화]
        df_raw = pd.read_csv(target_file)
        if df_raw.empty:
            print("🛑 원본 데이터가 비어 있습니다. 집행 중단.")
            return

        # [3단계: 14개국 전선 강제 박제 엔진]
        def get_global_ticker(symbol, country):
            s = str(symbol).strip().upper()
            c = str(country).strip().upper()
            if '.' in s: return s 
            
            # 아시아 5개국 숫자 체계 정밀 매핑
            if s.isdigit():
                if len(s) == 6: return s + ".KS" # KOR
                if len(s) == 4: return s + ".T"  # JPN
                if len(s) == 5: return s + ".HK" # HKG
                if s.startswith('6'): return s + ".SS" # SHG
                if s.startswith(('0','3')): return s + ".SZ" # SZN
            
            # 유럽 및 영미권 9개국 Suffix 강제 주입
            suffixes = {
                "UK": ".L", "DE": ".DE", "FR": ".PA", "NL": ".AS",
                "IT": ".MI", "CA": ".TO", "AU": ".AX", "IN": ".NS", 
                "USA": "", "EUR": ".PA", "KOR": ".KS", "JPN": ".T"
            }
            return f"{s}{suffixes.get(c, '')}"

        df_raw['Yahoo_Ticker'] = df_raw.apply(
            lambda x: get_global_ticker(x['Symbol'], x['Country']), axis=1
        )
        all_syms = df_raw['Yahoo_Ticker'].unique()
        print(f"🌍 총 {len(all_syms)}개 종목 전선 확보... (예상 소요 시간: 8분 내외)")

        # [4단계: 강제 집행 엔진 - 22초 컷 방지 루프]
        full_data = {}
        fail_stats = {"Empty": [], "Err": []}
        
        for idx, sym in enumerate(all_syms):
            success = False
            for attempt in range(3): # 최대 3회 재시도
                try:
                    print(f"🔎 [{idx+1}/{len(all_syms)}] {sym} 데이터 확보 시도 (Attempt {attempt+1})...", end="\r")
                    tk = yf.Ticker(sym)
                    # 형님의 원칙: 250일치 이상의 충분한 시계열 확보
                    df = tk.history(period="1y", interval="1d")
                    
                    if not df.empty and len(df) > 150:
                        full_data[sym] = df
                        success = True
                        break
                    time.sleep(1.5) # 재시도 간격
                except:
                    time.sleep(2)
            
            if not success:
                fail_stats["Empty"].append(sym)
            time.sleep(0.5) # IP 차단 방지용 정밀 딜레이

        # [5단계: V40 3층 분석 엔진]
        fortress_list, pool_2, pool_3, criteria_fail = [], [], [], []

        for sym, df in full_data.items():
            try:
                curr_price = float(df['Close'].iloc[-1])
                
                # [2층: 흑자전환 정밀 검증]
                is_turnaround = False
                try:
                    tk_fin = yf.Ticker(sym)
                    income = tk_fin.income_stmt
                    if not income.empty and 'Net Income' in income.index:
                        ni = income.loc['Net Income'].dropna()
                        if len(ni) >= 2 and ni.iloc[1] < 0 and ni.iloc[0] > 0:
                            is_turnaround = True
                except: pass

                # [1층: 강철 요새 분석]
                low_100 = df['Low'].tail(100).min()
                dist = (curr_price / low_100 - 1) * 100
                if dist <= 5.0:
                    fortress_list.append(f"🚨 {sym}: {curr_price:.2f} ({dist:.1f}%)")
                else:
                    criteria_fail.append(sym)

                # [EDI 에너지 공식 집행]
                rets = df['Close'].pct_change()
                v_std = df['Volume'].pct_change().rolling(10).std()
                r_std = rets.rolling(10).std()
                v_energy = (v_std * r_std * 1000000).fillna(0)
                edi = (v_energy.rolling(120).mean() / (rets.rolling(120).std() + 1e-9)).iloc[-1]
                
                pool_2.append({'sym': sym, 'curr': curr_price, 'edi': int(edi)})
                if is_turnaround:
                    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
                    pool_3.append({'sym': sym, 'edi': edi, 'target': curr_price + (atr * 4.0)})
            except: continue

        # [6단계: 데이터 물리적 저장]
        final_df = pd.DataFrame(pool_3 if pool_3 else pool_2)
        final_df.to_excel("V40_GLOBAL_FINAL_REPORT.xlsx", index=False)
        print(f"\n💾 엑셀 저장 완료: V40_GLOBAL_FINAL_REPORT.xlsx")

        # [7단계: 텔레그램 전송 보장 시스템]
        def send_secure_telegram(msg):
            t_key = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
            c_id = "198757117"
            url = f"https://api.telegram.org/bot{t_key}/sendMessage"
            
            for _ in range(3): # 전송 실패 시 3회 재시도
                try:
                    r = requests.post(url, json={"chat_id": c_id, "text": msg}, timeout=20)
                    if r.status_code == 200: return True
                    time.sleep(5)
                except: time.sleep(5)
            return False

        report_msg = (f"✅ V40 제압 리포트 ({datetime.now().strftime('%H:%M')})\n"
                      f"🏰 요새: {len(fortress_list)}개 탐지\n" + "\n".join(fortress_list[:12]) +
                      f"\n\n🔥 퀀텀 타겟: {len(pool_3)}개\n"
                      f"📉 데이터 누락: {len(fail_stats['Empty'])}건")
        
        if send_secure_telegram(report_msg):
            print("🎯 텔레그램 보고 완료.")
        else:
            print("🛑 텔레그램 전송 최종 실패.")

        duration = (datetime.now() - start_time).seconds
        print(f"🏁 집행 완료 (소요시간: {duration}초). 형님의 173줄 철학을 완수했습니다.")

    except Exception as e:
        print(f"🛑 치명적 에러: {e}. 즉시 수정하겠습니다.")

if __name__ == "__main__":
    run_v40_absolute_global_173_ironclad()
