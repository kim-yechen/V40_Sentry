import os
import glob
import pandas as pd
import yfinance as yf
from datetime import datetime
import time

def run_v40_no_mercy_global():
    # [V40 원칙: 1+1-1=Complete]
    files = glob.glob("*V40_NEW_HUMAN_V2_UPGRADE*.xlsx")
    if not files: return
    target_file = files[0]

    try:
        xls = pd.ExcelFile(target_file)
        # 형님 지시: 시트 A, B만 정밀 타격
        df_a = pd.read_excel(xls, sheet_name=1) 
        df_b = pd.read_excel(xls, sheet_name=2) 
        
        # 2923개 전 세계 티커 수집
        all_syms = pd.concat([df_a['Symbol'], df_b['Symbol']]).dropna().unique()
        all_syms = [str(s).strip().upper() for s in all_syms]
        
        print(f"🌍 전 세계 {len(all_syms)}개 전선 정밀 스캔 개시...")

        raw_dict = {}
        for sym in all_syms:
            try:
                # [수정] 미국 외 국가 티커 누락 방지: 낱개로 정밀 타격
                tk = yf.Ticker(sym)
                hist = tk.history(period="200d")
                if not hist.empty:
                    raw_dict[sym] = hist
                time.sleep(0.02) # 차단 방지
            except: continue

        # --- [형식 복원: V40-C 리포트] ---
        report = f"🌍 전 세계 {len(all_syms)}개 전선 정밀 스캔 완료\n"
        
        # [1층: 요새 긴급대응]
        fortress_list = ""
        for sym in df_a['Symbol'].dropna().unique():
            if sym in raw_dict:
                data = raw_dict[sym]
                curr = data['Close'].iloc[-1]
                low_60 = data['Low'].tail(60).min()
                dist = (curr/low_60 - 1) * 100
                if dist <= 5.0:
                    fortress_list += f"🚨 {sym}: $ {curr:.2f} ({dist:.1f}% 지지선)\n"
        
        report += f"\n🏰 [1층: 요새 긴급대응]\n{fortress_list if fortress_list else '이상 무'}\n"

        # [2층: 신인류 정예 매집 5선]
        # EDI 계산 및 상위 5개 추출
        pool_2 = []
        for sym in df_b['Symbol'].dropna().unique():
            if sym in raw_dict:
                data = raw_dict[sym]
                if len(data) < 130: continue
                rets = data['Close'].pct_change()
                v_energy = (data['Volume'].pct_change().rolling(10).std() * rets.rolling(10).std() * 10000).fillna(0)
                edi = (v_energy.rolling(120).mean() / (rets.rolling(120).std() + 1e-9)).iloc[-1]
                pool_2.append({'sym': sym, 'curr': data['Close'].iloc[-1], 'edi': int(edi)})
        
        top_2 = sorted(pool_2, key=lambda x: x['edi'], reverse=True)[:5]
        report += "\n🧬 [2층: 신인류 정예 매집 5선]\n"
        for i, item in enumerate(top_2):
            report += f"💎 {item['sym']}: {item['curr']:.2f} (적정가 추정 | 🔋{item['edi']})\n"

        # [3층: 퀀텀 압착 TOP 5]
        # FBGL 포함 퀀텀 로직 적용
        pool_3 = []
        for item in pool_2:
            sym = item['sym']
            data = raw_dict[sym]
            atr = (data['High'] - data['Low']).rolling(14).mean().iloc[-1]
            target = item['curr'] + (atr * 3.5)
            upside = ((target/item['curr'])-1)*100
            pool_3.append({'sym': sym, 'curr': item['curr'], 'target': target, 'upside': upside})

        top_3 = sorted(pool_3, key=lambda x: x['upside'], reverse=True)[:5]
        report += "\n🚀 [3층: 퀀텀 압착 TOP 5]\n"
        for item in top_3:
            report += f"🔋 {item['sym']:<10} | {item['curr']:>8.2f} | 목표 {item['target']:>8.2f} (+{item['upside']:.1f}%)\n"

        # [V40 원칙: 저장 후 보고]
        pd.DataFrame(pool_3).to_excel("V40_GLOBAL_RESTORED.xlsx", index=False)
        print(report)

    except Exception as e:
        print(f"🛑 치명적 결함 발생: {e}")

if __name__ == "__main__":
    run_v40_no_mercy_global()
