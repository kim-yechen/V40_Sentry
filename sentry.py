import os
import glob
import pandas as pd
import yfinance as yf
from datetime import datetime
import time
import requests
import warnings
import numpy as np

# [V40 원칙: No Shortcuts & Full Compliance]
warnings.filterwarnings('ignore')

def run_v40_monster_engine_final_restore():
    """
    [V40 GLOBAL MONSTER - FULL DISCLOSURE]
    - 한국, 일본, 홍콩 전선 무누락 타격
    - 1단계+1단계-1단계 = 파일 저장 후 보고 (완결성)
    - 데이터 상식 검증 (Negative Check) 포함
    """
    start_time = time.time()
    print(f"🚀 V40 괴물 엔진 가동: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # [1단계: 파일 추적 및 강제 로딩 - 확장자 기만 돌파]
    files = [f for f in glob.glob("*.*") if "V40" in f.upper()]
    target_file = None
    for f in files:
        if f.lower().endswith(('.csv', '.xlsx', '.xls')):
            target_file = f
            break

    if not target_file:
        print("❌ [CRITICAL] V40 데이터 파일을 찾을 수 없습니다.")
        return

    try:
        # 이중 로딩 장치 (엑셀 위장 CSV 돌파)
        if target_file.lower().endswith('.csv'):
            df_raw = pd.read_csv(target_file)
        else:
            try:
                df_raw = pd.read_excel(target_file)
            except:
                df_raw = pd.read_csv(target_file)

        df_raw.columns = [c.upper().strip() for c in df_raw.columns]
        sym_col = next((c for c in df_raw.columns if c in ['SYMBOL', 'TICKER', 'CODE']), df_raw.columns[0])
        cnt_col = next((c for c in df_raw.columns if c in ['COUNTRY', 'NATION']), None)
        
    except Exception as e:
        print(f"🛑 파일 로딩 중 Contradiction 발생: {e}")
        return

    # [2단계: 전 세계 14개국 티커 표준화 엔진 - 동양 전선 특화]
    def get_global_ticker(row):
        s = str(row[sym_col]).strip().upper()
        c = str(row[cnt_col]).strip().upper() if cnt_col else "USA"
        
        if '.' in s: return s  # 이미 접미사가 있으면 통과

        # 1. 한국 (KOR) - 6자리 숫자 보정
        if c in ['KOR', 'KR']:
            s = s.zfill(6) if s.isdigit() else s
            return s + ".KS"
            
        # 2. 일본 (JPN) - 4자리 숫자 보정
        if c in ['JPN', 'JP']:
            return s + ".T"
            
        # 3. 홍콩 (HKG) - 4자리 숫자 패딩 (0700.HK 형식)
        if c in ['HK', 'HKG']:
            return s.zfill(4) + ".HK" if s.isdigit() else s + ".HK"
            
        # 4. 중국 (CHN)
        if c in ['CHN', 'CN']:
            return s + ".SS" if s.startswith('6') else s + ".SZ"

        # 5. 유럽 및 기타 (형님의 14개국 매핑 테이블)
        suffix_map = {
            "USA": "", "UK": ".L", "GB": ".L", "DE": ".DE", "EUR": ".PA", 
            "FR": ".PA", "NL": ".AS", "IT": ".MI", "CA": ".TO", "AU": ".AX", "IN": ".NS"
        }
        return f"{s}{suffix_map.get(c, '')}"

    df_raw['Yahoo_Ticker'] = df_raw.apply(get_global_ticker, axis=1)
    all_syms = df_raw['Yahoo_Ticker'].unique()
    print(f"🌍 {len(all_syms)}개 글로벌 전선(KR/JP/HK 포함) 배치 완료.")

    # [3단계: 분석 컨테이너 및 수집 로직]
    market_heats = {"US": [], "KR": [], "JP": [], "EU": [], "HK": []}
    fortress_list, pool_2, pool_3 = [], [], []
    fail_count = 0

    for idx, sym in enumerate(all_syms):
        try:
            print(f"🔎 [{idx+1}/{len(all_syms)}] {sym} 타격 중...", end="\r")
            
            # [재시도 3회 로직: 아시아 시장 생존성 확보]
            df = pd.DataFrame()
            for _ in range(3):
                try:
                    tk = yf.Ticker(sym)
                    df = tk.history(period="1y", interval="1d", auto_adjust=True)
                    if not df.empty and len(df) > 60: break
                    time.sleep(0.8)  # 야후 서버 진정용
                except: time.sleep(1.5)
            
            if df.empty:
                fail_count += 1; continue

            # [Negative Check: 데이터 상식 검증]
            curr = float(df['Close'].iloc[-1])
            if curr <= 0: continue  # 상장폐지 또는 오류 데이터 제거

            # --- [분석 알고리즘 시작] ---
            # 1. 온도계 (120일 최고점 대비 현재 위치)
            high_120 = df['High'].tail(120).max()
            heat = (curr / high_120) * 100
            
            # 국가별 온도계 분류 (동양 전선 감시)
            if ".KS" in sym: market_heats['KR'].append(heat)
            elif ".T" in sym: market_heats['JP'].append(heat)
            elif ".HK" in sym: market_heats['HK'].append(heat)
            elif any(x in sym for x in [".L", ".DE", ".PA"]): market_heats['EU'].append(heat)
            else: market_heats['US'].append(heat)

            # 2. 1층 요새 (100일 최저점 이격 5% 이내)
            low_100 = df['Low'].tail(100).min()
            dist = (curr / low_100 - 1) * 100
            if dist <= 5.0:
                fortress_list.append(f"🏰 {sym}: {curr:.2f} (이격 {dist:.1f}%)")

            # 3. EDI 에너지 (형님의 수급 공식: 20일 이동평균 추세)
            rets = df['Close'].pct_change()
            v_std = df['Volume'].pct_change().rolling(10).std()
            r_std = rets.rolling(10).std()
            edi_raw = (v_std * r_std * 1000000).fillna(0)
            edi_final = edi_raw.rolling(20).mean().iloc[-1]

            # 4. 3층 퀀텀 (흑자전환 검증)
            is_turn = False
            try:
                ni = tk.income_stmt.loc['Net Income'].dropna()
                if len(ni) >= 2 and ni.iloc[1] < 0 and ni.iloc[0] > 0: is_turn = True
            except: pass

            data_pack = {
                'sym': sym, 'curr': curr, 'edi': int(edi_final), 
                'heat': heat, 'is_turn': is_turn, 'dist': dist
            }
            
            pool_2.append(data_pack)
            if is_turn:
                atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
                data_pack['target'] = curr + (atr * 4.0)
                pool_3.append(data_pack)

            time.sleep(0.2)
        except Exception as e:
            fail_count += 1; continue

    # [4단계: V40 제 1원칙 - 파일 저장 후 보고]
    final_report_df = pd.DataFrame(pool_2)
    save_name = f"V40_GLOBAL_TOTAL_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
    final_report_df.to_excel(save_name, index=False)
    print(f"\n💾 [Complete] {save_name} 물리적 저장 완료.")

    # [5단계: 텔레그램 최종 보고]
    def get_avg(l): return sum(l)/len(l) if l else 0.0
    
    heat_msg = (f"🌡 [글로벌 온도계]\n"
                f"🇰🇷 KR: {get_avg(market_heats['KR']):.1f}% | 🇯🇵 JP: {get_avg(market_heats['JP']):.1f}%\n"
                f"🇭🇰 HK: {get_avg(market_heats['HK']):.1f}% | 🇺🇸 US: {get_avg(market_heats['US']):.1f}%\n"
                f"🇪🇺 EU: {get_avg(market_heats['EU']):.1f}%")

    top_elite = sorted(pool_2, key=lambda x: x['edi'], reverse=True)[:5]
    top_quantum = sorted(pool_3, key=lambda x: x['edi'], reverse=True)[:5]

    msg = (f"👹 V40 몬스터 리포트 ({datetime.now().strftime('%H:%M')})\n\n"
           f"{heat_msg}\n\n"
           f"🏰 [1층 요새: {len(fortress_list)}개]\n" + "\n".join(fortress_list[:8]) + 
           f"\n\n🧬 [2층 정예: EDI 수급 괴물]\n" + "\n".join([f"💎 {x['sym']} | EDI:{x['edi']:,}" for x in top_elite]) +
           f"\n\n🌌 [3층 퀀텀: 흑자전환 TOP]\n" + "\n".join([f"🚀 {x['sym']} | 🎯:{x.get('target',0):.1f}" for x in top_quantum]) +
           f"\n\n📉 분석: {len(all_syms)} | 누락: {fail_count}")

    # 텔레그램 전송
    t_token = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
    chat_id = "198757117"
    requests.post(f"https://api.telegram.org/bot{t_token}/sendMessage", json={"chat_id": chat_id, "text": msg})
    print("🎯 텔레그램 전송 완료.")

if __name__ == "__main__":
    run_v40_monster_engine_final_restore()
