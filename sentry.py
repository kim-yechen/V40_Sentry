import os
import glob
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime
import time

# --- [V40 원칙 준수: 시트 인덱스 교정 및 누수 차단] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        for i in range(0, len(text), 4000):
            res = requests.post(url, data={"chat_id": CHAT_ID, "text": text[i:i+4000]}, timeout=30)
    except: pass

def run_v40_final_layered_sentry():
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: return
    target_file = files[0]
    
    special_watch = ['SLV', 'SCCO', 'FCX']

    try:
        # [핵심 교정] 시트 인덱스 0, 1, 2만 정확히 호출 (3번 호출 금지)
        xls = pd.ExcelFile(target_file)
        
        # 시트 이름이나 인덱스로 정확히 매칭 (Spear, Shield, Full Spectrum)
        df_sheet0 = pd.read_excel(xls, sheet_name=0) 
        df_sheet1 = pd.read_excel(xls, sheet_name=1) 
        df_sheet2 = pd.read_excel(xls, sheet_name=2) 
        
        # [티커 누수 차단] 모든 시트의 'Symbol' 컬럼 전수 합합
        # .KS, .T, .HK, .DE, .L, .PA 등 전 세계 티커 보존
        all_raw_syms = pd.concat([
            df_sheet0['Symbol'], 
            df_sheet1['Symbol'], 
            df_sheet2['Symbol'],
            pd.Series(special_watch)
        ]).dropna().unique()
        
        all_syms = [str(s).strip() for s in all_raw_syms]
        
        print(f"🌐 총 {len(all_syms)}개 종목 전수조사 시작... (인덱스 오류 해결 완료)")
        
        # 전 세계 데이터 정밀 다운로드
        raw = yf.download(all_syms, period="200d", group_by='ticker', progress=True, threads=True, timeout=60)
        
        report = f"🛡️ [V40-C 정예 복합 지령]\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"
        report += f"🌍 전 세계 {len(all_syms)}개 전선 정밀 스캔 완료\n"

        # --- [1층: 요새] --- (df_sheet1 기준 원본 로직)
        emergency = ""
        fortress_targets = list(set(list(df_sheet1['Symbol'].dropna().astype(str)) + special_watch))
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

        # --- [2, 3층 통합 엔진] --- (df_sheet0 기준 신인류 로직)
        human_pool = []
        tactical_pool = []
        
        for sym in df_sheet0['Symbol'].dropna().unique():
            sym = str(sym).strip()
            try:
                data = raw[sym]
                if len(data) < 130: continue
                close, vol = data['Close'], data['Volume']
                returns = close.pct_change()
                curr_price = float(close.iloc[-1])

                # [퀀텀 EDI 수식]
                v_energy = (vol.pct_change().rolling(10).std() * returns.rolling(10).std() * 10000).fillna(0)
                edi = (v_energy.rolling(120).mean() / (returns.rolling(120).std() + 1e-9)).iloc[-1]
                
                support = data['Low'].tail(60).min()
                atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
                core_max = support + (atr * 2.0)
                target = curr_price + (atr * 3.5)
                
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
        pd.DataFrame(tactical_pool).to_excel("V40_QUANTUM_FINAL.xlsx", index=False)
        send_telegram(report)
        print("✅ 오류 수정 및 전수조사 완료")

    except Exception as e:
        print(f"⚠️ 시스템 치명적 에러: {e}")

if __name__ == "__main__":
    run_v40_final_layered_sentry()
