import pandas as pd
import yfinance as yf
import numpy as np
import requests
import os
import glob
from datetime import datetime
import warnings

# [V40 원칙: 기계적 무결성 및 지름길 금지]
warnings.filterwarnings('ignore')

class QuantumControlCenter:
    def __init__(self, macro_v8_switch=0):
        # 1. 초기 설정 및 형님의 비상 스위치
        self.macro_v8_switch = macro_v8_switch 
        self.t_token = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
        self.chat_id = "198757117"
        
        # 2. 결과 저장용 상태 변수
        self.v7_p = 50.0
        self.v8_p = 50.0
        self.market_state = "⚖️ 초기화 중"
        self.analysis_report = ""

    def _smart_file_loader(self, file_name):
        """[고차원 사고] 인코딩(0x9d) 및 파일명 변형을 원천 차단하는 로직"""
        # 경로 후보군 생성 (원본, 변환본, 와일드카드)
        base = file_name.split('.')[0]
        candidates = [file_name, f"{base}.xlsx - Sheet1.csv", f"{base}.csv"]
        
        target_path = None
        for c in candidates:
            if os.path.exists(c):
                target_path = c
                break
        
        if not target_path:
            # 원칙 3: 지름길 금지. 파일 없으면 즉시 보고 후 중단
            raise FileNotFoundError(f"❌ 필수 데이터 누락: {file_name}")

        # 인코딩 파상 공세 (cp949는 한국어 엑셀 변환 CSV의 표준)
        for encoding in ['utf-8-sig', 'cp949', 'utf-8', 'latin1']:
            try:
                if target_path.endswith('.xlsx') and "csv" not in target_path:
                    return pd.read_excel(target_path)
                return pd.read_csv(target_path, encoding=encoding)
            except Exception:
                continue
        
        # 마지막 수단: 엔진 강제 지정
        try:
            return pd.read_excel(target_path, engine='openpyxl')
        except:
            raise ValueError(f"🚨 {file_name} 읽기 불가 (인코딩/포맷 붕괴)")

    def negative_check(self, df, col_name, threshold=-1000000):
        """[원칙 2] 데이터 커먼센스 체크: 기계적 에러 검출"""
        if df[col_name].isnull().any():
            raise ValueError(f"⚠️ {col_name} 데이터에 결측치(NaN) 발견.")
        
        min_val = df[col_name].min()
        if min_val < threshold:
            raise ValueError(f"🚨 {col_name} 수치 이상: {min_val} (논리적 한계 이탈)")
        return True

    def calculate_macro_spectrum(self):
        """1단계: 매크로 스펙트럼 분석 (+)"""
        print("🔎 1단계: V7/V8 에너지 스펙트럼 산출 중...")
        try:
            v7_df = self._smart_file_loader("V7_RESULT_BNAI_FINAL.xlsx")
            v8_df = self._smart_file_loader("KIM_DIRECTOR_V8_UPDATED.xlsx")
            
            # 데이터 검증 (원칙 2)
            self.negative_check(v7_df, 'V_Energy')
            self.negative_check(v8_df, 'Recommended_Cash_Ratio')
            
            v7_e = v7_df['V_Energy'].iloc[-1]
            v8_r = v8_df['Recommended_Cash_Ratio'].iloc[-1]
            
            # 형님 스위치 반영
            v8_final = v8_r + (self.macro_v8_switch * 5)
            total = v7_e + v8_final
            
            self.v7_p = (v7_e / total) * 100
            self.v8_p = (v8_final / total) * 100
            
            if self.v8_p > 65: self.market_state = "🥶 V8 붕괴파동 지배 (현금 사수)"
            elif self.v7_p > 65: self.market_state = "🔥 V7 상승파동 지배 (공격 전개)"
            else: self.market_state = "⚖️ 변곡점 구간 (선별적 대응)"
            
            return True
        except Exception as e:
            print(f"❌ 1단계 실패: {e}")
            return False

    def floor_1_action(self):
        """2단계: 1층 보유주 생존 판결 (+)"""
        print("🏢 2단계: 1층 보유주 실시간 진단 중...")
        portfolio = ['FCX', 'SCCO', 'SIVR', 'ISSC', 'LUNR', 'IREN', 'MU', 'SIDU']
        results = []
        try:
            data = yf.download(portfolio, period="1y", group_by='ticker', progress=False)
            # V8 수치에 따른 동적 이격도 제한
            dynamic_limit = max(0.2, 0.7 - (self.v8_p * 0.006))
            
            for sym in portfolio:
                df = data[sym]
                if df.empty: continue
                
                curr = df['Close'].iloc[-1]
                ma120 = df['Close'].rolling(120).mean().iloc[-1]
                gap = (curr / ma120 - 1) if ma120 else 0
                
                if curr < ma120:
                    action, icon = "🚨 전량 매도 (자살 방지선 이탈)", "🔴"
                elif gap > dynamic_limit:
                    action, icon = f"🔥 과열(비중 {int(self.v8_p)}% 축소)", "🚨"
                else:
                    action, icon = "💎 강력 홀딩", "🟢"
                
                results.append(f"{icon} {sym}: {action}")
            return "\n".join(results)
        except Exception as e:
            return f"⚠️ 1층 분석 오류: {e}"

    def floor_2_hunting(self):
        """3단계: 2층 신규 사냥터 - V7C + V40 BEST + TEN-BAGGER 교차 (+)"""
        print("🧬 3단계: 2층 신규 괴물 사냥 중...")
        try:
            v7c = self._smart_file_loader("V7C_GLOBAL_MINING_TOTAL_REPORT_20260116.xlsx")
            v40_best = self._smart_file_loader("V40_BEST_TARGETS.xlsx")
            v40_ten = self._smart_file_loader("V40_TEN_BAGGER_REPORT_0837.xlsx")
            
            # V7C 에너지 상위주
            v7c_targets = v7c[v7c['Grade'].str.contains('Shield|A', na=False)].head(2)
            # V40 BEST 타겟 (가격 전략 포함)
            best_targets = v40_best.sort_values(by='V_Energy', ascending=False).head(2)
            
            if self.v7_p > 55:
                # 상승장: 텐배거 리포트 우선
                hunt = v40_ten[v40_ten['Status'].str.contains('Buy', na=False)].head(3)
                msg = "\n".join([f"🚀 {r['Symbol']} (Q:{r['Q_Score']:.1f})" for _, r in hunt.iterrows()])
            else:
                # 혼조/하락장: 실물 및 BEST 타겟 우선
                msg = "\n".join([f"⛏️ {r['Symbol']} (E:{r['V_Energy']:.1f})" for _, r in v7c_targets.iterrows()])
                msg += "\n" + "\n".join([f"🎯 {r['Ticker']} (Best Target)" for _, r in best_targets.iterrows()])
            
            return msg
        except Exception as e:
            return f"🧬 2층 분석 오류: {e}"

    def run_process(self):
        """[원칙 1] 전 과정 준수: 분석 -> 처리 -> 저장 -> 보고 (=)"""
        if not self.calculate_macro_spectrum(): return
        
        f1 = self.floor_1_action()
        f2 = self.floor_2_hunting()
        
        self.analysis_report = (f"👹 [V40 퀀텀 관제센터]\n\n"
                                f"📊 [시장 스펙트럼]\n"
                                f"🔴 V7: {self.v7_p:.1f}% | 🔵 V8: {self.v8_p:.1f}%\n"
                                f"📢 판정: {self.market_state}\n\n"
                                f"🏢 [1층: 보유주 대응]\n{f1}\n\n"
                                f"🧬 [2층: 신규 사냥터]\n{f2}")

        # [저장] 원칙 1: 보고 전 반드시 저장
        file_name = f"V40_QUANTUM_LOG_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
        pd.DataFrame([{"Content": self.analysis_report}]).to_excel(file_name, index=False)
        
        # [보고] 텔레그램 발송
        try:
            res = requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                                json={"chat_id": self.chat_id, "text": self.analysis_report}, timeout=15)
            if res.status_code == 200:
                print(f"✅ 보고 완료 및 {file_name} 저장 성공.")
            else:
                print(f"❌ 발송 실패: {res.status_code}")
        except Exception as e:
            print(f"❌ 통신 오류: {e}")

if __name__ == "__main__":
    engine = QuantumControlCenter(macro_v8_switch=2)
    engine.run_process()
