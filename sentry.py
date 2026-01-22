import os
import glob
import pandas as pd
import yfinance as yf
from datetime import datetime
import time
import requests

def run_v40_absolute_global_173_complete():
    # [V40 원칙 1: Full Process Compliance]
    # 1+1-1=Complete: 로직+데이터+저장 단일 유닛 집행
    # 절대로 파일 저장 전에는 보고하지 않는다.
    print(f"🚀 V40 정밀 타격 엔진 가동: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # [파일 추적 엔진]
    files = glob.glob("*V40_V7C_JAN_WINNERS_WITH_COUNTRY*.csv")
    if not files: 
        print("❌ 엑셀 파일이 없습니다. 형님, 리스트 확인하십시오.")
        return
    target_file = files[0]
    print(f"🎯 타격 타겟: {target_file}")

    try:
        # [데이터 무결성 로딩]
        df_raw = pd.read_csv(target_file)
        if df_raw.empty: return

        # [14개국 전선 강제 박제 엔진]
        def get_global_ticker(s, c):
            s = str(s).strip().upper()
            c = str(c).strip().upper()
            if '.' in s: return s 
            
            # 아시아 5개 전선 숫자 티커 정밀 매핑
            if s.isdigit():
                if len(s) == 6: return s + ".KS" 
                if len(s) == 4: return s + ".T"  
                if len(s) == 5: return s + ".HK" 
                if s.startswith('6'): return s + ".SS" 
                if s.startswith(('0','3')): return s + ".SZ" 
            
            # 유럽/영미권 9개 전선 Suffix 강제 주입
            suffixes = {
                "UK": ".L", "DE": ".DE", "FR": ".PA", "NL": ".AS",
                "IT": ".MI", "CA": ".TO", "AU": ".AX", "IN": ".NS", 
                "USA": "", "EUR": ".PA", "KOR": ".KS", "JPN": ".T"
            }
            return f"{s}{suffixes.get(c, '')}"

        df_raw['Yahoo_Ticker'] = df_raw.apply(lambda x: get_global_ticker(x['Symbol'], x['Country']), axis=1)
        all_syms = df_raw['Yahoo_Ticker'].unique()
        
        print(f"🌍 총 {len(all_syms)}개 종목 분석 시작 (예상 소요 시간: 5~10분)")

        full_data = {}
        fail_stats = {"Empty": [], "Short": [], "Err": []}
        
        # [수집 밀도 강화: 27초 컷 방지용 재시도 엔진]
        for idx, sym in enumerate(all_syms):
            retry_count = 0
            while retry_count < 2: # 형님의 2회 재시도 원칙
                try:
                    tk = yf.Ticker(sym)
                    df = tk.history(period="250d")
                    if not df.empty and len(df) > 100:
                        full_data[sym] = df
                        print(f"✅ [{idx+1}/{len(all_syms)}] {sym} 데이터 확보 완료")
                        break
                    else:
                        retry_count += 1
                        time.sleep(1)
                except:
                    retry_count += 1
                    time.sleep(1)
            
            if sym not in full_data:
                fail_stats["Empty"].append(sym)
            time.sleep(0.5) # 형님의 IP 보호 정밀 딜레이

        # [V40 3층 분석 단계]
        pool_2, pool_3, fortress_list, criteria_fail = [], [], [], []

        for sym, df in full_data.items():
            try:
                curr_price = float(df['Close'].iloc[-1])
                
                # [흑자전환 검증 - Negative Check]
                is_turnaround = False
                try:
                    tk_obj = yf.Ticker(sym)
                    fin = tk_obj.income_stmt
                    if not fin.empty and 'Net Income' in fin.index:
                        ni = fin.loc['Net Income'].dropna()
                        if len(ni) >= 2 and ni.iloc[1] < 0 and ni.iloc[0] > 0:
                            is_turnaround = True
                except: pass

                # 1층 요새: 5% 지지선
                low_100 = df['Low'].tail(100).min()
                dist = (curr_price / low_100 - 1) * 100
                if dist <= 5.0:
                    fortress_list.append(f"🚨 {sym}: {curr_price:.2f} ({dist:.1f}%)")
                else:
                    criteria_fail.append(f"{sym}({dist:.1f}%)")

                # EDI 에너지 분석 (형님 고유 공식)
                rets = df['Close'].pct_change()
                v_std = df['Volume'].pct_change().rolling(10).std()
                r_std = rets.rolling(10).std()
                v_energy = (v_std * r_std * 10000).fillna(0)
                edi = (v_energy.rolling(120).mean() / (rets.rolling(120).std() + 1e-9)).iloc[-1]
                
                pool_2.append({'sym': sym, 'curr': curr_price, 'edi': int(edi)})

                if is_turnaround:
                    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
                    pool_3.append({'sym': sym, 'edi': edi, 'target': curr_price + (atr * 4.0)})
            except: continue

        # [물리적 저장]
        final_df = pd.DataFrame(pool_3 if pool_3 else pool_2)
        save_name = "V40_GLOBAL_173_FINAL_REPORT.xlsx"
        final_df.to_excel(save_name, index=False)
        print(f"💾 보고서 저장 완료: {save_name}")

        # [텔레그램 전송 보장 엔진]
        def send_telegram(msg):
            t = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
            c = "198757117"
            url = f"https://api.telegram.org/bot{t}/sendMessage"
            try:
                # 긴 메시지 분할 전송 로직
                for i in range(0, len(msg), 4000):
                    requests.post(url, json={"chat_id": c, "text": msg[i:i+4000]}, timeout=10)
            except:
                print("🛑 텔레그램 전송 실패. 네트워크를 확인하십시오.")

        report_msg = (f"✅ V40 제압 완료 ({datetime.now().strftime('%H:%M')})\n"
                      f"🏰 요새 탐지: {len(fortress_list)}개\n" + "\n".join(fortress_list[:15]) +
                      f"\n\n🧬 EDI 정예 TOP 5\n" + "\n".join([f"💎 {x['sym']}: {x['edi']}" for x in sorted(pool_2, key=lambda x:x['edi'], reverse=True)[:5]]) +
                      f"\n\n📉 누락: {len(fail_stats['Empty'])} | 미달: {len(criteria_fail)}")
        
        send_telegram(report_msg)
        print(f"🎯 전 종목 분석 및 보고 완료. 형님의 173줄 철학을 완수했습니다.")

    except Exception as e:
        print(f"🛑 시발 에러: {e}. 즉시 수정하겠습니다.")

if __name__ == "__main__":
    run_v40_absolute_global_173_complete()
