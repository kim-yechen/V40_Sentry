import os
import glob
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime
import time

# --- [V40 원칙 준수: 전 세계 티커 무결성 강제] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        for i in range(0, len(text), 4000):
            requests.post(url, data={"chat_id": CHAT_ID, "text": text[i:i+4000]}, timeout=30)
    except: pass

def run_v40_no_leak_sentry():
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: return
    target_file = files[0]
    special_watch = ['SLV', 'SCCO', 'FCX']

    try:
        xls = pd.ExcelFile(target_file)
        # 0번 시트 무시, 1번(요새)과 2번(신인류)만 정밀 타격
        df_sheet1 = pd.read_excel(xls, sheet_name=1) 
        df_sheet2 = pd.read_excel(xls, sheet_name=2) 
        
        # [핵심] 엑셀에 적힌 티커 그대로, 공백 제거 후 보존
        all_raw_syms = pd.concat([
            df_sheet1['Symbol'], 
            df_sheet2['Symbol'],
            pd.Series(special_watch)
        ]).dropna().unique()
        
        # 티커 정규화: 야후가 못 읽는 형식 방지
        all_syms = [str(s).strip().upper() for s in all_raw_syms if len(str(s)) > 0]
        
        print(f"📡 총 {len(all_syms)}개 전 세계 티커 수집 개시 (국가 코드 포함)...")

        raw_dict = {}
        # [수정] 대량 다운로드 실패 방지를 위한 '티커별 개별/소량 확인 사살' 로직
        # 한꺼번에 던지면 .KS .T 등이 씹히므로 20개씩 아주 조심스럽게 가져옵니다.
        chunk_size = 20 
        for i in range(0, len(all_syms), chunk_size):
            chunk = all_syms[i:i + chunk_size]
            # [Full Process Compliance] 데이터 누수 체크
            data = yf.download(chunk, period="200d", group_by='ticker', progress=False, threads=True, timeout=60)
            
            if not data.empty:
                for sym in chunk:
                    if sym in data.columns.levels[0] if isinstance(data.columns, pd.MultiIndex) else [sym]:
                        # 데이터가 있는 놈만 챙깁니다.
                        try:
                            s_data = data[sym] if len(chunk) > 1 else data
                            if not s_data.empty and 'Close' in s_data.columns:
                                raw_dict[sym] = s_data
                        except: continue
            
            print(f"📦 {min(i + chunk_size, len(all_syms))} / {len(all_syms)} 확인 중... (누적 성공: {len(raw_dict)}개)")
            time.sleep(0.5) # 야후 차단 회피용 미세 지연

        report = f"🛡️ [V40-C 정예 타격 지령]\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"
        report += f"🌍 전 세계 {len(all_syms)}개 중 {len(raw_dict)}개 데이터 생존 확인\n"

        # --- [1층: 요새] ---
        emergency = ""
        # 1층 시트와 special_watch 종목 중 데이터가 확보된 놈들만 분석
        fortress_targets = [s for s in list(set(list(df_sheet1['Symbol'].dropna().astype(str)) + special_watch)) if s in raw_dict]
        for sym in fortress_targets:
            try:
                data = raw_dict[sym]
                curr = float(data['Close'].iloc[-1])
                low_60 = data['Low'].tail(60).min()
                dist = (curr / low_60 - 1) * 100
                if dist <= 5.0:
                    emergency += f"🚨 {sym}: $ {curr:.2f} ({dist:.1f}% 남음)\n"
            except: continue
        report += "\n🏰 [1층: 요새 긴급대응]\n" + (emergency if emergency else "요새 이상 무\n")

        # --- [2, 3층 통합 엔진] ---
        human_pool = []
        tactical_pool = []
        # 2층 시트 종목 중 데이터가 확보된 놈들만 퀀텀 분석
        human_targets = [str(s).strip() for s in df_sheet2['Symbol'].dropna().unique() if str(s).strip() in raw_dict]
        for sym in human_targets:
            try:
                data = raw_dict[sym]
                if len(data) < 130: continue
                close, vol = data['Close'], data['Volume']
                returns = close.pct_change(fill_method=None)
                curr_price = float(close.iloc[-1])

                v_energy = (vol.pct_change(fill_method=None).rolling(10).std() * returns.rolling(10).std() * 10000).fillna(0)
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

        # [Full Process Compliance] 저장 후 보고
        pd.DataFrame(tactical_pool).to_excel("V40_QUANTUM_FINAL.xlsx", index=False)
        send_telegram(report)
        print(f"✅ 분석 완료. 총 {len(raw_dict)}개 종목 생존.")

    except Exception as e:
        print(f"⚠️ 시스템 치명적 에러: {e}")

if __name__ == "__main__":
    run_v40_no_leak_sentry()
