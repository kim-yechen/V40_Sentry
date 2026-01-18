import os
import yfinance as yf
import pandas as pd
import requests
import time
import numpy as np
from datetime import datetime

# --- [환경 변수 설정] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def calculate_indicators(df):
    try:
        # RSI
        delta = df['Close'].diff()
        up = delta.clip(lower=0); down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rsi = 100 - (100 / (1 + (ema_up / (ema_down + 1e-10))))
        
        # MFI
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        rmf = tp * df['Volume']
        up_mf = pd.Series(0.0, index=df.index); dn_mf = pd.Series(0.0, index=df.index)
        up_mf[tp > tp.shift(1)] = rmf[tp > tp.shift(1)]
        dn_mf[tp < tp.shift(1)] = rmf[tp < tp.shift(1)]
        mfi = 100 - (100 / (1 + (up_mf.rolling(14).sum() / (dn_mf.rolling(14).sum() + 1e-10))))
        
        return rsi.iloc[-1], mfi.iloc[-1]
    except: return 50.0, 50.0

def get_v40_tactical_report():
    print("📡 [V40-C Tactical] 실시간 전술 무전 엔진 가동...")
    
    # 1. 대상 징집 (기존 엑셀 + 핵심 섹터)
    hunting_targets = ['VERO', 'IREN', 'ASTS', 'FCX', 'SCCO', 'PSLV', 'SI=F', 'COPX', 'MARA', 'CLSK']
    # 형님이 관리하시는 엑셀 파일이 있다면 추가 로드 가능
    
    market_ref = yf.download("SPY", period="20d", progress=False)['Close'].pct_change().sum()
    
    shield_a = [] # 1,050만 원 타겟
    spear_b = []  # 200만 원 타겟
    danger_c = [] # 소각 대상
    
    all_data_for_excel = []

    for symbol in hunting_targets:
        try:
            df = yf.download(symbol, period="250d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 200: continue
            
            curr_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            peak_250 = df['Close'].max()
            mdd = ((curr_price - peak_250) / peak_250) * 100
            
            rsi, mfi = calculate_indicators(df)
            energy = (mfi * 0.6) + (rsi * 0.4)
            
            # Alpha (시장 대비 강도)
            my_perf = df['Close'].tail(5).pct_change().sum()
            alpha = my_perf - market_ref
            
            # 거래대금 (유동성 체크)
            avg_vol = (df['Close'] * df['Volume']).tail(20).mean()
            
            analysis = {
                'Symbol': symbol, 'Price': curr_price, 'MDD': mdd, 
                'Energy': energy, 'Alpha': alpha, 'Vol_Avg': avg_vol
            }
            all_data_for_excel.append(analysis)

            # --- [V40-C 전술 판정 로직] ---
            
            # 1️⃣ [목돈 사격]: A-Shield (방패)
            # 조건: MDD -10% 이내 + 에너지 80점 이상 + 시장보다 강함
            if mdd >= -10 and energy >= 75 and alpha > 0:
                shield_a.append(analysis)
                
            # 2️⃣ [잉여소득]: B-Spear (창)
            # 조건: 에너지는 높으나 MDD가 -10% ~ -30% 사이 (발아 단계)
            elif -30 <= mdd < -10 and energy >= 70:
                spear_b.append(analysis)
                
            # 3️⃣ [리밸런싱]: C-Danger (소각)
            # 조건: MDD -35% 돌파 혹은 에너지 40미만 추락
            elif mdd < -35 or energy < 40:
                danger_c.append(analysis)
                
        except: continue

    # 1+1-1=Complete: 데이터 보존
    pd.DataFrame(all_data_for_excel).to_excel(f"V40C_TACTICAL_{datetime.now().strftime('%m%d')}.xlsx")

    # --- [전술 무전 발송] ---
    
    # 1. 목돈 사격 무전
    for target in shield_a[:2]: # 너무 많으면 핵심만
        msg = (f"🚨 *[V40-A: 방패 입고]*\n\n"
               f"🎯 종목: {target['Symbol']}\n"
               f"🛡️ 상태: [기관급 수급] - MDD {target['MDD']:.1f}%\n"
               f"💰 한도: *1,050만 원 (Full 사격)*\n"
               f"💬 지침: 형님, 성벽 재료입니다. 시장 대비 Alpha({target['Alpha']:.2%}) 확인. 본진 투입 적기입니다.")
        send_telegram(msg)

    # 2. 잉여소득 무전
    for target in spear_b[:2]:
        msg = (f"⚔️ *[V40-B: 창의 탄생]*\n\n"
               f"🎯 종목: {target['Symbol']}\n"
               f"🔥 성질: [신인류/발아] - 에너지 {target['Energy']:.1f}\n"
               f"💰 한도: *200만 원 (분할 매집)*\n"
               f"💬 지침: 거래량 실린 진짜 창입니다. 잉여소득으로 개수 늘려가십시오.")
        send_telegram(msg)

    # 3. 리밸런싱 경고
    if danger_c:
        msg = (f"💀 *[V40-⚠️: 리밸런싱 경고]*\n\n"
               f"❌ 대상: {', '.join([d['Symbol'] for d in danger_c[:3]])}\n"
               f"📉 상황: [소각대상] 전락 / 에너지 붕괴\n"
               f"💬 지침: 형님, 바람 빠졌습니다. 미련 없이 던지고 A(방패)로 회군하십시오.")
        send_telegram(msg)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_tactical_report()
