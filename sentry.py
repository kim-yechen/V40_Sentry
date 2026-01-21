import os
import glob
import pandas as pd
import yfinance as yf
from datetime import datetime
import time
import requests

def run_v40_absolute_global_14():
    # [V40 원칙] 1+1-1=Complete: 로직+데이터+저장을 하나로
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: 
        print("❌ 엑셀 파일이 없습니다. 형님, 원본 리스트를 확인하십시오.")
        return
        
    target_file = files[0]

    try:
        # 1. 엑셀 로딩 (형님이 말씀하신 시트들 확인)
        xls = pd.ExcelFile(target_file)
        # 마스터 데이터는 'Full_Spectrum'에서 가져옴
        df_master = pd.read_excel(xls, sheet_name='Full_Spectrum')
        
        # 2. 형님이 세팅한 티커 그대로 추출 (보정 없이 그대로 사용)
        all_syms = [str(s).strip().upper() for s in df_master['Symbol'].dropna().unique()]
        print(f"✅ 확인 완료: {len(all_syms)}개 종목 분석 시작")

        market_heats = {"KR": [], "US": [], "JP": [], "HK": [], "EU": []}

        # 3. 데이터 수집 엔진
        for sym in all_syms:
            try:
                # 엑셀 티커 그대로 야후에 던짐
                t_obj = yf.Ticker(sym)
                h = t_obj.history(period="250d")
                
                if not h.empty:
                    # 국가 분류 로직 (이미 엑셀에 점미사가 있으므로 포함 여부로 판단)
                    if ".KS" in sym or ".KQ" in sym: cat = "KR"
                    elif ".T" in sym: cat = "JP"
                    elif ".HK" in sym: cat = "HK"
                    elif any(x in sym for x in [".L", ".DE", ".PA", ".AS", ".MI"]): cat = "EU"
                    else: cat = "US"

                    # 온도계 계산 (120일 고점 대비 현재가)
                    high_120 = h['High'].tail(120).max()
                    current_price = float(h['Close'].iloc[-1])
                    heat = (current_price / high_120) * 100
                    market_heats[cat].append(heat)
                    
                time.sleep(0.1) # 과부하 방지
            except:
                continue
        
        # 4. 온도계 결과 리포팅
        print("\n" + "="*40)
        print(f"📊 {datetime.now().strftime('%Y-%m-%d %H:%M')} 시장 온도 리포트")
        print("-" * 40)
        for k, v in market_heats.items():
            if v:
                avg_heat = sum(v) / len(v)
                print(f"📡 {k} 시장 온도: {avg_heat:.2f}% (종목수: {len(v)})")
        print("="*40)

    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {e}")

        # 2. 직접 티커 보정 로직 (get_global_ticker 함수 대신 사용)
        all_syms_raw = df_master['Symbol'].dropna().unique()
        all_syms = []
        for s in all_syms_raw:
            s = str(s).strip().upper()
            if s.endswith('L') and '.' not in s: s = s[:-1] + '.L'
            elif s.endswith('DE') and '.' not in s: s = s[:-2] + '.DE'
            elif s.endswith('PA') and '.' not in s: s = s[:-2] + '.PA'
            all_syms.append(s)
        

        # [수선] 정의되지 않은 df_a, df_b 대신 df_master 사용
        all_syms_raw = df_master['Symbol'].dropna().unique() 
        all_syms = []
        # (그 아래 for문 로직은 형님 버전 그대로 유지...)
        for s in all_syms_raw:
            s = str(s).strip().upper()
            if s.endswith('L') and '.' not in s: s = s[:-1] + '.L'
            elif s.endswith('DE') and '.' not in s: s = s[:-2] + '.DE'
            elif s.endswith('PA') and '.' not in s: s = s[:-2] + '.PA'
            all_syms.append(s)
        
        print(f"🌍 14개국 {len(all_syms)}개 종목 전선 실시간 데이터 집행 및 돌파 시작...")

        # [수정: 해외 데이터 누락 방지 - 묶음 요청 배제, 1:1 강제 타격 엔진]
        # 야후 서버가 해외 티커 묶음 요청 시 데이터를 누락시키는 고질적 문제 해결
        full_data = {}
        # [추가 로직] 탈락 사유 추적을 위한 카운터 (밀도 상승)
        fail_stats = {"Data_Empty": [], "Short_Period": [], "Fetch_Err": []}
        
        # [온도계 세분화: 아시아 전선 해체]
        market_heats = {"US": [], "KR": [], "JP": [], "HK": [], "EU": []}
        
        for sym in all_syms:
            try:
                # [개별 타격 엔진 강화] - 아시아 데이터는 안 주면 3번까지 재청구
                ticker_obj = yf.Ticker(sym)
                df = pd.DataFrame()
                
                for attempt in range(3): # 최대 3번 시도
                    df = ticker_obj.history(period="250d")
                    if not df.empty: break
                    time.sleep(0.5) # 실패 시 0.5초 쉬고 재시도
                
                if not df.empty and len(df) > 100:
                    full_data[sym] = df  # <--- 이 줄이 반드시 있어야 나중에 분석이 됩니다!
                    
                    # --- [온도계 계산 로직 시작] ---
                    if ".KS" in sym or ".KQ" in sym: cat = "KR"
                    elif ".T" in sym: cat = "JP"
                    elif ".HK" in sym: cat = "HK"
                    elif any(x in sym for x in [".L", ".DE", ".PA", ".AS", ".MI"]): cat = "EU"
                    else: cat = "US"

                    high_v_temp = df['High'].tail(120).max()
                    heat_val = (float(df['Close'].iloc[-1]) / high_v_temp) * 100
                    market_heats[cat].append(heat_val)
                    # --- [온도계 계산 로직 끝] ---
                    
                    # 고점 근접도 계산 (현대차, 한화 등 주도주 화력 반영)
                    high_v_temp = df['High'].tail(120).max()
                    heat_val = (float(df['Close'].iloc[-1]) / high_v_temp) * 100
                    market_heats[cat].append(heat_val)

                    # --- 엔진 끝 ---
                    
                    if '.' in sym: 
                        print(f"✅ 해외 전선 데이터 확보 성공: {sym}")
                elif df.empty:
                    fail_stats["Data_Empty"].append(sym)
                else:
                    fail_stats["Short_Period"].append(sym)
                # 서버 IP 차단 및 부하 방지를 위한 정밀 딜레이
                time.sleep(0.15)
            except Exception:
                fail_stats["Fetch_Err"].append(sym)
                continue

        pool_2, pool_3, fortress_list = [], [], []
        # [추가 로직] 기준 미달(지지선 이탈) 종목 추적 리스트
        criteria_fail = []

        for sym, df in full_data.items():
            try:
                # [V40 분석 단계: 가격 데이터 추출]
                curr_price = float(df['Close'].iloc[-1])
                
                # [V40-팔란티어 로직: 흑자전환 강제 검증]
                # Negative Check: 재무 데이터가 없거나 논리에 맞지 않으면 제외
                is_turnaround = False
                try:
                    tk = yf.Ticker(sym)
                    fin = tk.income_stmt
                    if not fin.empty and 'Net Income' in fin.index:
                        ni = fin.loc['Net Income'].dropna()
                        if len(ni) >= 2:
                            # 전기 적자 -> 당기 흑자 전환 여부 판별
                            if ni.iloc[1] < 0 and ni.iloc[0] > 0:
                                is_turnaround = True
                except Exception:
                    pass

                # 1층 요새 분석: 최근 100일 최저가 대비 현재가 괴리율 (지지선 5.0% 이내)
                low_100 = df['Low'].tail(100).min()
                dist = (curr_price / low_100 - 1) * 100
                if dist <= 5.0:
                    fortress_list.append(f"🚨 {sym}: {curr_price:.2f} ({dist:.1f}% 지지선)")
                else:
                    # [추가 로직] 형님의 기준(5%)을 넘어서 너무 많이 오른 종목 추적
                    criteria_fail.append(f"{sym}({dist:.1f}%)")

                # 2/3층 EDI 에너지 분석 (거래량 변동성 x 수익률 변동성)
                # EDI = (Volume Energy Moving Average) / (Return Volatility)
                rets = df['Close'].pct_change(fill_method=None)
                v_std = df['Volume'].pct_change(fill_method=None).rolling(10).std()
                r_std = rets.rolling(10).std()
                v_energy = (v_std * r_std * 10000).fillna(0)
                edi = (v_energy.rolling(120).mean() / (rets.rolling(120).std() + 1e-9)).iloc[-1]
                
                pool_2.append({'sym': sym, 'curr': curr_price, 'edi': int(edi), 'turn': is_turnaround})

                # 3층 퀀텀 타겟: 흑자전환주 대상 ATR 기반 목표가 산출
                if is_turnaround:
                    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
                    pool_3.append({'sym': sym, 'curr': curr_price, 'target': curr_price + (atr * 4.0), 'edi': edi})
            except Exception:
                continue

        # [V40 원칙: 파일 물리적 저장 후 보고 프로세스 이행]
        final_report_df = pd.DataFrame(pool_3 if pool_3 else pool_2)
        final_report_df.to_excel("V40_GLOBAL_14_FINAL_REPORT.xlsx", index=False)
        
        # --- [포인트 2] 5개 권역별 독립 온도계 산출 ---
        def get_avg(l): return sum(l)/len(l) if l else 0

        heat_report = (f"🌡️ [국가별 시장 온도계 (100% 만점)]\n"
                       f"🇰🇷 한국: {get_avg(market_heats['KR']):.1f}% (현대차/한화 등 주도주 화력)\n"
                       f"🇺🇸 미국: {get_avg(market_heats['US']):.1f}% (정점 점유율)\n"
                       f"🇯🇵 일본: {get_avg(market_heats['JP']):.1f}% (니케이 탄력)\n"
                       f"🇭🇰 홍콩: {get_avg(market_heats['HK']):.1f}% (중화권 회복세)\n"
                       f"🇪🇺 유럽: {get_avg(market_heats['EU']):.1f}% (안정적 흐름)")
        
        # --- 온도계 결과 산출 끝 ---

        # [텔레그램 풀 리포트 전송]
        t, c = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0", "198757117"
        
        # 2층 정예 및 3층 퀀텀 상세 리스트 생성
        p2_report = "\n".join([f"💎 {x['sym']}: {x['curr']:.2f} (🔋EDI: {x['edi']})" for x in sorted(pool_2, key=lambda x:x['edi'], reverse=True)[:5]])
        p3_report = "\n".join([f"🔥 {x['sym']} | EDI: {x['edi']:.1f} [글로벌 팔란티어 타격]" for x in sorted(pool_3 if pool_3 else pool_2, key=lambda x:x.get('edi',0), reverse=True)[:5]])
        
        # [추가] 왜 해외 주식이 안나왔는지 형님께 보고드리는 디버그 정보
        fail_summary = f"📉 기준미달(5%↑): {len(criteria_fail)}건\n📉 데이터누락: {len(fail_stats['Data_Empty'])}건"
        
        full_msg = (f"✅ V40 제압 리포트 ({datetime.now().strftime('%m-%d %H:%M')})\n\n"
                    f"{heat_report}\n\n"
                    f"🏰 [1층 요새] - {len(fortress_list)}개\n" + "\n".join(fortress_list[:10]) + 
                    f"\n\n🧬 [2층 정예 5선]\n{p2_report}\n\n"
                    f"🚀 [3층 퀀텀 TOP 5]\n{p3_report}\n\n{fail_summary}")
        
        requests.post(f"https://api.telegram.org/bot{t}/sendMessage", json={"chat_id": c, "text": full_msg})

        # 터미널 실시간 모니터링 출력
        print(f"\n✅ 14개국 전선 제압 완료: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(heat_report)
        print(f"🏰 [1층 요새] - {len(fortress_list)}개")
        for line in fortress_list[:15]: print(line)
        
        # 형님이 보셔야 할 탈락 상세 보고
        print(f"\n⚠️ 해외 전선 탈락 분석: 기준미달 {len(criteria_fail)}개, 수집불가 {len(fail_stats['Data_Empty'])}개")
        print(f"👉 주요 기준미달 예시: {', '.join(criteria_fail[:5])}")

    except Exception as e:
        print(f"🛑 시발 에러 발생: {e}. 로직 밀도 재검토 및 즉시 수정하겠습니다.")

if __name__ == "__main__":
    run_v40_absolute_global_14()
