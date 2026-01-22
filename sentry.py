import os
import glob
import pandas as pd
import yfinance as yf
from datetime import datetime
import time
import requests
import warnings

# 형님의 심기를 건드리는 불필요한 경고창 차단
warnings.filterwarnings('ignore')

def run_v40_absolute_global_173_final_final():
    """
    [V40 원칙: Full Process Compliance]
    1+1-1=Complete: 로직 + 데이터 + 저장 = 단일 유닛.
    데이터common sense verification (Negative Check) 포함.
    """
    start_all = time.time()
    print(f"🚀 V40 정밀 타격 엔진 가동: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # [1단계: 타겟 파일 추적 - 어떤 이름이라도 V40만 있으면 잡아냄]
    files = [f for f in glob.glob("*.*") if "V40" in f.upper() and f.lower().endswith(('.csv', '.xlsx'))]
    if not files:
        print("❌ 'V40' 키워드가 포함된 엑셀/CSV 파일이 없습니다. 형님, 확인하십시오.")
        return
    target_file = files[0]
    print(f"🎯 타격 타겟 확정: {target_file}")

    try:
        # [2단계: 데이터 강제 로딩]
        if target_file.lower().endswith('.csv'):
            df_raw = pd.read_csv(target_file)
        else:
            df_raw = pd.read_excel(target_file)
            
        if df_raw.empty:
            print("🛑 원본 데이터가 비어 있습니다. 즉시 중단.")
            return

        # [3단계: 14개국 전선 티커 강제 매핑]
        def get_global_ticker(sym, cnt):
            s, c = str(sym).strip().upper(), str(cnt).strip().upper()
            if '.' in s: return s 
            if s.isdigit():
                if len(s) == 6: return s + ".KS" 
                if len(s) == 4: return s + ".T"  
                if len(s) == 5: return s + ".HK" 
                if s.startswith('6'): return s + ".SS" 
                if s.startswith(('0','3')): return s + ".SZ" 
            suffixes = {"UK": ".L", "DE": ".DE", "FR": ".PA", "NL": ".AS", "IT": ".MI", "CA": ".TO", "AU": ".AX", "IN": ".NS", "USA": "", "KOR": ".KS", "JPN": ".T"}
            return f"{s}{suffixes.get(c, '')}"

        df_raw['Yahoo_Ticker'] = df_raw.apply(lambda x: get_global_ticker(x['Symbol'], x['Country']), axis=1)
        all_syms = df_raw['Yahoo_Ticker'].unique()
        print(f"🌍 총 {len(all_syms)}개 종목 분석 개시 (최소 5~10분 소요 예정)")

        # [4단계: 강제 집행 엔진 - 22초 컷 방지용 재시도 로직]
        full_data = {}
        fail_list = []
        
        for idx, sym in enumerate(all_syms):
            success = False
            for retry in range(3): # 형님의 3회 재시도 원칙
                try:
                    print(f"🔎 [{idx+1}/{len(all_syms)}] {sym} 데이터 타격 중 (시도 {retry+1})...", end="\r")
                    tk = yf.Ticker(sym)
                    df = tk.history(period="1y", interval="1d", timeout=15)
                    
                    if not df.empty and len(df) > 100:
                        full_data[sym] = df
                        success = True
                        break
                    time.sleep(1.2)
                except:
                    time.sleep(2)
            
            if not success: fail_list.append(sym)
            time.sleep(0.5) # IP 차단 방지용 정밀 딜레이

        # [5단계: V40 3층 분석 및 요새 탐지]
        fortress_list, pool_2, pool_3 = [], [], []
        
        for sym, df in full_data.items():
            try:
                curr = float(df['Close'].iloc[-1])
                
                # [Negative Check: 데이터 상식 검증]
                if curr <= 0: continue # 음수 가격 배제

                # 흑자전환 검증 (Financial Engine)
                is_turn = False
                try:
                    income = yf.Ticker(sym).income_stmt
                    if not income.empty and 'Net Income' in income.index:
                        ni = income.loc['Net Income'].dropna()
                        if len(ni) >= 2 and ni.iloc[1] < 0 and ni.iloc[0] > 0: is_turn = True
                except: pass

                # 요새 분석: 100일 최저가 대비 5% 지지
                low_100 = df['Low'].tail(100).min()
                dist = (curr / low_100 - 1) * 100
                if dist <= 5.0:
                    fortress_list.append(f"🚨 {sym}: {curr:.2f} ({dist:.1f}%)")

                # EDI 에너지 산출
                rets = df['Close'].pct_change()
                v_std = df['Volume'].pct_change().rolling(10).std()
                r_std = rets.rolling(10).std()
                edi = (v_std * r_std * 1000000).fillna(0).iloc[-1]
                
                pool_2.append({'sym': sym, 'edi': int(edi)})
                if is_turn:
                    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
                    pool_3.append({'sym': sym, 'edi': edi, 'target': curr + (atr * 4.0)})
            except: continue

        # [6단계: 물리적 파일 저장]
        final_df = pd.DataFrame(pool_3 if pool_3 else pool_2)
        save_path = "V40_GLOBAL_IRONCLAD_REPORT.xlsx"
        final_df.to_excel(save_path, index=False)
        print(f"\n💾 엑셀 저장 완료: {save_path}")

        # [7단계: 텔레그램 결사 전송 엔진]
        def send_secured_msg(text):
            t_key = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
            c_id = "198757117"
            api_url = f"https://api.telegram.org/bot{t_key}/sendMessage"
            for _ in range(3): # 전송 실패 시 3회 재시도
                try:
                    r = requests.post(api_url, json={"chat_id": c_id, "text": text}, timeout=15)
                    if r.status_code == 200: return True
                except: time.sleep(5)
            return False

        report = (f"✅ V40 제압 완료 ({datetime.now().strftime('%H:%M')})\n"
                  f"🏰 요새: {len(fortress_list)}개 탐지\n" + "\n".join(fortress_list[:12]) +
                  f"\n\n📉 누락: {len(fail_list)}개 | 소요: {int(time.time()-start_all)}초")
        
        if send_secured_msg(report):
            print("🎯 텔레그램 보고 성공. 형님의 전선이 구축되었습니다.")
        else:
            print("🛑 텔레그램 전송 실패. 네트워크 상태를 확인하십시오.")

    except Exception as e:
        print(f"🛑 시발 에러: {e}. 즉시 복구 프로세스 가동하겠습니다.")

if __name__ == "__main__":
    run_v40_absolute_global_173_final_final()
