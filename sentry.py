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
        self.macro_v8_switch = macro_v8_switch # 형님이 입력하는 비상 V8 가중치
        self.report_data = []
        self.v7_p = 50.0
        self.v8_p = 50.0
        self.market_state = "⚖️ 초기화 중"
        self.t_token = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
        self.chat_id = "198757117"

    def negative_check(self, value, name):
        """[원칙 2] 데이터 커먼센스 체크: 음수나 비논리적 수치 차단"""
        if value < 0 or value > 1000000000: # 비정상적 수치
            raise ValueError(f"❌ {name} 데이터 오류: {value} (논리적 한계를 벗어남)")

    def calculate_spectrum(self):
        """V7(상승) vs V8(붕괴) 스펙트럼 산출 (+)"""
        try:
            v7_df = pd.read_csv("V7_RESULT_BNAI_FINAL.xlsx - Sheet1.csv")
            v8_df = pd.read_csv("KIM_DIRECTOR_V8_UPDATED.xlsx - Sheet1.csv")
            
            v7_e = v7_df['V_Energy'].iloc[-1]
            v8_r = v8_df['Recommended_Cash_Ratio'].iloc[-1]
            
            # 데이터 검증 (Negative Check)
            self.negative_check(v8_r, "V8 Cash Ratio")
            
            # 매크로 스위치 반영 (형님의 직관 주입)
            v8_final = v8_r + (self.macro_v8_switch * 5) # 스위치당 5%씩 위험도 가중
            
            total = v7_e + v8_final
            self.v7_p = (v7_e / total) * 100
            self.v8_p = (v8_final / total) * 100
            
            if self.v8_p > 65: self.market_state = "🥶 V8 붕괴파동 지배"
            elif self.v7_p > 65: self.market_state = "🔥 V7 상승파동 지배"
            else: self.market_state = "⚖️ 중립 (데이터 연결 확인 필요)"
            
        except Exception as e:
            print(f"🚨 [로직오류] 스펙트럼 산출 불가: {e}")
            raise

    def floor_1_portfolio(self):
        """1층: 보유주 생존 판결 (V7/V8 비율에 따른 동적 대응) (+)"""
        portfolio = ['FCX', 'SCCO', 'SIVR', 'ISSC', 'LUNR', 'IREN', 'MU', 'SIDU']
        results = []
        
        # V8(위험)이 높을수록 익절/손절 기준을 0.7에서 0.2까지 수축시킴 (안면몰수 전략)
        dynamic_limit = max(0.2, 0.7 - (self.v8_p * 0.006))
        
        for sym in portfolio:
            tk = yf.Ticker(sym)
            df = tk.history(period="1y")
            if df.empty: continue
            
            curr = df['Close'].iloc[-1]
            ma120 = df['Close'].rolling(120).mean().iloc[-1]
            
            # 강제 손절 원칙: 평단가 데이터 부재 시 120일선 이탈을 '자살 방지선'으로 설정
            if curr < ma120:
                action, icon = "🚨 전량 매도 (생존 본능)", "🔴"
            elif (curr / ma120 - 1) > dynamic_limit:
                action, icon = f"🔥 과열(비중 {int(self.v8_p)}% 축소)", "🚨"
            else:
                action, icon = "💎 강력 홀딩", "🟢"
            
            results.append(f"{icon} {sym}: {action}")
        return "\n".join(results)

    def floor_2_hunting(self):
        """2층: 신규 사냥터 (V7C 원자재 + V40 리포트 교차 분석) (+)"""
        try:
            v7c = pd.read_csv("V7C_GLOBAL_MINING_TOTAL_REPORT_20260116.xlsx - Sheet1.csv")
            v40_target = pd.read_csv("V40_BEST_TARGETS.xlsx - Sheet1.csv")
            v40_ten = pd.read_csv("V40_TEN_BAGGER_REPORT_0837.xlsx - Sheet1.csv")
            
            # V7C 에너지가 높은 원자재주와 V40 리스트의 교집합 추출
            v7c_top = v7c[v7c['Grade'].str.contains('A|B')].sort_values(by='V_Energy', ascending=False)
            
            # V7 우세 시: 텐배거 리포트에서 공격적 종목
            if self.v7_p > self.v8_p:
                hunt_list = v40_ten[v40_ten['Status'].str.contains('Buy')].head(3)
                msg = "\n".join([f"🚀 {r['Symbol']} | 펄스:{r['Q_Score']:.1f}" for _, r in hunt_list.iterrows()])
            # V8 우세 시: 원자재 방어주(V7C) 중심
            else:
                hunt_list = v7c_top.head(3)
                msg = "\n".join([f"⛏️ {r['Symbol']} | 원자재 에너지:{r['V_Energy']}" for _, r in hunt_list.iterrows()])
            
            return msg
        except Exception as e:
            return f"🧬 사냥터 분석 오류: {e}"

    def run_process(self):
        """[원칙 1] 전 과정 준수: 분석 -> 처리 -> 저장 -> 보고 (=)"""
        try:
            self.calculate_spectrum()
            f1_msg = self.floor_1_portfolio()
            f2_msg = self.floor_2_hunting()
            
            # 결과 저장 (엑셀 파일 생성)
            report_df = pd.DataFrame([{"V7": self.v7_p, "V8": self.v8_p, "State": self.market_state}])
            file_name = f"V40_FINAL_REPORT_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
            report_df.to_excel(file_name)
            
            # 최종 메시지 구성
            final_msg = (f"👹 [V40 퀀텀 관제센터]\n\n"
                         f"📊 [시장 스펙트럼 판정]\n"
                         f"🔴 V7(상승파동): {self.v7_p:.1f}%\n"
                         f"🔵 V8(붕괴파동): {self.v8_p:.1f}%\n"
                         f"📢 판정: {self.market_state}\n\n"
                         f"🏢 [1층: 보유주 대응]\n{f1_msg}\n\n"
                         f"🧬 [2층: 신규 사냥터]\n{f2_msg}")
            
            # 텔레그램 발송
            requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                          json={"chat_id": self.chat_id, "text": final_msg})
            
            print(f"✅ 프로세스 완료: {file_name} 저장 및 보고 완료")
            
        except Exception as e:
            print(f"❌ 프로세스 중단 (지름길 금지): {e}")

if __name__ == "__main__":
    # 매크로 스위치 (0~10): 유동성 축소 등 위험 시 숫자를 높여 V8 가중치 부여
    engine = QuantumControlCenter(macro_v8_switch=2)
    engine.run_process()
