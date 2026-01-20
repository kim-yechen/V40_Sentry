import os
import glob
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime
import time

# --- [V40 원칙 준수: 원본 보존 및 전 세계 확장] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        # 메시지 누락 방지를 위해 4000자씩 정밀 분할 전송
        for i in range(0, len(text), 4000):
            res = requests.post(url, data={"chat_id": CHAT_ID, "text": text[i:i+4000]}, timeout=30)
            if res.status_code != 200:
                print(f"텔레그램 전송 실패: {res.status_code}")
    except Exception as e:
        print(f"텔레그램 에러: {e}")

def run_v40_final_layered_sentry():
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: return
    target_file = files[0]
    
    # [형님 지령] 원자재 및 지수 절대 누락 금지
    special_watch = ['SLV', 'SCCO', 'FCX']

    try:
        xls = pd.ExcelFile(target_file)
        # 모든 시트 데이터 전수 로드 (1, 2, 3층 및 전체 스펙트럼 포함)
        df_fortress = pd.read_excel(xls, sheet_name=1) 
        df_new_human = pd.read_excel(xls, sheet_name=2) 
        # [추가] 엑셀의 모든 데이터를 뒤지는 시트 (전 세계 누수 방지용)
        df_full = pd.read_excel(xls, sheet_name=3) 
        
        # [핵심 수정] 엑셀의 모든 티커 + special_watch를 단 한 놈도 빠짐없이 합침
        # .KS, .KQ, .T, .HK, .DE, .L, .PA, .AS, .MI, .MA, .SW, .OL, .BR 등 전체 인식
        all_raw_syms = pd.concat([
            df_fortress['Symbol'], 
            df_new_human['Symbol'], 
            df_full['Symbol'],
            pd.Series(special_watch)
        ]).dropna().unique()
        
        all_syms = [str(s).strip() for s in all_raw_syms]
        
        print(f"🌐 총 {len(all_syms)}개 종목 전수조사 시작... (22분 이상의 정밀 스캔)")
        
        # 데이터 누락 방지를 위해 threads=True 및 타임아웃 60초 유지
        raw = yf.download(all_syms, period="200d", group_by='ticker', progress=True, threads=True, timeout=60)
        
        report = f"🛡️ [V40-C 정예 복합 지령]\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"
        report += f"🌍 전 세계 {len(all_syms)}개 전선 정밀 스캔 완료\n"

        # --- [1층: 요새] --- 형님의 원본 로직 (절대 수정 금지)
        emergency = ""
        fortress_targets = list(set(list(df_fortress['Symbol'].dropna().astype(str)) + special_watch))
        for sym in fortress_targets:
            try:
                data = raw[sym]
                if data.empty: continue
                curr = float(data['Close'].iloc[-1])
                low_60 = data['Low'].tail(60).min()
                dist = (curr / low_60 - 1) * 100
                if dist <= 5.0:
                    emergency += f"🚨 {sym}: $ {curr:.2f} ({dist:.1f}% 남음)\n"
            except: continue
        report += "\n🏰 [1층: 요새 긴급대응]\n" + (emergency if emergency else "전선 이상 무\n")

        # --- [2, 3층 통합 엔진] --- 형님의 퀀텀 수식 100% 원본 유지
        human_pool = []
        tactical_pool = []
        
        for sym in df_new_human['Symbol'].dropna().unique():
            sym = str(sym).strip()
            try:
                data = raw[sym]
                if len(data) < 130: continue
                close, vol = data['Close'], data['Volume']
                returns = close.pct_change()
                curr_price = float(close.iloc[-1])

                # [V40 전용 퀀텀 EDI 수식]
                v_energy = (vol.pct_change().rolling(10).std() * returns.rolling(10).std() * 10000).fillna(0)
                edi = (v_energy.rolling(120).mean() / (returns.rolling(120).std() + 1e-9)).iloc[-1]
                
                support = data['Low'].tail(60).min()
                atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
                core_max = support + (atr * 2.0)
                target = curr_price + (atr * 3.5)
                
                # 거래대금 필터 (50만 불 원본 유지)
                if (vol.iloc[-1] * curr_price) < 500000: continue

                if support <= curr_price <= core_max:
                    human_pool.append({'sym': sym, 'curr': curr_price, 'core': core_max, 'edi': edi})

                if edi > 400:
                    tactical_pool.append({'sym': sym, 'curr': curr_price, 'target': target, 'edi': edi, 'upside': ((target/curr_price)-1)*100})
            except: continue

        # --- [출력부: 원본 보존] ---
        if human_pool:
            report += "\n🧬 [2층: 신인류 정예 매집 5선]\n"
            for h in sorted(human_pool, key=lambda x: x['edi'], reverse=True)[:5]:
                report += f"💎 {h['sym']}: {h['curr']:.2f} (적정가 ~{h['core']:.1f} | 🔋{int(h['edi'])})\n"

        if tactical_pool:
            report += "\n🚀 [3층: 퀀텀 압착 TOP 5]\n"
            for t in sorted(tactical_pool, key=lambda x: x['edi'], reverse=True)[:5]:
                report += f"🔋 {t['sym']:<10} | {t['curr']:>8.2f} | 목표 {t['target']:>8.2f} (+{t['upside']:.1f}%)\n"

        # [Full Process Compliance] 저장 후 전송
        final_df = pd.DataFrame(tactical_pool)
        final_df.to_excel("V40_QUANTUM_FINAL.xlsx", index=False)
        
        send_telegram(report)
        print("✅ 전수조사 및 보고 완료")

    except Exception as e:
        print(f"⚠️ 시스템 치명적 에러: {e}")

if __name__ == "__main__":
    run_v40_final_layered_sentry()
