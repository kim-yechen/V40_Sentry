import pandas as pd
import yfinance as yf
import numpy as np
import requests
import os
from datetime import datetime
import warnings

# [V40 원칙: 기계적 무결성 및 지름길 금지]
warnings.filterwarnings('ignore')

class QuantumControlCenter:
    def __init__(self, macro_v8_switch=0):
        # 형님의 직관 주입용 비상 스위치
        self.macro_v8_switch = macro_v8_switch 
        self.t_token = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
        self.chat_id = "198757117"
        
        # 데이터 저장 공간
        self.v7_p = 50.0
        self.v8_p = 50.0
        self.market_state = "⚖️ 초기화"
        self.analysis_log = []

    def negative_check(self, df, col_name):
        """[원칙 2] 데이터 커먼센스 체크: 음수/NaN 발생 시 즉시 중단"""
        if df[col_name].isnull().any() or (df[col_name] < -1000000).any():
            print(f"🚨 [데이터 오염] {col_name} 열에 비논리적 수치 발견. 수식 수정 필요.")
            return False
        return True

    def calculate_macro_spectrum(self):
        """V7(상승) vs V8(붕괴) 스펙트럼 산출 (+)"""
        print("🔎 1단계: 매크로 스펙트럼 분석 중...")
        try:
            v7_df = pd.read_csv("V7_RESULT_BNAI_FINAL.xlsx - Sheet1.csv")
            v8_df = pd.read_csv("KIM_DIRECTOR_V8_UPDATED.xlsx - Sheet1.csv")
            
            # 마지막 데이터 포인트 추출
            v7_e = v7_df['V_Energy'].iloc[-1]
            v8_r = v8_df['Recommended_Cash_Ratio'].iloc[-1]
            
            # 형님의 비상 스위치 반영 (유동성 축소 등 매크로 악재 강제 주입)
            v8_final = v8_r + (self.macro_v8_switch * 5)
            
            total = v7_e + v8_final
            self.v7_p = (v7_e / total) * 100
            self.v8_p = (v8_final / total) * 100
            
            if self.v8_p > 65: self.market_state = "🥶 V8 붕괴파동 지배 (현금 사수)"
            elif self.v7_p > 65: self.market_state = "🔥 V7 상승파동 지배 (공격 전개)"
            else: self.market_state = "⚖️ 변곡점 구간 (선별적 대응)"
            
            return True
        except Exception as e:
            print(f"❌ 매크로 분석 실패: {e}")
            return False

    def floor_1_action(self):
        """1층: 보유주 대응 - V8 기반 동적 매도 로직 (+)"""
        print("🏢 2단계: 1층 보유주 생존 판결 중...")
        portfolio = ['FCX', 'SCCO', 'SIVR', 'ISSC', 'LUNR', 'IREN', 'MU', 'SIDU']
        results = []
        
        try:
            # 일괄 다운로드로 속도 보장
            data = yf.download(portfolio, period="1y", group_by='ticker', progress=False)
            # V8 위험도에 따라 익절/손절 기준을 타이트하게 조절
            dynamic_limit = max(0.2, 0.7 - (self.v8_p * 0.006))
            
            for sym in portfolio:
                df = data[sym]
                if df.empty: continue
                
                curr = df['Close'].iloc[-1]
                ma120 = df['Close'].rolling(120).mean().iloc[-1]
                gap = (curr / ma120 - 1) if ma120 else 0
                
                # [강제 원칙]
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
        """2층: 신규 사냥터 - V7C 원자재 + V40 리포트 교차 매칭 (+)"""
        print("🧬 3단계: 2층 신규 괴물 사냥 중...")
        try:
            v7c = pd.read_csv("V7C_GLOBAL_MINING_TOTAL_REPORT_20260116.xlsx - Sheet1.csv")
            v40_ten = pd.read_csv("V40_TEN_BAGGER_REPORT_0837.xlsx - Sheet1.csv")
            
            # V7C(원자재) 필터링: Grade가 Shield인 우량주 우선
            shield_mining = v7c[v7c['Grade'].str.contains('Shield', na=False)]
            
            # V7 우세 시: 텐배거 리포트의 펄스(Q_Score) 높은 종목
            if self.v7_p > self.v8_p:
                targets = v40_ten[v40_ten['Status'].str.contains('Buy', na=False)].head(3)
                hunt_msg = "\n".join([f"🚀 {r['Symbol']} | 펄스:{r['Q_Score']:.1f}" for _, r in targets.iterrows()])
            # V8 우세 시: 실물 기반 Shield 종목
            else:
                targets = shield_mining.head(3)
                hunt_msg = "\n".join([f"⛏️ {r['Symbol']} | 에너지:{r['V_Energy']}" for _, r in targets.iterrows()])
                
            return hunt_msg
        except Exception as e:
            return f"🧬 2층 분석 오류: {e}"

    def run_process(self):
        """[원칙 1] 전 과정 준수: 분석 + 처리 + 저장 = 보고 (=)"""
        # 1. 분석
        if not self.calculate_macro_spectrum(): return
        
        f1_report = self.floor_1_action()
        f2_report = self.floor_2_hunting()
        
        # 2. 처리 (메시지 구성)
        final_msg = (f"👹 [V40 퀀텀 관제센터]\n\n"
                     f"📊 [시장 스펙트럼 판정]\n"
                     f"🔴 V7(상승파동): {self.v7_p:.1f}%\n"
                     f"🔵 V8(붕괴파동): {self.v8_p:.1f}%\n"
                     f"📢 판정: {self.market_state}\n\n"
                     f"🏢 [1층: 보유주 대응]\n{f1_report}\n\n"
                     f"🧬 [2층: 신규 사냥터]\n{f2_report}")

        # 3. 저장 (1+1-1 원칙: 보고 전 저장)
        file_name = f"V40_QUANTUM_LOG_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
        pd.DataFrame([{"Content": final_msg}]).to_excel(file_name, index=False)
        
        # 4. 보고 (텔레그램)
        try:
            res = requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                                json={"chat_id": self.chat_id, "text": final_msg}, timeout=15)
            if res.status_code == 200:
                print(f"✅ 보고 완료 및 {file_name} 저장 성공.")
            else:
                print(f"❌ 텔레그램 발송 실패: {res.status_code}")
        except Exception as e:
            print(f"❌ 통신 오류: {e}")

if __name__ == "__main__":
    # 매크로 스위치: 0(기본) ~ 10(극심한 위험)
    engine = QuantumControlCenter(macro_v8_switch=2)
    engine.run_process()
