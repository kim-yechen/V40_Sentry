import os
import glob
import pandas as pd
import yfinance as yf
from datetime import datetime
import time
import requests

# [V40 원칙 1: Full Process Compliance]
# 1+1-1=Complete 원칙에 의거, 로직-데이터-저장을 단일 유닛으로 강제 집행함.
def run_v40_absolute_global_173():
    """
    형님의 173줄 정밀 타격 로직 복구판
    1. 데이터 로딩 및 무결성 검증
    2. 14개국 티커 접미사 강제 매핑
    3. 1:1 개별 종목 정밀 스캔
    4. 3단계 층별 분석 (요새-정예-퀀텀)
    5. 물리적 저장 후 텔레그램 보고
    """
    print(f"🚀 V40 GLOBAL ENGINE START: {datetime.now()}")
    
    # [데이터 확보 단계]
    # glob을 통한 패턴 매칭으로 형님의 최신 파일을 추적함.
    files = glob.glob("*V40_V7C_JAN_WINNERS_WITH_COUNTRY*.csv")
    if not files: 
        print("❌ 엑셀 파일이 없습니다. 형님, 원본 리스트를 확인하십시오.")
        return
    target_file = files[0]
    print(f"🎯 타격 목표 설정: {target_file}")

    try:
        # [데이터 로딩 단계] 
        # 데이터 유실 방지를 위한 형님의 엄격한 로딩 방식 적용
        df_raw = pd.read_csv(target_file)
        if df_raw.empty:
            print("🛑 파일 내용이 비어있습니다. 로직 중단.")
            return

        # [14개국 전선 강제 박제 엔진]
        # 국가 코드를 기반으로 야후 파이낸스 규격 티커를 생성하는 핵심 함수
        def get_global_ticker(symbol, country):
            s = str(symbol).strip().upper()
            c = str(country).strip().upper()
            
            # 이미 도트(.)가 포함된 경우 처리 스킵
            if '.' in s: 
                return s 
            
            # 아시아 5개국 숫자 티커 정밀 분류 로직
            if s.isdigit():
                if len(s) == 6: return s + ".KS" # 한국
                if len(s) == 4: return s + ".T"  # 일본
                if len(s) == 5: return s + ".HK" # 홍콩
                if s.startswith('6'): return s + ".SS" # 상해
                if s.startswith(('0','3')): return s + ".SZ" # 심천
            
            # 영미권 및 유럽 9개국 Suffix 강제 매핑
            suffixes = {
                "UK": ".L", "DE": ".DE", "FR": ".PA", "NL": ".AS",
                "IT": ".MI", "CA": ".TO", "AU": ".AX", "IN": ".NS", 
                "USA": "", "EUR": ".PA", "KOR": ".KS", "JPN": ".T"
            }
            
            # 구형 데이터 규격(L, DE, PA 접미사) 호환성 유지
            if s.endswith('L') and c == "UK": return s.replace('L', '.L')
            if s.endswith('DE') and c == "DE": return s.replace('DE', '.DE')
            if s.endswith('PA') and c == "FR": return s.replace('PA', '.PA')
            
            return f"{s}{suffixes.get(c, '')}"

        # 티커 변환 집행
        df_raw['Yahoo_Ticker'] = df_raw.apply(
            lambda x: get_global_ticker(x['Symbol'], x['Country']), axis=1
        )
        all_syms = df_raw['Yahoo_Ticker'].unique()
        
        print(f"🌍 총 {len(all_syms)}개 전선에 대한 실시간 데이터 확보 개시...")

        # [데이터 수집 엔진]
        # 묶음 요청 누락 방지를 위한 1:1 강제 타격 방식
        full_data = {}
        fail_stats = {"Data_Empty": [], "Short_Period": [], "Fetch_Err": []}
        
        for sym in all_syms:
            try:
                tk_obj = yf.Ticker(sym)
                df = tk_obj.history(period="250d")
                
                # 데이터 유효성 검증 (Negative Check)
                if not df.empty and len(df) > 100:
                    full_data[sym] = df
                    if '.' in sym: 
                        print(f"✅ 해외 데이터 확보: {sym}")
                elif df.empty:
                    fail_stats["Data_Empty"].append(sym)
                else:
                    fail_stats["Short_Period"].append(sym)
                
                # 서버 부하 방지 및 IP 차단 우회를 위한 정밀 딜레이
                time.sleep(0.18)
            except Exception as fe:
                print(f"⚠️ {sym} 수집 에러: {fe}")
                fail_stats["Fetch_Err"].append(sym)

        # [V40 3층 분석 단계]
        pool_2, pool_3, fortress_list, criteria_fail = [], [], [], []

        for sym, df in full_data.items():
            try:
                curr_price = float(df['Close'].iloc[-1])
                
                # [2층: 흑자전환 강제 검증 - 팔란티어 로직]
                is_turnaround = False
                try:
                    tk_fin = yf.Ticker(sym)
                    income = tk_fin.income_stmt
                    if not income.empty and 'Net Income' in income.index:
                        ni = income.loc['Net Income'].dropna()
                        if len(ni) >= 2:
                            # 전기 적자 -> 당기 흑자 전환 필터링
                            if ni.iloc[1] < 0 and ni.iloc[0] > 0:
                                is_turnaround = True
                except: 
                    pass # 재무 데이터 부재 시 기술적 분석으로 대체

                # [1층: 강철 요새 분석]
                # 최근 100일 최저점 대비 5% 이내 지지 여부 판별
                low_100 = df['Low'].tail(100).min()
                dist = (curr_price / low_100 - 1) * 100
                
                if dist <= 5.0:
                    fortress_list.append(f"🚨 {sym}: {curr_price:.2f} ({dist:.1f}% 지지)")
                else:
                    criteria_fail.append(f"{sym}({dist:.1f}%)")

                # [2/3층: EDI 에너지 및 퀀텀 타겟]
                # EDI = 거래량 에너지 / 변동성 (형님의 고유 공식)
                rets = df['Close'].pct_change(fill_method=None)
                v_std = df['Volume'].pct_change(fill_method=None).rolling(10).std()
                r_std = rets.rolling(10).std()
                v_energy = (v_std * r_std * 10000).fillna(0)
                edi = (v_energy.rolling(120).mean() / (rets.rolling(120).std() + 1e-9)).iloc[-1]
                
                pool_2.append({'sym': sym, 'curr': curr_price, 'edi': int(edi), 'turn': is_turnaround})

                # 퀀텀 타격: 흑자전환 종목 대상 ATR 변동성 목표가 산출
                if is_turnaround:
                    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
                    pool_3.append({
                        'sym': sym, 'curr': curr_price, 
                        'target': curr_price + (atr * 4.0), 'edi': edi
                    })
            except Exception as ae:
                continue

        # [V40 원칙 2: 파일 물리적 저장 후 보고]
        # 결과가 없더라도 빈 파일을 생성하여 프로세스 완료를 증명함.
        final_df = pd.DataFrame(pool_3 if pool_3 else pool_2)
        report_name = "V40_GLOBAL_173_FINAL_REPORT.xlsx"
        final_df.to_excel(report_name, index=False)
        print(f"💾 보고서 저장 완료: {report_name}")

        # [텔레그램 보고 단계]
        t_key, c_id = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0", "198757117"
        
        p2_report = "\n".join([f"💎 {x['sym']}: {x['curr']:.2f} (🔋EDI: {x['edi']})" for x in sorted(pool_2, key=lambda x:x['edi'], reverse=True)[:5]])
        p3_report = "\n".join([f"🔥 {x['sym']} | EDI: {x['edi']:.1f} [퀀텀 타격]" for x in sorted(pool_3 if pool_3 else pool_2, key=lambda x:x.get('edi',0), reverse=True)[:5]])
        
        full_msg = (
            f"✅ V40 제압 완료 ({datetime.now().strftime('%m-%d %H:%M')})\n\n"
            f"🏰 [1층 요새] - {len(fortress_list)}개\n" + "\n".join(fortress_list[:10]) + 
            f"\n\n🧬 [2층 정예]\n{p2_report}\n\n"
            f"🚀 [3층 퀀텀]\n{p3_report}\n\n"
            f"📉 기준미달: {len(criteria_fail)}건 | 데이터누락: {len(fail_stats['Data_Empty'])}건"
        )
        
        requests.post(f"https://api.telegram.org/bot{t_key}/sendMessage", json={"chat_id": c_id, "text": full_msg})
        
        # [최종 출력]
        print(f"\n✅ 형님, 173줄 정밀 공정 집행을 완료했습니다.")
        print(f"🏰 요새 리스트: {len(fortress_list)}개 탐지됨.")

    except Exception as ge:
        print(f"🛑 치명적 에러: {ge}. 로직을 즉시 점검하십시오.")

if __name__ == "__main__":
    run_v40_absolute_global_173()
