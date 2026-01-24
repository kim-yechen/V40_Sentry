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
    print(f"👹 [V40-DualLayer] 내 계좌 정밀 타격 엔진 가동... {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("----------------------------------------------------------------")

    # 0. 텔레그램 설정 (형님 토큰 그대로 유지)
    T_TOKEN = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
    CHAT_ID = "198757117"

    # 1. 타겟 설정
    # [1층] 형님의 보유 종목 (수성 대상)
    my_portfolio = ['FCX', 'SCCO', 'SLV', 'IORT', 'ISSC', 'LUNR', 'IREN', 'MU', 'BNAI', 'SIDU']
    
    # [2층] 신규 발굴 대상 로딩 (V40 파일)
    files = [f for f in glob.glob("*.*") if "V40" in f.upper() and f.endswith(('.csv', '.xlsx'))]
    if not files: 
        print("❌ V40 종목 파일이 없습니다. (2층 탐색 불가)"); return
    
    try:
        target_file = files[0]
        df_raw = pd.read_csv(target_file) if target_file.endswith('.csv') else pd.read_excel(target_file)
        df_raw.columns = [c.upper().strip() for c in df_raw.columns]
        
        # 미국 주식만 필터링 (US 온도계용)
        # 'Country' 컬럼이 있으면 활용, 없으면 티커 형태로 추정
        if 'COUNTRY' in df_raw.columns:
            us_candidates = df_raw[df_raw['COUNTRY'].isin(['USA', 'US'])]['SYMBOL'].unique()
        else:
            us_candidates = df_raw['SYMBOL'].unique() # 없을 땐 전체
            
        # 내 종목은 신규 발굴에서 제외
        new_candidates = [x for x in us_candidates if x not in my_portfolio]
        
    except Exception as e: print(f"❌ 파일 로드 에러: {e}"); return

    # ==============================================================================
    # 🏢 [1층] 보유 종목 정밀 진단 (Hold vs Sell 판결)
    # ==============================================================================
    print("\n🏢 [1층] 보유 종목(10선) 생존 여부 판결 중...")
    results_1f = []
    
    for sym in my_portfolio:
        try:
            tk = yf.Ticker(sym)
            df = tk.history(period="1y")
            
            if df.empty: continue
            
            curr = df['Close'].iloc[-1]
            ma120 = df['Close'].rolling(120).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            
            # [전술 로직] 이평선 위치에 따른 행동 강령
            action = ""
            status_color = ""
            
            if curr > ma120:
                action = "💎 강력 홀딩 (100%)"
                detail = "추세 완벽함"
                status_color = "🟢"
            elif curr > ma200:
                action = "⚠️ 비중 축소 (50% 유지)"
                detail = "120선 붕괴 (경고)"
                status_color = "🟡"
            else:
                action = "🚨 전량 매도 (Sell All)"
                detail = "200선(생명선) 붕괴"
                status_color = "🔴"

            # 거리 계산 (%)
            dist_120 = ((curr - ma120) / ma120) * 100
            
            results_1f.append({
                'Symbol': sym, 
                'Price': round(curr, 2),
                'Action': action,
                'Detail': detail,
                'Dist_120': round(dist_120, 2),
                'Status_Icon': status_color
            })
            print(f"   >> {sym}: {action}")
        except: continue

    # ==============================================================================
    # 🌡 [온도계] 미국 시장 과열 여부 (S&P500 ETF 'SPY' 기준)
    # ==============================================================================
    spy = yf.Ticker("SPY").history(period="6mo")
    spy_curr = spy['Close'].iloc[-1]
    spy_high = spy['High'].max()
    us_heat = (spy_curr / spy_high) * 100
    heat_msg = f"🌡 미국 시장 온도: {us_heat:.1f}% (SPY 기준)"

    # ==============================================================================
    # 🧬 [2층] 신규 괴물 사냥 (Price > 200MA + 60일 가속도 폭발)
    # ==============================================================================
    print("\n🧬 [2층] 새로운 주도주(Ten-Bagger) 탐색 중... (약 2~3분 소요)")
    results_2f = []
    
    # 시간 관계상 후보군 중 무작위 or 상위 500개만 샘플링 (전수조사 원하시면 슬라이싱 제거)
    target_pool = new_candidates if len(new_candidates) < 500 else new_candidates[:500] 
    
    for i, sym in enumerate(target_pool):
        if i % 50 == 0: time.sleep(1)
        try:
            df = yf.Ticker(str(sym)).history(period="1y")
            if len(df) < 200: continue
            
            curr = df['Close'].iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            
            # 필터 1: 200일선 위에 있는가? (기본 자격)
            if curr < ma200: continue
            
            # 필터 2: 60일 가속도 (3개월 추세 에너지)
            mom60 = df['Close'].pct_change(60)
            accel = mom60.diff(20).iloc[-1] # 가속도
            
            # 필터 3: 거래량 질량 (최근 거래량이 평소보다 많은가)
            vol_ratio = df['Volume'].iloc[-20:].mean() / df['Volume'].iloc[-120:].mean()
            
            if accel > 0.05 and vol_ratio > 1.2: # 가속도 붙고 거래량 터진 놈
                results_2f.append({
                    'Symbol': sym,
                    'Price': round(curr, 2),
                    'Accel_Score': round(accel * 100, 2),
                    'Vol_Ratio': round(vol_ratio, 2)
                })
                print(f"   >> 🚀 발견: {sym} (가속도: {accel:.2f})", end="\r")
        except: continue
            except Exception:
            continue
                
    # --------------------------------------------------------------------------
    # 여기서부터는 for 문 밖입니다 (모든 종목 검사 완료 후)
    # --------------------------------------------------------------------------

    # 1. 데이터프레임 생성 (에러 방지용)
    df_1 = pd.DataFrame(results_1f)
    df_2 = pd.DataFrame(results_2f)
    if not df_2.empty:
        df_2 = df_2.sort_values(by='Accel_Score', ascending=False)

    # 2. 메시지 구성 (평일/주말 공통)
    msg_1 = "\n".join([f"{r['Status_Icon']} {r['Symbol']}: {r['Action']}" for r in results_1f]) if results_1f else "보유 종목 없음"
    # df_2.head(5)를 사용하여 상위 5개만 메시지에 포함
    msg_2 = "\n".join([f"🚀 {r['Symbol']} | 가속:{r['Accel_Score']}" for _, r in df_2.head(5).iterrows()]) if not df_2.empty else "조건 충족 없음"
    
    final_msg = (f"👹 [V40 데일리 감시]\n\n"
                 f"{heat_msg}\n\n"
                 f"🏢 [1층: 내 종목 생존여부]\n{msg_1}\n\n"
                 f"🧬 [2층: 신규 괴물 TOP 5]\n{msg_2}\n\n"
                 f"💡 평일에는 '생존'만 확인하십시오. 전략은 주말에 짭니다.")

    # 3. 요일 확인 (5가 토요일)
    is_weekend = (datetime.now().weekday() == 5)

    try:
        # 공통: 텔레그램 텍스트 발송
        requests.post(f"https://api.telegram.org/bot{T_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": final_msg})

        # 토요일에만 파일 생성 및 발송
        if is_weekend:
            save_name = f"V40_Weekly_DeepScan_{datetime.now().strftime('%m%d')}.xlsx"
            with pd.ExcelWriter(save_name, engine='openpyxl') as writer:
                df_1.to_excel(writer, sheet_name='1층_보유점검', index=False)
                df_2.to_excel(writer, sheet_name='2층_신규발굴', index=False)
            
            with open(save_name, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{T_TOKEN}/sendDocument", 
                              data={'chat_id': CHAT_ID}, files={'document': f})
            print("📡 토요일 정밀 분석 파일 발송 완료.")
        else:
            print("📲 평일 요약 보고 완료.")

    except Exception as e:
        print(f"❌ 보고 중 오류 발생: {e}")

# (이 부분은 파일의 가장 끝, 들여쓰기 없음)
if __name__ == "__main__":
    run_v40_dual_layer_strategy()
