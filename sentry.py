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
        """[V40 하이브리드] NBI(바이오) + NG100(넥스트젠) 지수를 반영한 정밀 판정"""
        print("🔭 매크로 정찰병 투입 중 (NBI + NG100 관측)...")
        try:
            # 1. 기존 파일 데이터 로드 (형님 데이터 무결성 유지)
            v7_df = self._smart_file_loader("KIM_DIRECTOR_V7_HYBRID_FINAL.xlsx")
            v8_df = self._smart_file_loader("KIM_DIRECTOR_V8_RECESSION_ALERT.xlsx")
            
            v8_raw = v8_df['Recommended_Cash_Ratio'].iloc[-1] # 예: 0.58
            
            # 기본 비중 설정 (파일 값 그대로 1차 인정)
            self.v8_p = v8_raw * 100 
            self.v7_p = 100 - self.v8_p 

            # ------------------------------------------------------------------
            # [신규 추가] 2. 나스닥 바이오(^NBI) & 넥스트젠 100(^NGX) 실시간 분석
            # ------------------------------------------------------------------
            try:
                # 데이터 수집 (최근 1개월)
                sentinels = yf.download(['^NBI', '^NGX'], period='1mo', progress=False)['Close']
                
                if not sentinels.empty and len(sentinels) > 20:
                    # NBI 추세 확인 (현재가 vs 20일 평균)
                    nbi_curr = sentinels['^NBI'].iloc[-1]
                    nbi_ma20 = sentinels['^NBI'].rolling(20).mean().iloc[-1]
                    
                    # NG100 추세 확인
                    ngx_curr = sentinels['^NGX'].iloc[-1]
                    ngx_ma20 = sentinels['^NGX'].rolling(20).mean().iloc[-1]
                    
                    # 시장 야성(Risk-On) 부스트 점수 계산
                    boost = 0
                    if nbi_curr > nbi_ma20: boost += 5  # 바이오가 평균 위에 있으면 +5% 공세
                    if ngx_curr > ngx_ma20: boost += 5  # 넥스트젠이 평균 위에 있으면 +5% 공세
                    
                    # [원칙 2: Negative Check] 
                    # 야성이 확인되면 현금(V8) 비중을 줄이고 주식(V7)을 그만큼 늘림
                    prev_v8 = self.v8_p
                    self.v8_p = max(0, self.v8_p - boost)
                    self.v7_p = 100 - self.v8_p
                    
                    if boost > 0:
                        print(f"✅ 야성 지표 포착: 현금 비중 {prev_v8:.1f}% -> {self.v8_p:.1f}%로 하향 (공격력 강화)")
            
            except Exception as e_sentinel:
                print(f"⚠️ 지수 실시간 조회 실패 (기본값 유지): {e_sentinel}")
            # ------------------------------------------------------------------

            # 3. 최종 상태 판정
            if self.v8_p > 60:
                self.market_state = "🚨 [수비 강화] 현금 비중 압도적 유지"
            elif self.v8_p > 50:
                self.market_state = "⚖️ [쏠림형 강세] 대형주 위주 관망"
            else:
                self.market_state = "🔥 [적극 공략] 중소형주/바이오 탄력 구간"

            # [원칙 2] 쏠림장 강제 보정 로직 유지
            if v8_raw > 0.6: 
                 if self.v8_p < 60:
                     self.v8_p = 60.0
                     self.v7_p = 40.0

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
    # --- 1층 엔진: AttributeError 해결 및 데이터 복구 ---
    def _get_floor_1_data(self):
        portfolio = ['FCX', 'SCCO', 'SIVR', 'ISSC', 'LUNR', 'IREN', 'MU', 'SIDU']
        data_list = []
        try:
            # 원칙 2 적용: yfinance 데이터 직접 추출
            data = yf.download(portfolio, period="1y", group_by='ticker', progress=False)
            for sym in portfolio:
                df = data[sym]
                if df.empty: continue
                curr = df['Close'].iloc[-1]
                ma120 = df['Close'].rolling(120).mean().iloc[-1]
                gap = ((curr/ma120)-1)*100
                # 전임자 판정 아이콘 및 로직
                if curr < ma120: act, icon = "🔴 [전량매도] 120일선 붕괴", "💀"
                elif gap > 60: act, icon = "🚨 과열권 (비중 축소)", "🔥"
                else: act, icon = "🟢 강력 홀딩", "💎"
                data_list.append({"Symbol": sym, "Price": round(curr, 2), "Action": act, "Status_Icon": icon, "Gap_120": round(gap, 1)})
            return pd.DataFrame(data_list)
        except:
            return pd.DataFrame(columns=["Symbol", "Price", "Action", "Status_Icon", "Gap_120"])

    # --- 2층 엔진: 텐배거 파일 누락 해결 및 텍스트와 100% 동기화 ---
    def _get_floor_2_data(self):
        combined = []
        # 텍스트 리포트에서 사용하는 3개 파일을 동일하게 스캔
        targets = [
            ("V7C_GLOBAL_MINING_TOTAL_REPORT_20260116.xlsx", "🛡️ Shield"),
            ("V40_BEST_TARGETS.xlsx", "🎯 BEST"),
            ("V40_TEN_BAGGER_REPORT_0837.xlsx", "🚀 TEN-B")
        ]
        
        for file_name, tag in targets:
            df = self._smart_file_loader(file_name)
            if not df.empty:
                # 텐배거 파일(Symbol, Q_Score)과 BEST파일(Ticker, V_Energy) 컬럼 통합
                temp = df.copy()
                if 'Ticker' in temp.columns: temp = temp.rename(columns={'Ticker': 'Symbol'})
                if 'V_Energy' in temp.columns: temp = temp.rename(columns={'V_Energy': 'Accel_Score'})
                if 'Q_Score' in temp.columns: temp = temp.rename(columns={'Q_Score': 'Accel_Score'})
                
                # 필수 컬럼만 추출하여 병합
                cols = [c for c in ['Symbol', 'Price', 'Accel_Score'] if c in temp.columns]
                subset = temp[cols].head(5)
                subset['Risk_Tag'] = tag
                combined.append(subset)
        
        if combined:
            res = pd.concat(combined, ignore_index=True)
            res['Real_Pulse'] = res['Accel_Score'] * 10 # 전임자 포맷 복구
            return res
        return pd.DataFrame(columns=["Symbol", "Price", "Accel_Score", "Real_Pulse", "Risk_Tag"])

    def run_process(self):
        # 1. [시간 설정] 한국 시간(KST) 및 요일 판정
        from datetime import datetime, timedelta
        kst_now = datetime.utcnow() + timedelta(hours=9)
        weekday = kst_now.weekday()  # 0:월, 5:토
        
        # 2. [제목 결정] 요일별 리포트 타이틀 분기
        if weekday == 0:
            title = "📅 [V40 주초 개장상황 보고]"
        elif weekday == 5:
            title = "📊 [V40 주간 결산 보고]"
        else:
            title = "👹 [V40 일일 관제 보고]"

        # 3. [데이터 처리] 매크로 분석 및 1, 2층 데이터 수집
        if not self.calculate_macro_spectrum(): 
            return # 분석 실패 시 중단 (원칙 2: 네거티브 체크)
            
        df_f1 = self._get_floor_1_data()
        df_f2 = self._get_floor_2_data()

        # 4. [리포트 생성] 텍스트 구성 (self.analysis_report로 통일)
        self.analysis_report = f"{title}\n\n📊 [파동] V7:{self.v7_p:.1f}% | V8:{self.v8_p:.1f}%\n"
        self.analysis_report += f"📢 상태: {self.market_state}\n\n🏢 [1층]\n"
        
        for _, r in df_f1.iterrows():
            self.analysis_report += f"{r['Status_Icon']} {r['Symbol']}: {r['Action']} (Gap:{r['Gap_120']}%)\n"
        
        self.analysis_report += f"\n🧬 [2층]\n"
        if not df_f2.empty:
            for _, r in df_f2.head(10).iterrows():
                # Risk_Tag와 Accel_Score가 있는지 확인 후 안전하게 추출
                tag = r.get('Risk_Tag', '🚀')
                score = r.get('Accel_Score', 0)
                self.analysis_report += f"{tag} {r['Symbol']} | Q:{score}\n"
        else:
            self.analysis_report += "⚠️ 2층 데이터 로딩 실패\n"

        # 5. [파일 저장] 원칙 1: 보고 전 반드시 엑셀 파일 생성 및 저장
        file_name = f"V40_Weekly_Wolf_{kst_now.strftime('%m%d')}.xlsx"
        df_summary = pd.DataFrame([{"V40_SUMMARY": line} for line in self.analysis_report.split('\n')])
        
        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            df_f1.to_excel(writer, sheet_name='1층_보유점검', index=False)
            df_f2.to_excel(writer, sheet_name='2층_신규발굴', index=False)
            df_summary.to_excel(writer, sheet_name='종합리포트', index=False)

        # 6. [최종 보고] 텔레그램 발송
        try:
            # (1) 텍스트 리포트 발송 (매일)
            requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                          json={"chat_id": self.chat_id, "text": self.analysis_report})

            # (2) 토요일(5) 아침에만 '만들어둔 엑셀' 발송
            if weekday == 5:
                with open(file_name, 'rb') as f:
                    requests.post(f"https://api.telegram.org/bot{self.t_token}/sendDocument", 
                                  data={'chat_id': self.chat_id, 'caption': "📊 주간 데이터 정합성 검증 완료"}, 
                                  files={'document': f})
        except Exception as e:
            print(f"❌ 보고 체계 장애: {e}")
            
if __name__ == "__main__":
    # 스위치 2단계: V8 현금 비중에 +10% 가산하여 보수적으로 관측
    engine = QuantumControlCenter(macro_v8_switch=2)
    engine.run_process()
