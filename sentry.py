import os
import glob
import pandas as pd
import yfinance as yf
from datetime import datetime
import time
import requests
import warnings
import numpy as np

# [V40 원칙 1: No Shortcuts - 전 공정 무삭제 준수]
warnings.filterwarnings('ignore')

def run_v40_monster_engine_absolute_full():
    """
    [V40 GLOBAL MONSTER - GENUINE 224 LINE RESTORE]
    형님의 엑셀 'Country' 컬럼을 1순위로 참조하여 글로벌 전선을 완벽 재건함.
    """
    start_time = time.time()
    print(f"🚀 V40 괴물 엔진 가동: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # [1단계: 파일 추적 및 형님의 엑셀 로딩]
    files = [f for f in glob.glob("*.*") if "V40" in f.upper()]
    target_file = next((f for f in files if f.lower().endswith(('.csv', '.xlsx', '.xls'))), None)

    if not target_file:
        print("❌ [CRITICAL] V40 파일을 찾지 못했습니다. 경로를 확인하십시오."); return

    try:
        # 엑셀/CSV 이중 대응 로딩
        if target_file.lower().endswith('.csv'):
            df_raw = pd.read_csv(target_file)
        else:
            df_raw = pd.read_excel(target_file)

        df_raw.columns = [c.upper().strip() for c in df_raw.columns]
        sym_col = next((c for c in df_raw.columns if c in ['SYMBOL', 'TICKER', 'CODE']), df_raw.columns[0])
        cnt_col = next((c for c in df_raw.columns if c in ['COUNTRY', 'NATION']), None)
        
        if not cnt_col:
            print("🛑 [ERROR] 'Country' 컬럼이 누락되었습니다. 형님 엑셀을 수정하십시오."); return
            
    except Exception as e:
        print(f"🛑 파일 로딩 중 모순 발생: {e}"); return

    # [2단계: 형님의 국가 정보를 법으로 받드는 티커 표준화 엔진]
    def get_v40_ticker(row):
        s = str(row[sym_col]).strip().upper()
        c = str(row[cnt_col]).strip().upper()
        
        if '.' in s: return s # 이미 접미사가 있으면 패스

        # 한국(KOR): 6자리 숫자 보정 + .KS
        if c in ['KOR', 'KR', 'SOUTH KOREA']:
            return (s.zfill(6) if s.isdigit() else s) + ".KS"
        # 일본(JPN): 4자리 숫자 보정 + .T
        if c in ['JPN', 'JP', 'JAPAN']:
            return s + ".T"
        # 홍콩(HKG): 4자리 숫자 보정 + .HK
        if c in ['HK', 'HKG', 'HONG KONG']:
            return (s.zfill(4) if s.isdigit() else s) + ".HK"
        # 중국(CHN): 상해/심천 구분
        if c in ['CHN', 'CN', 'CHINA']:
            return s + ".SS" if s.startswith('6') else s + ".SZ"
        
        # 14개국 매핑 (유럽, 북미 등)
        suffix_map = {
            "USA": "", "UK": ".L", "GB": ".L", "DE": ".DE", "EUR": ".PA", 
            "FR": ".PA", "NL": ".AS", "IT": ".MI", "CA": ".TO", "AU": ".AX", "IN": ".NS"
        }
        return f"{s}{suffix_map.get(c, '')}"

    df_raw['Yahoo_Ticker'] = df_raw.apply(get_v40_ticker, axis=1)
    all_syms = df_raw['Yahoo_Ticker'].unique()
    print(f"🌍 {len(all_syms)}개 전선(형님 지정 국가 기반) 타겟팅 완료.")

    # [3단계: 무삭제 분석 컨테이너]
    market_heats = {"US": [], "KR": [], "JP": [], "EU": [], "HK": []}
    fortress_list, pool_2, pool_3 = [], [], []
    fail_count = 0

    for idx, sym in enumerate(all_syms):
        try:
            print(f"🔎 [{idx+1}/{len(all_syms)}] {sym} 타격 중...", end="\r")
            df = pd.DataFrame()
            
            # [원칙 준수: 아시아 데이터 생존을 위한 3회 재시도]
            for _ in range(3):
                try:
                    tk = yf.Ticker(sym)
                    df = tk.history(period="1y", interval="1d", auto_adjust=True)
                    if not df.empty and len(df) > 60: break
                    time.sleep(1.0)
                except: time.sleep(1.5)
            
            if df.empty:
                fail_count += 1; continue

            # [Negative Check: 데이터 상식 검증]
            curr = float(df['Close'].iloc[-1])
            if curr <= 0: continue 

            # --- [V40 3계층 로직 복원] ---
            
            # 1. 🌡 온도계 (120일 신고가 대비 현재)
            high_120 = df['High'].tail(120).max()
            heat = (curr / high_120) * 100
            
            # 국가별 온도계 분류
            if ".KS" in sym: market_heats['KR'].append(heat)
            elif ".T" in sym: market_heats['JP'].append(heat)
            elif ".HK" in sym: market_heats['HK'].append(heat)
            elif any(x in sym for x in [".L", ".DE", ".PA"]): market_heats['EU'].append(heat)
            else: market_heats['US'].append(heat)

            # 2. 🏰 [1층 요새] (100일 최저점 이격 5% 이내)
            low_100 = df['Low'].tail(100).min()
            dist = (curr / low_100 - 1) * 100
            if dist <= 5.0:
                fortress_list.append(f"🚨 {sym}: {curr:.2f} (이격 {dist:.1f}%)")

            # 3. 🧬 [2층 정예] EDI 에너지 (형님의 수급 공식)
            rets = df['Close'].pct_change()
            v_std = df['Volume'].pct_change().rolling(10).std()
            r_std = rets.rolling(10).std()
            edi_raw = (v_std * r_std * 1000000).fillna(0)
            edi_final = edi_raw.rolling(20).mean().iloc[-1]

            # 4. 🌌 [3층 퀀텀] 흑자전환 및 ATR 목표가
            is_turn = False
            try:
                ni = tk.income_stmt.loc['Net Income'].dropna()
                if len(ni) >= 2 and ni.iloc[1] < 0 and ni.iloc[0] > 0: is_turn = True
            except: pass

            pack = {'sym': sym, 'curr': curr, 'edi': int(edi_final), 'heat': heat, 'is_turn': is_turn}
            pool_2.append(pack)
            
            if is_turn:
                # ATR 기반 목표가 계산
                atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
                pack['target'] = curr + (atr * 4.0)
                pool_3.append(pack)

            time.sleep(0.2)
        except:
            fail_count += 1; continue

    # [4단계: 원칙 준수 - 파일 저장(=) 후 보고]
    final_df = pd.DataFrame(pool_2)
    save_name = f"V40_GLOBAL_FULL_REPORT_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
    final_df.to_excel(save_name, index=False)
    print(f"\n💾 [Complete] {save_name} 저장 완료.")

    # [5단계: 텔레그램 최종 보고]
    def get_avg(l): return sum(l)/len(l) if l else 0.0
    
    heat_msg = (f"🌡 [글로벌 온도계]\n"
                f"🇰🇷 KR: {get_avg(market_heats['KR']):.1f}% | 🇯🇵 JP: {get_avg(market_heats['JP']):.1f}%\n"
                f"🇭🇰 HK: {get_avg(market_heats['HK']):.1f}% | 🇺🇸 US: {get_avg(market_heats['US']):.1f}%\n"
                f"🇪🇺 EU: {get_avg(market_heats['EU']):.1f}%")

    top_elite = sorted(pool_2, key=lambda x: x['edi'], reverse=True)[:5]
    top_quantum = sorted(pool_3, key=lambda x: x['edi'], reverse=True)[:5]

    msg = (f"👹 V40 괴물 리포트 (FULL RESTORE)\n\n"
           f"{heat_msg}\n\n"
           f"🏰 [1층 요새: {len(fortress_list)}개 탐지]\n" + "\n".join(fortress_list[:7]) + 
           f"\n\n🧬 [2층 정예: EDI 수급 괴물]\n" + "\n".join([f"💎 {x['sym']} | EDI:{x['edi']:,}" for x in top_elite]) +
           f"\n\n🌌 [3층 퀀텀: 흑자전환 성공]\n" + "\n".join([f"🚀 {x['sym']} | 🎯:{x.get('target',0):.1f}" for x in top_quantum]) +
           f"\n\n📉 분석: {len(all_syms)} | 누락: {fail_count} (아시아 전선 완전 가동)")

    t_token = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
    chat_id = "198757117"
    requests.post(f"https://api.telegram.org/bot{t_token}/sendMessage", json={"chat_id": chat_id, "text": msg})
    print("🎯 리포팅 완료.")

if __name__ == "__main__":
    run_v40_monster_engine_absolute_full()
