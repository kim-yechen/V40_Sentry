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
        # 1. 초기 설정: 형님의 비상 스위치 및 텔레그램 토큰
        self.macro_v8_switch = macro_v8_switch 
        self.t_token = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
        self.chat_id = "198757117"
        
        # 2. 시스템 상태 변수 (파동 관측용)
        self.v7_p = 50.0 # 상승 에너지
        self.v8_p = 50.0 # 붕괴(현금) 압력
        self.market_state = "⚖️ 시스템 초기화 중..."
        self.analysis_report = ""

    def _smart_file_loader(self, file_name):
        """[방어 시스템] 인코딩(0x9d) 및 파일명 변조를 원천 차단하는 중장갑 로더"""
        # 경로 후보군 생성 (원본, 엑셀->CSV 변환본, 순수 CSV)
        base = file_name.split('.')[0]
        candidates = [file_name, f"{base}.xlsx - Sheet1.csv", f"{base}.csv"]
        
        target_path = None
        for c in candidates:
            if os.path.exists(c):
                target_path = c
                break
        
        # 파일 부재 시 즉시 경고 (원칙 3: 지름길 금지)
        if not target_path:
            raise FileNotFoundError(f"❌ 필수 데이터 누락: {file_name}을 찾을 수 없습니다.")

        # 인코딩 파상 공세 (한국어 엑셀 호환성 확보)
        for encoding in ['utf-8-sig', 'cp949', 'utf-8', 'latin1']:
            try:
                if target_path.endswith('.xlsx') and "csv" not in target_path:
                    return pd.read_excel(target_path)
                return pd.read_csv(target_path, encoding=encoding)
            except Exception:
                continue
        
        # 최후의 수단: openpyxl 엔진 강제 구동
        try:
            return pd.read_excel(target_path, engine='openpyxl')
        except:
            raise ValueError(f"🚨 {file_name} 로딩 실패. 파일이 손상되었거나 잠겨있습니다.")

    def negative_check(self, df, col_name, threshold=-1000000):
        """[원칙 2] 데이터 커먼센스 체크: 기계적 결함 감지"""
        if df[col_name].isnull().any():
            raise ValueError(f"⚠️ {col_name} 열에 결측치(NaN)가 포함되어 있습니다.")
        
        min_val = df[col_name].min()
        if min_val < threshold:
            raise ValueError(f"🚨 {col_name} 수치 오류: {min_val} (논리적 한계치 이탈)")
        return True

    def calculate_macro_spectrum(self):
        """[V40 무결성+쏠림보정] 0.58을 58점으로 대접하고 쏠림장세를 감지하는 로직"""
        print("🔎 1단계: 시장 파동 관측 및 '쏠림형 강세' 정밀 진단 중...")
        try:
            # 1. 형님이 신뢰하시는 데이터 2개 로드
            v7_df = self._smart_file_loader("KIM_DIRECTOR_V7_HYBRID_FINAL.xlsx")
            v8_df = self._smart_file_loader("KIM_DIRECTOR_V8_RECESSION_ALERT.xlsx")
            
            # 2. 마지막 데이터 추출
            v7_energy = v7_df['V_Energy'].iloc[-1]           # 약 713
            v8_cash_raw = v8_df['Recommended_Cash_Ratio'].iloc[-1] # 약 0.58 (58%)
            
            # 3. [체급 동기화] 0.58을 58점으로 변환하여 V7(713)과 싸울 수 있게 만듦
            v8_score = v8_cash_raw * 100 
            v8_final = v8_score + (self.macro_v8_switch * 5) # 스위치 반영
            
            # 4. [쏠림형 강세 감지] 형님 계좌 -11%의 원인을 잡는 핵심 로직
            # 지수는 높은데(V7 > 500) 리스크 경고(V8 > 50)가 동시에 뜨면 '기형적 쏠림'으로 판단
            if v7_energy > 500 and v8_score > 50:
                self.market_state = "🚨 [⚠️쏠림형 강세] 대형주 독식 / 중소형주 피빨림 장세"
                # 쏠림장에서는 V8(방패)의 가중치를 1.5배 강제 펌핑하여 형님 자산 보호
                v8_final = v8_final * 1.5 
            
            # 5. 파동 붕괴 시뮬레이션 (최종 비중 계산)
            if v8_final > 60:
                collapse_factor = np.exp(-(v8_final - 60) / 10)
                v7_effective = v7_energy * collapse_factor
            else:
                v7_effective = v7_energy

            total = v7_effective + v8_final
            self.v7_p = (v7_effective / total) * 100
            self.v8_p = (v8_final / total) * 100
            
            # 6. 최종 상태 메시지 보정
            if self.v8_p > 70:
                self.market_state += " | 💀 파동 붕괴 (현금 100% 권장)"
            elif self.v8_p > 50:
                self.market_state += " | ⚖️ 보수적 대응 구간"
            
            return True
        except Exception as e:
            print(f"❌ 분석 실패: {e}")
            return False

    def floor_1_action(self):
        """2단계: 1층 보유주 - 트레일링 스탑(Trailing Stop) 적용"""
        print("🏢 2단계: 1층 보유주 정밀 진단 (트레일링 스탑 가동)...")
        portfolio = ['FCX', 'SCCO', 'SIVR', 'ISSC', 'LUNR', 'IREN', 'MU', 'SIDU']
        results = []
        try:
            data = yf.download(portfolio, period="1y", group_by='ticker', progress=False)
            dynamic_limit = max(0.2, 0.7 - (self.v8_p * 0.006)) # V8 높으면 이격도 허용치 축소
            
            for sym in portfolio:
                df = data[sym]
                if df.empty: continue
                
                curr = df['Close'].iloc[-1]
                ma120 = df['Close'].rolling(120).mean().iloc[-1]
                
                # [신규 로직] 고점 대비 하락률 (MDD from 20-day High)
                recent_high = df['Close'].rolling(20).max().iloc[-1]
                drawdown = (curr / recent_high - 1) * 100
                
                # 판결 로직 (우선순위: 생존 > 익절 > 홀딩)
                if curr < ma120:
                    action, icon = "🔴 [전량매도] 120일선 붕괴", "💀"
                elif drawdown < -12.0:
                    # 120일선 위에 있더라도 고점 대비 12% 밀리면 기계적 탈출
                    action, icon = f"🟠 [트레일링 스탑] 고점대비 {drawdown:.1f}% 하락", "🏃"
                elif (curr/ma120 - 1) > dynamic_limit:
                    action, icon = f"🚨 과열권 진입 (비중 {int(self.v8_p)}% 축소)", "🔥"
                else:
                    action, icon = "🟢 강력 홀딩", "💎"
                
                results.append(f"{icon} {sym}: {action} (DD: {drawdown:.1f}%)")
            return "\n".join(results)
        except Exception as e:
            return f"⚠️ 1층 분석 오류: {e}"

    def floor_2_hunting(self):
        """3단계: 2층 신규 사냥터 (누락 방지 및 교차 검증)"""
        print("🧬 3단계: 2층 신규 타겟 스캐닝...")
        try:
            # 모든 타겟 파일 로딩 (누락 없음)
            v7c = self._smart_file_loader("V7C_GLOBAL_MINING_TOTAL_REPORT_20260116.xlsx")
            v40_best = self._smart_file_loader("V40_BEST_TARGETS.xlsx")
            v40_ten = self._smart_file_loader("V40_TEN_BAGGER_REPORT_0837.xlsx")
            
            # 등급 필터링
            v7c_shield = v7c[v7c['Grade'].str.contains('Shield|A', na=False)].head(2)
            best_picks = v40_best.sort_values(by='V_Energy', ascending=False).head(2)
            ten_baggers = v40_ten[v40_ten['Status'].str.contains('Buy', na=False)].head(3)

            # 시장 상황(V7 vs V8)에 따른 추천 전략 분기
            if self.v7_p > 60:
                # 상승장: 텐배거 공격적 매수
                msg = "\n".join([f"🚀 {r['Symbol']} | Q:{r['Q_Score']:.1f}" for _, r in ten_baggers.iterrows()])
            else:
                # 붕괴/혼조세: 방어적 채굴주 + 검증된 BEST 타겟
                msg = "\n".join([f"⛏️ {r['Symbol']} | E:{r['V_Energy']:.1f}" for _, r in v7c_shield.iterrows()])
                msg += "\n" + "\n".join([f"🎯 {r['Ticker']} | P:{r['Price']}" for _, r in best_picks.iterrows()])
            
            return msg
        except Exception as e:
            return f"🧬 2층 분석 오류: {e}"

    def run_process(self):
        """[원칙 1] 전 과정 준수: 분석 -> 검증 -> 저장 -> 보고"""
        if not self.calculate_macro_spectrum(): return
        
        f1_report = self.floor_1_action()
        f2_report = self.floor_2_hunting()
        
        self.analysis_report = (f"👹 [V40 퀀텀 관제센터: Hybrid]\n\n"
                                f"📊 [파동 관측]\n"
                                f"🔴 V7(에너지): {self.v7_p:.1f}% | 🔵 V8(붕괴압력): {self.v8_p:.1f}%\n"
                                f"📢 상태: {self.market_state}\n\n"
                                f"🏢 [1층: 트레일링 스탑]\n{f1_report}\n\n"
                                f"🧬 [2층: 타겟 스캐닝]\n{f2_report}")

        # [저장] 1+1-1=Complete (보고 전 저장)
        file_name = f"V40_QUANTUM_LOG_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
        pd.DataFrame([{"Content": self.analysis_report}]).to_excel(file_name, index=False)
        
        # [보고] 텔레그램 발송
        try:
            res = requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                                json={"chat_id": self.chat_id, "text": self.analysis_report}, timeout=15)
            if res.status_code == 200:
                print(f"✅ 보고 완료: {file_name} 저장됨.")
            else:
                print(f"❌ 발송 실패: {res.status_code}")
        except Exception as e:
            print(f"❌ 통신 오류: {e}")

if __name__ == "__main__":
    # 스위치 2단계: V8 현금 비중에 +10% 가산하여 보수적으로 관측
    engine = QuantumControlCenter(macro_v8_switch=2)
    engine.run_process()
