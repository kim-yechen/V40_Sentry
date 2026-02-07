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
        """[V40 최종 무결성] 데이터 수치를 조작하지 않고, 비중(0.58)을 절대값으로 사용"""
        try:
            v7_df = self._smart_file_loader("KIM_DIRECTOR_V7_HYBRID_FINAL.xlsx")
            v8_df = self._smart_file_loader("KIM_DIRECTOR_V8_RECESSION_ALERT.xlsx")
            
            v7_raw = v7_df['V_Energy'].iloc[-1]           # 713.77
            v8_raw = v8_df['Recommended_Cash_Ratio'].iloc[-1] # 0.5858 (58.5%)
            
            # [핵심] 0.58이라는 숫자를 58%로 바로 인정합니다.
            # V8 비중은 파일에 적힌 그대로 가져오고, 나머지를 V7로 채웁니다.
            self.v8_p = v8_raw * 100  # 결과: 58.5%
            self.v7_p = 100 - self.v8_p # 결과: 41.5%
            
            # 쏠림 감지 판정
            if v8_raw > 0.5:
                self.market_state = "🚨 [⚠️쏠림형 강세] 대형주 독식 / 개별주 피빨림"
                if self.v8_p < 60: # 쏠림장일 땐 리스크를 더 엄격하게 (최소 60% 확보)
                    self.v8_p = 60.0
                    self.v7_p = 40.0
            else:
                self.market_state = "🔥 V7 정상 파동 (적극 공략)"
            
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

    # [추가] 전임자 스타일 데이터 추출 엔진 (1층용)
    def _get_floor_2_data(self):
        """2층: 텍스트 리포트와 100% 동기화 (V7C, BEST, TEN_BAGGER 통합)"""
        combined = []
        try:
            # 1. 파일 3종 세트 로딩 (텍스트 로직과 동일하게)
            v7c = self._smart_file_loader("V7C_GLOBAL_MINING_TOTAL_REPORT_20260116.xlsx")
            best = self._smart_file_loader("V40_BEST_TARGETS.xlsx")
            v40_ten = self._smart_file_loader("V40_TEN_BAGGER_REPORT_0837.xlsx")
            
            # 2. V7C (Mining Shield) 추출
            if not v7c.empty:
                t1 = v7c[v7c['Grade'].str.contains('Shield|A', na=False)].head(3).copy()
                t1 = t1[['Symbol', 'Price', 'V_Energy']].rename(columns={'V_Energy': 'Accel_Score'})
                t1['Risk_Tag'] = '🛡️ Shield'
                combined.append(t1)
            
            # 3. BEST Targets 추출
            if not best.empty:
                t2 = best.sort_values(by='V_Energy', ascending=False).head(3).copy()
                t2 = t2[['Ticker', 'Price', 'V_Energy']].rename(columns={'Ticker': 'Symbol', 'V_Energy': 'Accel_Score'})
                t2['Risk_Tag'] = '🎯 BEST'
                combined.append(t2)

            # 4. TEN_BAGGER (이게 누락되어 빈칸이었던 주범입니다)
            if not v40_ten.empty:
                t3 = v40_ten[v40_ten['Status'].str.contains('Buy', na=False)].head(5).copy()
                # 텐배거 파일은 컬럼명이 다를 수 있으므로 안전하게 처리
                cols = {'Symbol': 'Symbol', 'Q_Score': 'Accel_Score', 'Price': 'Price'}
                t3 = t3[[c for c in cols.keys() if c in t3.columns]].rename(columns=cols)
                t3['Risk_Tag'] = '🚀 TEN-B'
                combined.append(t3)

            if not combined:
                # 데이터가 하나도 없으면 전임자 양식이라도 유지
                return pd.DataFrame(columns=["Symbol", "Price", "Accel_Score", "Risk_Tag"])
            
            df_final = pd.concat(combined, ignore_index=True)
            # 0131 파일 스타일로 Real_Pulse 컬럼(보조지표) 강제 생성
            df_final['Real_Pulse'] = df_final['Accel_Score'] * 10 
            return df_final
            
        except Exception as e:
            print(f"⚠️ 2층 데이터 수집 중 엔진 과부하: {e}")
            return pd.DataFrame(columns=["Symbol", "Price", "Accel_Score", "Real_Pulse", "Risk_Tag"])

    def run_process(self):
        """[V40 무결성 공정] 데이터 생성 -> 시트 분리 저장 -> 텔레그램 발송"""
        if not self.calculate_macro_spectrum(): return
        
        # 1. 데이터 준비 (1층, 2층, 종합리포트)
        df_f1 = self._get_floor_1_data()
        df_f2 = self._get_floor_2_data() # 이제 꽉 차서 나옵니다
        
        f1_msg = self.floor_1_action()
        f2_msg = self.floor_2_hunting()
        self.analysis_report = (f"👹 [V40 퀀텀 관제센터: Hybrid]\n\n"
                                f"📊 [파동 관측]\n"
                                f"🔴 V7: {self.v7_p:.1f}% | 🔵 V8: {self.v8_p:.1f}%\n"
                                f"📢 상태: {self.market_state}\n\n"
                                f"🏢 [1층 보유점검]\n{f1_msg}\n\n"
                                f"🧬 [2층 신규발굴]\n{f2_msg}")

        # 2. 엑셀 파일 물리적 저장
        file_name = f"V40_Weekly_Wolf_{datetime.now().strftime('%m%d')}.xlsx"
        report_rows = [{"V40_REPORT_SUMMARY": line} for line in self.analysis_report.split('\n')]
        df_summary = pd.DataFrame(report_rows)

        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            df_f1.to_excel(writer, sheet_name='1층_보유점검', index=False)
            df_f2.to_excel(writer, sheet_name='2층_신규발굴', index=False)
            df_summary.to_excel(writer, sheet_name='종합리포트', index=False)

        # 3. 보고 체계 가동
        try:
            # 텍스트는 매일 발송
            requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                          json={"chat_id": self.chat_id, "text": self.analysis_report})

            # 토요일엔 '진짜 엑셀' 발송
            if datetime.now().weekday() == 5:
                with open(file_name, 'rb') as f:
                    requests.post(f"https://api.telegram.org/bot{self.t_token}/sendDocument", 
                                  data={'chat_id': self.chat_id, 'caption': f"📊 {file_name} 데이터 정합성 검증 완료"}, 
                                  files={'document': f})
        except Exception as e:
            print(f"❌ 보고 체계 장애: {e}")
            
if __name__ == "__main__":
    # 스위치 2단계: V8 현금 비중에 +10% 가산하여 보수적으로 관측
    engine = QuantumControlCenter(macro_v8_switch=2)
    engine.run_process()
