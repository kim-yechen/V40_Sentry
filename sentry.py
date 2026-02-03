import pandas as pd
import yfinance as yf
import numpy as np
import glob
import os
import requests
from datetime import datetime
import warnings

# [V40 원칙: 기계적 무결성]
warnings.filterwarnings('ignore')

# ---------------------------------------------------------
# [신규 추가] V8 스펙트럼 분석 함수 (안 되던 부분)
# ---------------------------------------------------------
def get_quantum_spectrum():
    v8_file = "KIM_DIRECTOR_V8_RECESSION_ALERT.xlsx"
    try:
        if v8_file.endswith('.csv'):
            df_v8 = pd.read_csv(v8_file)
        else:
            df_v8 = pd.read_excel(v8_file)
            
        latest = df_v8.iloc[-1]
        v8_p = float(latest['Recommended_Cash_Ratio'])
        v7_p = 100.0 - v8_p
        
        if v8_p >= 60: state = "🥶 V8 빙하기 (현금확보)"
        elif v8_p >= 35: state = "☁️ 경계 구간 (선별접근)"
        else: state = "🔥 V7 불장 (풀매수)"
        return v7_p, v8_p, state
    except Exception as e:
        print(f"⚠️ V8 파일 분석 실패(중립 판정): {e}")
        return 50.0, 50.0, "⚖️ 중립 (데이터 연결 확인 필요)"

def run_v40_dual_layer_strategy():
    print(f"👹 [V40-Dynamic-Pulse] 늑대 엔진 가동... {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("----------------------------------------------------------------")

    # 1. 스펙트럼 측정 (파동 붕괴)
    v7_p, v8_p, market_state = get_quantum_spectrum()

    # 0. 텔레그램 설정
    T_TOKEN = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
    CHAT_ID = "198757117"

    # 1. 타겟 설정 (잘되던 부분 유지)
    my_portfolio = ['FCX', 'SCCO', 'SIVR', 'IORT', 'ISSC', 'LUNR', 'IREN', 'MU', 'SIDU']
    files = [f for f in glob.glob("*.*") if "V40" in f.upper() and f.endswith(('.csv', '.xlsx'))]
    if not files: 
        print("❌ V40 종목 파일이 없습니다."); return
    
    try:
        target_file = files[0]
        df_raw = pd.read_csv(target_file) if target_file.endswith('.csv') else pd.read_excel(target_file)
        df_raw.columns = [c.upper().strip() for c in df_raw.columns]
        us_candidates = df_raw['SYMBOL'].unique() if 'SYMBOL' in df_raw.columns else df_raw['TICKER'].unique()
        new_candidates = [x for x in us_candidates if x not in my_portfolio]
    except Exception as e: 
        print(f"❌ 파일 로드 에러: {e}"); return

    # 🏢 [1층] 보유 종목 진단 (V8 수치에 따른 동적 변환 적용)
    print("\n🏢 [1층] 보유 종목 생존 판결 중...")
    results_1f = []
    # V8 위험도에 따라 익절 기준(이격도)을 타이트하게 조절
    # V8이 0일 때 70%, V8이 50일 때 45%에서 익절 신호 발생
    dynamic_limit = 0.7 - (v8_p * 0.005) 

    for sym in my_portfolio:
        try:
            tk = yf.Ticker(sym)
            df = tk.history(period="1y")
            if df.empty: continue
            
            curr = df['Close'].iloc[-1]
            ma120 = df['Close'].rolling(120).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            gap_120 = (curr / ma120) - 1

            if curr > ma120:
                if gap_120 > dynamic_limit:
                    action, icon = f"🚨 과열(비중 {int(v8_p)}% 축소)", "🔥"
                else:
                    action, icon = "💎 강력 홀딩", "🟢"
            elif curr > ma200:
                action, icon = "⚠️ 비중 축소", "🟡"
            else:
                action, icon = "🚨 전량 매도", "🔴"

            results_1f.append({'Symbol': sym, 'Action': action, 'Status_Icon': icon})
        except: continue

    # 🧬 [2층] 신규 괴물 사냥 (잘되던 펄스 로직 유지)
    print("\n🧬 [2층] '설거지 방지' 펄스 스캔 중...")
    results_2f = []
    target_pool = new_candidates[:300] # 속도를 위해 300개로 제한
    
    for sym in target_pool:
        try:
            df = yf.Ticker(str(sym)).history(period="6mo")
            if len(df) < 20: continue 
            curr = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            pulse_10d = (curr / df['Close'].iloc[-10]) - 1
            disparity = (curr / ma20) - 1
            
            if pulse_10d > 0.1:
                risk_tag = ""
                score = pulse_10d * 100
                if disparity > 0.3:
                    risk_tag = "(❌과열)"
                    score *= 0.1 
                
                results_2f.append({'Symbol': sym, 'Accel_Score': score, 'Pulse': pulse_10d*100, 'Tag': risk_tag})
        except: continue

    # 💾 [저장 및 메시지 구성]
    df_2 = pd.DataFrame(results_2f).sort_values(by='Accel_Score', ascending=False) if results_2f else pd.DataFrame()
    
    msg_1 = "\n".join([f"{r['Status_Icon']} {r['Symbol']}: {r['Action']}" for r in results_1f])
    
    # 2층 필터링: V8이 높으면 아예 추천을 줄임
    top_n = 3 if v8_p > 40 else 5
    msg_2 = "\n".join([f"🚀 {r['Symbol']} | 펄스:{r['Pulse']:.1f}% {r['Tag']}" for _, r in df_2.head(top_n).iterrows()])

    # [수정된 템플릿] 관성적인 SPY 온도계를 버리고 스펙트럼 주입
    final_msg = (f"👹 [V40 퀀텀 관제센터]\n\n"
                 f"📊 [시장 스펙트럼 판정]\n"
                 f"🔴 V7(상승파동): {v7_p:.1f}%\n"
                 f"🔵 V8(붕괴파동): {v8_p:.1f}%\n"
                 f"📢 판정: {market_state}\n\n"
                 f"🏢 [1층: 보유주 대응]\n{msg_1}\n\n"
                 f"🧬 [2층: 신규 사냥터]\n{msg_2}")

    # 발송 로직
    requests.post(f"https://api.telegram.org/bot{T_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": final_msg})

if __name__ == "__main__":
    run_v40_dual_layer_strategy()
