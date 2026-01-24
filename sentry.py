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
    print(f"👹 [V40-DualLayer] 엔진 가동... {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("----------------------------------------------------------------")

    # 0. 텔레그램 설정
    T_TOKEN = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
    CHAT_ID = "198757117"

    # 1. 타겟 설정
    my_portfolio = ['FCX', 'SCCO', 'SLV', 'IORT', 'ISSC', 'LUNR', 'IREN', 'MU', 'BNAI', 'SIDU']
    
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

    # 🏢 [1층] 보유 종목 진단
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
            
            if curr > ma120:
                action, icon = "💎 강력 홀딩 (100%)", "🟢"
            elif curr > ma200:
                action, icon = "⚠️ 비중 축소 (50%)", "🟡"
            else:
                action, icon = "🚨 전량 매도 (Sell)", "🔴"

            results_1f.append({
                'Symbol': sym, 'Price': round(curr, 2),
                'Action': action, 'Status_Icon': icon
            })
            print(f"   >> {sym}: {action}")
        except: continue

    # 🌡 [온도계] 미국 시장 과열 여부
    spy = yf.Ticker("SPY").history(period="6mo")
    us_heat = (spy['Close'].iloc[-1] / spy['High'].max()) * 100
    heat_msg = f"🌡 미국 시장 온도: {us_heat:.1f}% (SPY 기준)"

    # 🧬 [2층] 신규 괴물 사냥
    print("\n🧬 [2층] 신규 주도주 탐색 중...")
    results_2f = []
    target_pool = new_candidates[:500] if len(new_candidates) > 500 else new_candidates
    
    for i, sym in enumerate(target_pool):
        try:
            df = yf.Ticker(str(sym)).history(period="1y")
            if len(df) < 200: continue
            
            curr = df['Close'].iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            if curr < ma200: continue
            
            mom60 = df['Close'].pct_change(60)
            accel = mom60.diff(20).iloc[-1]
            vol_ratio = df['Volume'].iloc[-20:].mean() / df['Volume'].iloc[-120:].mean()
            
            if accel > 0.05 and vol_ratio > 1.2:
                results_2f.append({
                    'Symbol': sym, 'Price': round(curr, 2),
                    'Accel_Score': round(accel * 100, 2)
                })
                print(f"   >> 🚀 발견: {sym}", end="\r")
        except: continue

    # 💾 [저장 및 보고 로직]
    df_1 = pd.DataFrame(results_1f)
    df_2 = pd.DataFrame(results_2f).sort_values(by='Accel_Score', ascending=False) if results_2f else pd.DataFrame()

    msg_1 = "\n".join([f"{r['Status_Icon']} {r['Symbol']}: {r['Action']}" for r in results_1f]) if results_1f else "보유 데이터 없음"
    msg_2 = "\n".join([f"🚀 {r['Symbol']} | 가속:{r['Accel_Score']}" for _, r in df_2.head(5).iterrows()]) if not df_2.empty else "조건 충족 없음"
    
    final_msg = (f"👹 [V40 데일리 감시]\n\n{heat_msg}\n\n"
                 f"🏢 [1층: 보유주]\n{msg_1}\n\n"
                 f"🧬 [2층: 신규 TOP 5]\n{msg_2}")

    # 토요일(5) 아침에만 엑셀 파일 전송 (미국 금요일 장 마감 보고)
    is_weekend = (datetime.now().weekday() == 5)

    try:
        # 메시지 전송
        requests.post(f"https://api.telegram.org/bot{T_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": final_msg})
        
        if is_weekend:
            save_name = f"V40_Weekly_Report_{datetime.now().strftime('%m%d')}.xlsx"
            with pd.ExcelWriter(save_name, engine='openpyxl') as writer:
                df_1.to_excel(writer, sheet_name='1층_보유점검', index=False)
                df_2.to_excel(writer, sheet_name='2층_신규발굴', index=False)
            with open(save_name, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{T_TOKEN}/sendDocument", data={'chat_id': CHAT_ID}, files={'document': f})
    except Exception as e:
        print(f"❌ 보고 중 오류: {e}")

if __name__ == "__main__":
    run_v40_dual_layer_strategy()
