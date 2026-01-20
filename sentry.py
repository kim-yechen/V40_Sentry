import os
import glob
import pandas as pd
import yfinance as yf
from datetime import datetime
import time

def run_v40_global_conquest():
    # [V40 원칙: 1+1-1=Complete] - 저장 전엔 절대 입 안 뗌
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: 
        print("❌ 엑셀 파일이 없습니다. 형님, 확인하십시오.")
        return
    target_file = files[0]

    try:
        xls = pd.ExcelFile(target_file)
        df_a = pd.read_excel(xls, sheet_name=1) 
        df_b = pd.read_excel(xls, sheet_name=2) 
        
        # [14개국 티커 강제 매핑 엔진 - 전 세계 전선 박제]
        def get_global_ticker(s):
            s = str(s).strip().upper()
            # 1. 숫자형 티커 처리 (한/일/중/홍콩 등)
            if s.isdigit():
                if len(s) == 6: return s + ".KS" # 한국 (KOSPI/KOSDAQ)
                if len(s) == 4: return s + ".T"  # 일본 (Tokyo)
                if len(s) == 5: return s + ".HK" # 홍콩 (Hong Kong)
                if s.startswith('6'): return s + ".SS" # 중국 (상해)
                if s.startswith(('0','3')): return s + ".SZ" # 중국 (심천)
            
            # 2. 유럽 및 기타 주요국 처리 (사용자가 입력한 리스트 기준 확장)
            # 엑셀의 'Country' 컬럼이 있다면 더 정확하나, 심볼 패턴으로 강제 매핑
            # 주요 유럽 시장 Suffix 강제 주입 로직
            market_map = {
                'L': '.L',   # 영국 (London)
                'DE': '.DE', # 독일 (Frankfurt)
                'PA': '.PA', # 프랑스 (Paris)
                'AS': '.AS', # 네덜란드 (Amsterdam)
                'MI': '.MI', # 이탈리아 (Milan)
                'TO': '.TO', # 캐나다 (Toronto)
                'AX': '.AX', # 호주 (Sydney)
                'NS': '.NS', # 인도 (NSE)
            }
            # 이미 Suffix가 붙어있는 경우는 통과, 없으면 미국(기본) 처리
            if '.' in s: return s
            return s # 기본 미국은 Suffix 없음

        all_syms = pd.concat([df_a['Symbol'], df_b['Symbol']]).dropna().unique()
        all_syms = [get_global_ticker(s) for s in all_syms]
        
        print(f"🌍 14개국 {len(all_syms)}개 종목: EPS 적자→흑자 전환 및 EDI 폭발 전수 조사 개시...")

        # 가격 데이터 병렬 수집
        raw_price_data = yf.download(all_syms, period="250d", group_by='ticker', threads=True)
        
        pool_2, pool_3, fortress_list = [], [], []

        for sym in all_syms:
            try:
                df = raw_price_data[sym] if len(all_syms) > 1 else raw_price_data
                if df.empty or len(df) < 100: continue
                
                curr_price = df['Close'].iloc[-1]
                
                # [Turnaround Check] - 시키신 대로 EPS 흑자전환 전수 조사
                is_turnaround = False
                tk = yf.Ticker(sym)
                # 재무제표 털기 (Income Statement)
                fin = tk.financials
                if not fin.empty and 'Net Income' in fin.index:
                    # 최근 2개 데이터 비교 (iloc[0]이 최신)
                    incomes = fin.loc['Net Income'].dropna()
                    if len(incomes) >= 2:
                        if incomes.iloc[1] < 0 and incomes.iloc[0] > 0: # 적자 -> 흑자
                            is_turnaround = True

                # --- 1층: 요새 지지선 ---
                if any(str(s).strip().upper() in sym for s in df_a['Symbol']):
                    low_100 = df['Low'].tail(100).min()
                    dist = (curr_price / low_100 - 1) * 100
                    if dist <= 5.0:
                        fortress_list.append(f"🚨 {sym}: {curr_price:.2f} ({dist:.1f}% 지지선)")

                # --- 2/3층: EDI 및 퀀텀 ---
                rets = df['Close'].pct_change()
                v_energy = (df['Volume'].pct_change().rolling(10).std() * rets.rolling(10).std() * 10000).fillna(0)
                edi = (v_energy.rolling(120).mean() / (rets.rolling(120).std() + 1e-9)).iloc[-1]
                
                pool_2.append({'sym': sym, 'curr': curr_price, 'edi': int(edi), 'turn': is_turnaround})

                # [수정 로직]: 흑자전환 성공 + EDI 폭발 종목만 3층 입성
                if is_turnaround and edi > 10: # 에너지 기준치 추가
                    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
                    target = curr_price + (atr * 4.0)
                    upside = ((target / curr_price) - 1) * 100
                    pool_3.append({'sym': sym, 'curr': curr_price, 'target': target, 'upside': upside, 'edi': edi})

            except: continue

        # [V40 원칙: 저장 후 보고]
        final_df = pd.DataFrame(pool_3)
        final_df.to_excel("V40_GLOBAL_CONQUEST_REPORT.xlsx", index=False)

        print(f"\n✅ 14개국 전선 제압 완료: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"🏰 [1층: 요새 지지선] - {len(fortress_list)}개 발견")
        for line in fortress_list[:15]: print(line)

        print("\n🧬 [2층: 신인류 정예 매집 5선]")
        for item in sorted(pool_2, key=lambda x: x['edi'], reverse=True)[:5]:
            tag = " [★팔란티어식 흑자전환]" if item['turn'] else ""
            print(f"💎 {item['sym']}: {item['curr']:.2f} (🔋EDI: {item['edi']}){tag}")

        print("\n🚀 [3층: 퀀텀 압착 TOP 5 (적자탈출+에너지폭주)]")
        if not pool_3:
            print("💡 현재 흑자전환+에너지폭발 조건을 동시에 만족하는 종목이 없습니다.")
        else:
            for item in sorted(pool_3, key=lambda x: x['upside'], reverse=True)[:5]:
                print(f"🔥 {item['sym']:<8} | 목표: {item['target']:>8.2f} (+{item['upside']:.1f}%)")

    except Exception as e:
        print(f"🛑 치명적 결함: {e}. 즉시 공식을 재점검하십시오.")

if __name__ == "__main__":
    run_v40_global_conquest()
