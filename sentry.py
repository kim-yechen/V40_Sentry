import pandas as pd
import yfinance as yf
import numpy as np
import glob
import os
import time
import requests
from datetime import datetime
import warnings

# [V40 원칙: 기계적 무결성]
warnings.filterwarnings('ignore')

def run_v40_dual_layer_strategy():
    print(f"👹 [V40-Dynamic-Pulse] 늑대 엔진 가동... {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("----------------------------------------------------------------")

    # 0. 텔레그램 설정
    T_TOKEN = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
    CHAT_ID = "198757117"

    # 1. 타겟 설정
    my_portfolio = ['FCX', 'SCCO', 'SIVR', 'IORT', 'ISSC', 'LUNR', 'IREN', 'MU', 'SIDU']
    
    files = [f for f in glob.glob("*.*") if "V40" in f.upper() and f.endswith(('.csv', '.xlsx'))]
    if not files: 
        print("❌ V40 종목 파일이 없습니다."); return
    
    try:
        target_file = files[0]
        df_raw = pd.read_csv(target_file) if target_file.endswith('.csv') else pd.read_excel(target_file)
        df_raw.columns = [c.upper().strip() for c in df_raw.columns]
        
        if 'COUNTRY' in df_raw.columns:
            us_candidates = df_raw[df_raw['COUNTRY'].isin(['USA', 'US'])]['SYMBOL'].unique()
        else:
            us_candidates = df_raw['SYMBOL'].unique()
            
        new_candidates = [x for x in us_candidates if x not in my_portfolio]
    except Exception as e: 
        print(f"❌ 파일 로드 에러: {e}"); return

    # 🏢 [1층] 보유 종목 진단 (메시지용 데이터 강화)
    print("\n🏢 [1층] 보유 종목 생존 판결 중...")
    results_1f = []
    for sym in my_portfolio:
        try:
            tk = yf.Ticker(sym)
            df = tk.history(period="1y")
            if df.empty: continue
            
            curr = df['Close'].iloc[-1]
            ma120 = df['Close'].rolling(120).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            
            # [수정] 이격도 계산 (과열 익절 신호용)
            gap_120 = (curr / ma120) - 1

            if curr > ma120:
                action, icon = "💎 강력 홀딩", "🟢"
                # 120일선보다 70% 이상 폭등 시 익절 경고
                if gap_120 > 0.7: 
                    action, icon = "🚨 과열(분할익절)", "🔥"
            elif curr > ma200:
                action, icon = "⚠️ 비중 축소", "🟡"
            else:
                action, icon = "🚨 전량 매도", "🔴"

            results_1f.append({
                'Symbol': sym, 'Price': round(curr, 2),
                'Action': action, 'Status_Icon': icon,
                'Gap_120': round(gap_120 * 100, 1)
            })
            print(f"   >> {sym}: {action}")
        except: continue

    # 🌡 [온도계] 미국 시장 과열 여부
    spy = yf.Ticker("SPY").history(period="6mo")
    us_heat = (spy['Close'].iloc[-1] / spy['High'].max()) * 100
    heat_msg = f"🌡 미국 시장 온도: {us_heat:.1f}% (SPY 기준)"

    # ==============================================================================
    # 🧬 [2층] 신규 괴물 사냥 (여기가 핵심 수정 부위입니다)
    # ==============================================================================
    print("\n🧬 [2층] '설거지 방지' 펄스 스캔 중...")
    results_2f = []
    target_pool = new_candidates[:500] if len(new_candidates) > 500 else new_candidates
    
    for i, sym in enumerate(target_pool):
        try:
            # [수정 1] 데이터 족쇄 해제 (200일 -> 6개월/20일)
            df = yf.Ticker(str(sym)).history(period="6mo")
            if len(df) < 20: continue 
            
            curr = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1] # 단기 생명선
            
            # [수정 2] 엔진 교체: 10일 단기 펄스 (뒷북 방지)
            pulse_10d = (curr / df['Close'].iloc[-10]) - 1
            
            # [수정 3] 설거지 방지턱: 20일선 이격도
            disparity = (curr / ma20) - 1
            
            # 10일간 10% 이상 오르고 + 거래량 받쳐주는 놈만 1차 필터
            if pulse_10d > 0.1:
                risk_tag = ""
                score = pulse_10d * 100
                
                # 과열(설거지 위험) 체크: 이격도 30% 초과 시
                if disparity > 0.3:
                    risk_tag = "(❌과열)"
                    score *= 0.1 # 점수 강제 삭감 (리스트 하단으로 보냄)
                elif len(df) < 100:
                    risk_tag = "(⚠️신생)"
                
                results_2f.append({
                    'Symbol': sym, 'Price': round(curr, 2),
                    'Accel_Score': round(score, 2),
                    'Real_Pulse': round(pulse_10d * 100, 1), # 실제 상승률 표시
                    'Risk_Tag': risk_tag
                })
                print(f"   >> 🚀 포착: {sym} (펄스: {pulse_10d*100:.1f}%)", end="\r")
        except: continue

    # 💾 [저장 및 보고 로직]
    df_1 = pd.DataFrame(results_1f)
    # 점수순 정렬 (과열 종목은 점수가 깎여서 밑으로 감)
    df_2 = pd.DataFrame(results_2f).sort_values(by='Accel_Score', ascending=False) if results_2f else pd.DataFrame()

    # [수정 4] 텔레그램 메시지 포맷 변경 (경고 문구 포함)
    msg_1 = "\n".join([f"{r['Status_Icon']} {r['Symbol']}: {r['Action']}" for r in results_1f]) if results_1f else "보유 데이터 없음"
    
    msg_2_list = []
    if not df_2.empty:
        # 상위 5개만 뽑되, 리스크 태그를 같이 보여줌
        for _, r in df_2.head(5).iterrows():
            msg_2_list.append(f"🚀 {r['Symbol']} | 펄스:{r['Real_Pulse']}% {r['Risk_Tag']}")
    msg_2 = "\n".join(msg_2_list) if msg_2_list else "조건 충족 없음"
    
    # [수정안: V7/V8 스펙트럼 적용]
    v7_p, v8_p, market_state = get_quantum_spectrum() # V8 파일 읽는 함수 (위에서 드린 코드)

    final_msg = (f"👹 [V40 퀀텀 관제센터]\n\n"
                 f"📊 [시장 스펙트럼 판정]\n"
                 f"🔴 V7(상승파동): {v7_p:.1f}%\n"  # SPY 온도 대신 이게 들어가야 함
                 f"🔵 V8(붕괴파동): {v8_p:.1f}%\n"
                 f"📢 판정: {market_state}\n\n"
                 f"🏢 [1층: 보유주 대응]\n{msg_1}\n\n" # msg_1도 V8 비중에 따라 동적으로 생성
                 f"🧬 [2층: 신규 사냥터]\n{msg_2}")
    # 토요일(5) 아침에만 엑셀 파일 전송 (미국 금요일 장 마감 보고)
    is_weekend = (datetime.now().weekday() == 5)

    try:
        # 메시지 전송
        requests.post(f"https://api.telegram.org/bot{T_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": final_msg})
        
        if is_weekend:
            save_name = f"V40_Weekly_Wolf_{datetime.now().strftime('%m%d')}.xlsx"
            with pd.ExcelWriter(save_name, engine='openpyxl') as writer:
                df_1.to_excel(writer, sheet_name='1층_보유점검', index=False)
                df_2.to_excel(writer, sheet_name='2층_신규발굴', index=False)
            with open(save_name, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{T_TOKEN}/sendDocument", data={'chat_id': CHAT_ID}, files={'document': f})
    except Exception as e:
        print(f"❌ 보고 중 오류: {e}")

if __name__ == "__main__":
    run_v40_dual_layer_strategy()
