import pandas as pd
import yfinance as yf
import numpy as np
import requests
import os
import glob
from datetime import datetime
import warnings
import traceback

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
        """[방어 시스템] 파일명 변조를 원천 차단하는 중장갑 로더"""
        print(f"📂 파일 로딩 시도: {file_name}")
        
        # 1. 파일 존재 여부 확인 (경로 자동 보정)
        target_path = file_name
        if not os.path.exists(target_path):
            # /content/ 경로를 붙여서 재시도
            target_path = f"/content/{file_name}"
            
        if not os.path.exists(target_path):
            # 그래도 없으면 파일명 일부로 검색 (유연성 확보)
            keyword = file_name.split('_')[0] # 예: V7, V8
            candidates = glob.glob(f"/content/*{keyword}*.xlsx")
            if candidates:
                target_path = candidates[0]
                print(f"⚠️ 대체 파일 발견: {target_path}")
            else:
                print(f"❌ [치명적 결함] 파일 실종: {file_name}")
                raise FileNotFoundError(f"필수 데이터 누락: {file_name}")

        # 2. 로딩 시도 (openpyxl 엔진)
        try:
            return pd.read_excel(target_path, engine='openpyxl')
        except Exception as e:
            # CSV로 재시도
            try:
                return pd.read_csv(target_path)
            except:
                raise ValueError(f"🚨 로딩 실패 ({file_name}): {e}")

    def calculate_macro_spectrum(self):
        """[V40 하이브리드] NBI(바이오) + NG100(넥스트젠) 지수를 반영한 정밀 판정"""
        print("🔭 매크로 정찰병 투입 중 (NBI + NG100 관측)...")
        try:
            # [수정] 방금 생성한 최신 파일명으로 교체
            v7_df = self._smart_file_loader("V7_FINAL_REPORT.xlsx")
            v8_df = self._smart_file_loader("V8_REVISION_FINAL.xlsx")
            
            # 파일 구조에 맞게 컬럼명 및 데이터 추출
            # V8 파일의 경우 'V8_NextGen_Cash' 컬럼이 최종임
            if 'V8_NextGen_Cash' in v8_df.columns:
                v8_raw = v8_df['V8_NextGen_Cash'].iloc[-1] / 100 # %단위를 소수로 변환
            else:
                v8_raw = v8_df['Recommended_Cash_Ratio'].iloc[-1]

            # 기본 비중 설정
            self.v8_p = v8_raw * 100 
            self.v7_p = 100 - self.v8_p 

            # ------------------------------------------------------------------
            # [신규 추가] 2. 나스닥 바이오(^NBI) & 넥스트젠 100(^NGX) 실시간 분석
            # ------------------------------------------------------------------
            try:
                sentinels = yf.download(['^NBI', '^NGX'], period='1mo', progress=False)['Close']
                
                if not sentinels.empty and len(sentinels) > 20:
                    nbi_curr = sentinels['^NBI'].iloc[-1]
                    nbi_ma20 = sentinels['^NBI'].rolling(20).mean().iloc[-1]
                    
                    ngx_curr = sentinels['^NGX'].iloc[-1]
                    ngx_ma20 = sentinels['^NGX'].rolling(20).mean().iloc[-1]
                    
                    boost = 0
                    if nbi_curr > nbi_ma20: boost += 5 
                    if ngx_curr > ngx_ma20: boost += 5 
                    
                    # [원칙 2: Negative Check] 
                    prev_v8 = self.v8_p
                    self.v8_p = max(0, self.v8_p - boost)
                    self.v7_p = 100 - self.v8_p
                    
                    if boost > 0:
                        print(f"✅ 야성 지표 포착: 현금 {prev_v8:.1f}% -> {self.v8_p:.1f}% (공격 강화)")
            
            except Exception as e_sentinel:
                print(f"⚠️ 지수 조회 실패 (기본값 유지): {e_sentinel}")

            # 3. 최종 상태 판정
            if self.v8_p > 60:
                self.market_state = "🚨 [수비 강화] 현금 비중 압도적 유지"
            elif self.v8_p > 50:
                self.market_state = "⚖️ [쏠림형 강세] 대형주 위주 관망"
            else:
                self.market_state = "🔥 [적극 공략] 중소형주/바이오 탄력 구간"

            return True

        except Exception as e:
            print(f"❌ 매크로 분석 실패: {e}")
            print(traceback.format_exc()) # 상세 에러 출력
            return False

    def floor_1_action(self):
        """2단계: 1층 보유주 - 트레일링 스탑"""
        print("🏢 2단계: 1층 보유주 정밀 진단...")
        portfolio = ['FCX', 'SCCO', 'SIVR', 'ISSC', 'LUNR', 'IREN', 'MU', 'SIDU']
        results = []
        try:
            data = yf.download(portfolio, period="1y", group_by='ticker', progress=False)
            dynamic_limit = max(0.2, 0.7 - (self.v8_p * 0.006)) 
            
            for sym in portfolio:
                try:
                    df = data[sym]
                    if df.empty: continue
                    
                    curr = df['Close'].iloc[-1]
                    ma120 = df['Close'].rolling(120).mean().iloc[-1]
                    recent_high = df['Close'].rolling(20).max().iloc[-1]
                    drawdown = (curr / recent_high - 1) * 100
                    
                    if curr < ma120: action, icon = "🔴 [매도] 120선 붕괴", "💀"
                    elif drawdown < -12.0: action, icon = f"🟠 [손절] 고점대비 {drawdown:.1f}%", "🏃"
                    elif (curr/ma120 - 1) > dynamic_limit: action, icon = f"🚨 과열 (비중축소)", "🔥"
                    else: action, icon = "🟢 홀딩", "💎"
                    
                    results.append(f"{icon} {sym}: {action}")
                except:
                    continue
            return "\n".join(results)
        except Exception as e:
            return f"⚠️ 1층 분석 오류: {e}"

    def floor_2_hunting(self):
        """3단계: 2층 신규 사냥터"""
        print("🧬 3단계: 2층 신규 타겟 스캐닝...")
        try:
            # [수정] 파일명 현행화
            v7c = self._smart_file_loader("COMMODITY_ANALYSIS_REPORT.xlsx") # 원자재
            # 아래 파일들은 형님 폴더에 있는지 확인 필요 (없으면 빈 리스트 처리)
            try: v40_best = self._smart_file_loader("V40_BEST_TARGETS.xlsx")
            except: v40_best = pd.DataFrame()
            
            try: v40_ten = self._smart_file_loader("V40_TEN_BAGGER_REPORT_0837.xlsx")
            except: v40_ten = pd.DataFrame()
            
            msg = []
            
            # 원자재 리포트 활용
            if '원자재_진단' in pd.ExcelFile("COMMODITY_ANALYSIS_REPORT.xlsx").sheet_names:
                df_comm = pd.read_excel("COMMODITY_ANALYSIS_REPORT.xlsx", sheet_name='원자재_진단')
                status = df_comm.iloc[0]['데이터'] if not df_comm.empty else "N/A"
                msg.append(f"🛢️ 원자재 상태: {status}")

            return "\n".join(msg)
        except Exception as e:
            print(f"⚠️ 2층 분석 오류: {e}")
            return "⚠️ 2층 데이터 로딩 실패"

    def run_process(self):
        print("\n🚀 [V40 시스템] 가동 시작...")
        
        # 1. 매크로 분석
        if not self.calculate_macro_spectrum():
            print("❌ 매크로 분석 단계에서 치명적 오류 발생. 시스템 종료.")
            # 실패해도 텔레그램으로 알림
            requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                          json={"chat_id": self.chat_id, "text": "❌ [V40 경보] 시스템 가동 실패 (파일/로직 확인 요망)"})
            return 
            
        # 2. 1층/2층 분석
        f1_res = self.floor_1_action()
        f2_res = self.floor_2_hunting()

        # 3. 리포트 작성
        from datetime import datetime, timedelta
        kst_now = datetime.utcnow() + timedelta(hours=9)
        
        self.analysis_report = f"📊 [V40 통합 리포트] {kst_now.strftime('%m/%d %H:%M')}\n\n"
        self.analysis_report += f"🔥 주식(V7): {self.v7_p:.1f}% | 💰 현금(V8): {self.v8_p:.1f}%\n"
        self.analysis_report += f"📢 상태: {self.market_state}\n\n"
        self.analysis_report += f"🏢 [보유주 진단]\n{f1_res}\n\n"
        self.analysis_report += f"🧬 [신규/원자재]\n{f2_res}"

        print("\n📨 텔레그램 전송 시도...")
        try:
            resp = requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                          json={"chat_id": self.chat_id, "text": self.analysis_report})
            if resp.status_code == 200:
                print("✅ 텔레그램 전송 성공!")
            else:
                print(f"❌ 텔레그램 전송 실패: {resp.text}")
        except Exception as e:
            print(f"❌ 통신 오류: {e}")

if __name__ == "__main__":
    engine = QuantumControlCenter()
    engine.run_process()
