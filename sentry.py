import os
import glob
import pandas as pd
import yfinance as yf
from datetime import datetime
import time
import requests
import warnings
import numpy as np

# [V40 원칙: No Shortcuts]
warnings.filterwarnings('ignore')

def run_v40_monster_engine():
    """
    [V40 GLOBAL MONSTER VERSION]
    - 파일 확장자 기만(.xlsx로 위장한 .csv) 돌파 로직 탑재
    - 2층(EDI 정예) / 3층(흑자전환 퀀텀) 정밀 타격 및 분류 보고
    """
    start_time = time.time()
    print(f"🚀 V40 몬스터 엔진 가동: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # [1단계: 파일 추적 및 강제 로딩]
    # V40이 포함된 모든 파일을 찾는다.
    files = [f for f in glob.glob("*.*") if "V40" in f.upper()]
    target_file = None
    for f in files:
        if f.lower().endswith(('.csv', '.xlsx', '.xls')):
            target_file = f
            break

    if not target_file:
        print("❌ [CRITICAL] 파일이 없습니다. 경로를 확인하십시오.")
        return
    print(f"🎯 타격 타겟 확보: {target_file}")

    # [중요] 파일 읽기 시도 (엑셀인지 CSV인지 찔러보기)
    try:
        if target_file.lower().endswith('.csv'):
            df_raw = pd.read_csv(target_file)
        else:
            # 엑셀로 읽어보고 실패하면 CSV로 다시 읽는 이중 장치
            try:
                df_raw = pd.read_excel(target_file)
            except:
                print("⚠️ 엑셀 포맷 아님. CSV 모드로 강제 전환합니다.")
                df_raw = pd.read_csv(target_file)

        # 컬럼명 대문자화 (실수 방지)
        df_raw.columns = [c.upper().strip() for c in df_raw.columns]
        
        # 티커 컬럼 찾기 (SYMBOL 우선)
        sym_col = next((c for c in df_raw.columns if c in ['SYMBOL', 'TICKER', 'CODE']), None)
        cnt_col = next((c for c in df_raw.columns if c in ['COUNTRY', 'NATION']), None)

        if not sym_col:
            # 그래도 없으면 첫번째 컬럼을 티커로 간주
            sym_col = df_raw.columns[0]
            print(f"⚠️ 'SYMBOL' 컬럼 못 찾음. 첫 번째 컬럼 '{sym_col}'을 티커로 지정.")

        # [형님 확인용] 티커 실존 여부 출력
        first_5 = df_raw[sym_col].head(5).tolist()
        print(f"✅ 티커 확인 완료: {first_5} ... (총 {len(df_raw)}개)")
        
    except Exception as e:
        print(f"🛑 파일 로딩 대실패: {e}")
        return

    # [2단계: 14개국 전선 티커 표준화]
    def get_global_ticker(row):
        s = str(row[sym_col]).strip().upper()
        c = str(row[cnt_col]).strip().upper() if cnt_col else "USA"
        
        if '.' in s: return s # 이미 접미사 있으면 패스
        
        # 국가별 접미사 매핑 (형님 로직 + 추가 보완)
        if c == 'USA': return s
        if c in ['KOR', 'KR']: return s + ".KS" # 코스피 우선
        if c in ['JPN', 'JP']: return s + ".T"
        if c in ['HK', 'HKG']: return s + ".HK"
        if c in ['CHN', 'CN']: return s + ".SS" if s.startswith('6') else s + ".SZ"
        
        # 유럽 및 기타
        suffix_map = {
            "UK": ".L", "GB": ".L", "DE": ".DE", "EUR": ".PA", "FR": ".PA", 
            "NL": ".AS", "IT": ".MI", "CA": ".TO", "AU": ".AX", "IN": ".NS"
        }
        return f"{s}{suffix_map.get(c, '')}" # 매핑 안되면 그냥 미국장으로 간주

    df_raw['Yahoo_Ticker'] = df_raw.apply(get_global_ticker, axis=1)
    all_syms = df_raw['Yahoo_Ticker'].unique()
    print(f"🌍 전 세계 {len(all_syms)}개 전선으로 확장. 타격 개시.")

    # [3단계: 데이터 수집 및 V40 몬스터 분석]
    # 시장별 온도계
    market_heats = {"US": [], "KR": [], "JP": [], "EU": [], "HK": []}
    
    fortress_list = [] # 1층 요새
    pool_2 = []        # 2층 정예 (EDI)
    pool_3 = []        # 3층 퀀텀 (흑자전환)
    
    fail_count = 0

    for idx, sym in enumerate(all_syms):
        try:
            print(f"🔎 [{idx+1}/{len(all_syms)}] {sym} 정밀 타격 중...", end="\r")
            
            # 데이터 수집 (재시도 3회)
            df = pd.DataFrame()
            for _ in range(3):
                try:
                    tk = yf.Ticker(sym)
                    df = tk.history(period="1y", interval="1d", auto_adjust=True)
                    if not df.empty and len(df) > 100: break
                    time.sleep(0.5)
                except: time.sleep(1)
            
            if df.empty:
                fail_count += 1
                continue

            curr = float(df['Close'].iloc[-1])
            
            # --- [온도계 로직] ---
            high_120 = df['High'].tail(120).max()
            heat = (curr / high_120) * 100
            
            if ".KS" in sym: market_heats['KR'].append(heat)
            elif ".T" in sym: market_heats['JP'].append(heat)
            elif ".HK" in sym: market_heats['HK'].append(heat)
            elif any(x in sym for x in [".L", ".DE", ".PA"]): market_heats['EU'].append(heat)
            else: market_heats['US'].append(heat)
            # --------------------

            # [1층 요새] 5% 지지선
            low_100 = df['Low'].tail(100).min()
            dist = (curr / low_100 - 1) * 100
            if dist <= 5.0:
                fortress_list.append(f"🚨 {sym}: {curr:.2f} (이격 {dist:.1f}%)")

            # [2층/3층 분석 공통: EDI 산출]
            # EDI = (거래량변동성 * 수익률변동성 * 가중치) / (수익률변동성 보정)
            rets = df['Close'].pct_change()
            v_std = df['Volume'].pct_change().rolling(10).std()
            r_std = rets.rolling(10).std()
            
            # 형님의 EDI 공식 적용
            edi_raw = (v_std * r_std * 1000000).fillna(0)
            edi_final = edi_raw.rolling(20).mean().iloc[-1] # 최근 추세 반영
            
            # [재무 체크: 흑자전환 여부]
            is_turn = False
            try:
                ni = yf.Ticker(sym).income_stmt.loc['Net Income'].dropna()
                if len(ni) >= 2 and ni.iloc[1] < 0 and ni.iloc[0] > 0: is_turn = True
            except: pass

            # 데이터 패키징
            data_pack = {
                'sym': sym, 
                'curr': curr, 
                'edi': int(edi_final), 
                'is_turn': is_turn
            }

            pool_2.append(data_pack) # 일단 2층 후보에 다 넣고 나중에 정렬

            if is_turn:
                # 3층 퀀텀: 흑자전환 종목은 목표가(ATR * 4) 산출하여 별도 관리
                atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
                data_pack['target'] = curr + (atr * 4.0)
                pool_3.append(data_pack)

            time.sleep(0.2) # 야후 형님들 화나지 않게 딜레이

        except Exception as e:
            fail_count += 1
            continue

    # [4단계: 결과 정렬 및 저장]
    # 2층 정예: EDI 높은 순서
    top_elite = sorted(pool_2, key=lambda x: x['edi'], reverse=True)[:5]
    
    # 3층 퀀텀: 흑자전환 중 EDI 높은 순서
    top_quantum = sorted(pool_3, key=lambda x: x['edi'], reverse=True)[:5]

    # 엑셀 저장 (형님의 명령: 저장 먼저)
    final_df = pd.DataFrame(pool_3 if pool_3 else pool_2)
    final_df.to_excel("V40_GLOBAL_MONSTER_REPORT.xlsx", index=False)
    print("\n💾 데이터/로직/저장 완료: V40_GLOBAL_MONSTER_REPORT.xlsx")

    # [5단계: 텔레그램 리포팅]
    def get_avg(l): return sum(l)/len(l) if l else 0
    
    heat_msg = (f"🌡 [글로벌 온도계]\n"
                f"🇺🇸 US: {get_avg(market_heats['US']):.1f}% | 🇰🇷 KR: {get_avg(market_heats['KR']):.1f}%\n"
                f"🇯🇵 JP: {get_avg(market_heats['JP']):.1f}% | 🇪🇺 EU: {get_avg(market_heats['EU']):.1f}%")

    # 2층 보고 텍스트
    p2_txt = "\n".join([f"💎 {x['sym']} | EDI:{x['edi']:,}" for x in top_elite])
    
    # 3층 보고 텍스트
    p3_txt = "\n".join([f"🚀 {x['sym']} | 🎯목표:{x['target']:.1f} | 턴어라운드" for x in top_quantum])

    msg = (f"👹 V40 괴물 리포트 ({datetime.now().strftime('%H:%M')})\n\n"
           f"{heat_msg}\n\n"
           f"🏰 [1층 요새: {len(fortress_list)}개]\n" + "\n".join(fortress_list[:7]) + 
           f"\n...\n\n🧬 [2층 정예 5선: 수급 괴물]\n{p2_txt}\n\n"
           f"🌌 [3층 퀀텀 TOP 5: 흑자전환]\n{p3_txt}\n\n"
           f"📉 분석종료: {len(all_syms)}개 | 실패: {fail_count}개")

    # 전송
    t_token = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
    chat_id = "198757117"
    
    try:
        requests.post(f"https://api.telegram.org/bot{t_token}/sendMessage", 
                      json={"chat_id": chat_id, "text": msg})
        print("🎯 텔레그램 전송 완료.")
    except Exception as e:
        print(f"🛑 텔레그램 전송 실패: {e}")

if __name__ == "__main__":
    run_v40_monster_engine()
