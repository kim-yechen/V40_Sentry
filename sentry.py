import os
import glob
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime

# --- [V40 원칙 준수] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # 분할 전송 (혹시 모를 용량 초과 대비)
    for i in range(0, len(text), 4000):
        requests.post(url, data={"chat_id": CHAT_ID, "text": text[i:i+4000], "parse_mode": "Markdown"}, timeout=20)

def run_v40_elite_sentry():
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: return
    target_file = files[0]
    special_watch = ['SLV', 'SCCO', 'FCX']

    try:
        xls = pd.ExcelFile(target_file)
        df_fortress = pd.read_excel(xls, sheet_name=1) 
        df_new_human = pd.read_excel(xls, sheet_name=2) 
        
        all_syms = list(set(list(df_fortress['Symbol'].dropna()) + list(df_new_human['Symbol'].dropna()) + special_watch))
        raw = yf.download(all_syms, period="100d", group_by='ticker', progress=False, threads=True)
        
        report = f"🛡️ **[V40-C 정예 사격 지령]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"

        # --- [1층: 요새 긴급상황 - 위급순 정렬] ---
        emergency_list = []
        for sym in list(set(list(df_fortress['Symbol'].dropna()) + special_watch)):
            data = raw[sym]
            curr = float(data['Close'].iloc[-1])
            low_60 = data['Low'].tail(60).min()
            dist = (curr / low_60 - 1) * 100 # 마지노선까지의 거리(%)
            if dist <= 5.0:
                emergency_list.append({'sym': sym, 'curr': curr, 'low': low_60, 'dist': dist})
        
        # 가장 위험한(마지노선에 가까운) 순서대로 정렬
        emergency_list = sorted(emergency_list, key=lambda x: x['dist'])
        
        if emergency_list:
            report += "\n🏰 **[1층: 요새 긴급 수비]**\n"
            for e in emergency_list[:15]: # 너무 많으면 15개까지만
                report += f"🚨 {e['sym']}: $ {e['curr']:.2f} (마지노선까지 {e['dist']:.1f}%)\n"
        else:
            report += "\n🏰 **[1층: 요새]** 모든 전선 이상 무\n"

        # --- [2, 3층: 신인류 및 단타 정예 선별] ---
        tactical_pool = []
        for sym in df_new_human['Symbol'].dropna().unique():
            data = raw[sym]
            if data.empty: continue
            curr = float(data['Close'].iloc[-1])
            atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
            support = data['Low'].tail(60).min()
            
            core_max = support + (atr * 2.0)
            target = curr + (atr * 2.5)
            upside = ((target / curr) - 1) * 100 # 기대 수익률
            
            # 매집권 안에 있는 종목들만 후보군에 등록
            if support <= curr <= core_max:
                tactical_pool.append({
                    'sym': sym, 'curr': curr, 'target': target, 
                    'upside': upside, 'core_max': core_max
                })

        # 수익률(Upside)이 가장 높은 TOP 5만 추출
        elite_5 = sorted(tactical_pool, key=lambda x: x['upside'], reverse=True)[:5]

        if elite_5:
            report += "\n🎯 **[단타: 정예 사격 TOP 5]**\n"
            report += "`종목   | 현재가 | 목표가 | 기대수익`\n"
            for t in elite_5:
                report += f"🔥 `{t['sym']:<6} | {t['curr']:>6.2f} | {t['target']:>6.2f} | +{t['upside']:.1f}%`\n"
            
            report += "\n🧬 **[매집: 추가 기회]**\n"
            # TOP 5 제외하고 나머지 매집권 종목 중 5개만 간략히
            others = sorted(tactical_pool, key=lambda x: x['upside'], reverse=True)[5:10]
            for o in others:
                report += f"💎 {o['sym']}: $ {o['curr']:.2f} (매집상한 {o['core_max']:.1f})\n"
        else:
            report += "\n🎯 현재 사격 범위(바닥권)에 들어온 종목이 없습니다."

        # [Full Process] 저장 후 무전
        pd.DataFrame(tactical_pool).to_excel("V40_DAILY_TACTICAL.xlsx", index=False)
        send_telegram(report)

    except Exception as e:
        send_telegram(f"⚠️ 에러: {str(e)}")

if __name__ == "__main__":
    run_v40_elite_sentry()
