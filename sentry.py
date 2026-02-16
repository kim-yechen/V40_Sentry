import pandas as pd
import yfinance as yf
import numpy as np
import requests
import os
import glob
import time
from datetime import datetime, timedelta
import warnings
from openpyxl import Workbook

# [V40 원칙: 기계적 무결성 및 지름길 금지]
warnings.filterwarnings('ignore')

class QuantumControlCenter:
    def __init__(self, macro_v8_switch=0):
        """
        초기화 단계: 시스템의 심장부 설정
        - macro_v8_switch: 시장 위기 시 수동 개입 계수
        """
        self.macro_v8_switch = macro_v8_switch 
        self.t_token = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
        self.chat_id = "198757117"
        
        # 시스템 내부 지표
        self.v7_p = 50.0 # 상승(바이오/중소형) 에너지
        self.v8_p = 50.0 # 하락(현금/방어) 압력
        self.market_state = "⚖️ 시스템 초기화 중..."
        self.analysis_report = ""
        
        # [원칙 1 준수] 파일 저장을 위한 버퍼
        self.floor_1_df = pd.DataFrame()
        self.floor_2_df = pd.DataFrame()
        
        print(f"🚀 V40 시스템 기동 (Switch Level: {self.macro_v8_switch})")

    def _smart_file_loader(self, file_name):
        """
        [방어 로직] 인코딩 지옥과 파일명 변조를 원천 차단하는 중장갑 로더
        - 형님의 원본 데이터 무결성을 위해 5단계 로딩 시도
        """
        base = file_name.split('.')[0]
        # 확장자 및 시트명 변조 대응 후보군
        candidates = [
            file_name, 
            f"{base}.xlsx", 
            f"{base}.csv", 
            f"{base}.xlsx - Sheet1.csv",
            f"{base}_FINAL.xlsx",
            f"{base}_REVISION.csv"
        ]
        
        target_path = None
        for c in candidates:
            if os.path.exists(c):
                target_path = c
                break
        
        if not target_path:
            # [원칙 3] 지름길 금지: 파일 없으면 가짜 데이터 만들지 말고 즉시 보고 중단
            raise FileNotFoundError(f"❌ 필수 데이터 누락: {file_name} 파일이 경로에 없습니다.")

        # 인코딩 파상 공세 (EUC-KR, CP949 등 모든 한국어 엑셀 변종 대응)
        encodings = ['utf-8-sig', 'cp949', 'utf-8', 'latin1', 'euc-kr']
        for enc in encodings:
            try:
                if target_path.endswith('.xlsx'):
                    return pd.read_excel(target_path, engine='openpyxl')
                return pd.read_csv(target_path, encoding=enc)
            except Exception:
                continue
        
        # 마지막 수단: 엔진 강제 지정
        try:
            return pd.read_excel(target_path, engine='openpyxl')
        except Exception as e:
            raise ValueError(f"🚨 {file_name} 로딩 치명적 실패: {e}")

    def negative_check(self, value, name, min_limit=-100, max_limit=1000000):
        """
        [원칙 2] 데이터 커먼센스 체크
        - MDD가 양수가 나오거나, 현금비중이 음수가 되는 '기계적 에러' 차단
        """
        if pd.isna(value):
            raise ValueError(f"⚠️ {name} 수치에 NaN(결측치) 감지. 연산 불능.")
        if value < min_limit or value > max_limit:
            raise ValueError(f"🚨 {name} 수치 이상: {value} (논리적 범위를 벗어남)")
        return True

    def calculate_macro_spectrum(self):
        """
        1단계: 매크로 스펙트럼 분석
        - 지수 호출은 10초 컷! 하지만 파일 분석은 0.1%까지 정밀하게 수행.
        """
        print("🔭 [Step 1] 매크로 정찰병 투입 (지수 호출 최대 10초 대기)...")
        self.indices_report = "🧬 NBI: 수신 실패(파일 데이터 기준)\n🚀 NGX: 수신 실패(파일 데이터 기준)" # 기본값
        
        try:
            # --- [Part A: 파일 데이터 정밀 분석] ---
            # 지수 호출 실패해도 이 부분은 절대 대충 넘기지 않습니다.
            v7_df = self._smart_file_loader("V7_RESULT_BNAI_FINAL")
            v8_df = self._smart_file_loader("V8_REVISION_FINAL")
            
            v8_col = 'Recommended_Cash_Ratio' if 'Recommended_Cash_Ratio' in v8_df.columns else 'V8_NextGen_Cash'
            v8_raw = v8_df[v8_col].iloc[-1]
            
            # [원칙 2] 현금 비중 검증 (기계적 에러 차단)
            self.negative_check(v8_raw, "V8_RAW_DATA", min_limit=0)
            
            # 파동 계산
            self.v8_p = v8_raw * 100 if v8_raw <= 1.0 else v8_raw
            self.v7_p = 100 - self.v8_p 

            # --- [Part B: 실시간 지수 호출 (타임아웃 10초)] ---
            try:
                # timeout=10으로 4분 동안 멍 때리는 현상 방어
                sentinels = yf.download(['^NBI', '^NGX'], period='5d', progress=False, timeout=10)['Close']
                
                if not sentinels.empty and len(sentinels) >= 2:
                    nbi_v = sentinels['^NBI'].iloc[-1]
                    ngx_v = sentinels['^NGX'].iloc[-1]
                    
                    # 전일 대비 등락률 계산 및 nan 방어
                    nbi_c = ((nbi_v / sentinels['^NBI'].iloc[-2]) - 1) * 100
                    ngx_c = ((ngx_v / sentinels['^NGX'].iloc[-2]) - 1) * 100
                    
                    # 수치 무결성 체크 (nan일 경우 0.0)
                    nbi_c = 0.0 if np.isnan(nbi_c) else nbi_c
                    ngx_c = 0.0 if np.isnan(ngx_c) else ngx_c
                    
                    self.indices_report = f"🧬 NBI: {nbi_v:,.2f} ({nbi_c:+.1f}%)\n🚀 NGX: {ngx_v:,.2f} ({ngx_c:+.1f}%)"
                    
                    # 지수 상태에 따른 가산점 보정 (파일 데이터만 쓰는 것보다 정밀함 추가)
                    if nbi_c > 0.5: self.v7_p += 2.0
                    if ngx_c < -0.5: self.v8_p += 2.0
            except Exception as e:
                print(f"⚠️ 지수 호출만 건너뜁니다 (이유: {e})")

            # --- [Part C: 최종 무결성 확보 및 판정] ---
            # 가산점 후에도 0~100 범위를 넘지 않게 조정
            self.v8_p = max(5.0, min(95.0, self.v8_p))
            self.v7_p = 100 - self.v8_p

            # 상태 판정 로직
            if self.v8_p > 60:
                self.market_state = "🚨 [수비 강화] 현금 비중 압도적 유지"
            elif self.v8_p > 50:
                self.market_state = "⚖️ [쏠림형 강세] 대형주 위주 관망"
            else:
                self.market_state = "🔥 [적극 공략] 중소형주/바이오 탄력 구간"

            # 형님의 스위치 강제 보정 로직 (V8이 0.6 이상이면 강제 60% 고정)
            if v8_raw > 0.6 and self.v8_p < 60:
                self.v8_p, self.v7_p = 60.0, 40.0

            return True

        except Exception as e:
            # 파일이 없거나 데이터가 깨졌을 때만 '진짜 실패' 보고
            print(f"❌ 매크로 분석 치명적 실패: {e}")
            return False

    def floor_1_action(self):
        """
        2단계: 1층 보유주 관리
        - 트레일링 스탑 및 동적 이격도 제한 적용
        """
        print("🏢 [Step 2] 1층 보유주 보유 여부 검진...")
        portfolio = ['FCX', 'SCCO', 'SIVR', 'ISSC', 'LUNR', 'IREN', 'MU', 'SIDU']
        data_list = []
        
        try:
            # [원칙 3] 지름길 금지: 실시간 데이터 확보
            data = yf.download(portfolio, period="1y", group_by='ticker', progress=False)
            
            # 형님의 핵심 수식: 시장 압박(V8)에 따른 이격도 한계값 설정
            dynamic_limit = max(0.2, 0.7 - (self.v8_p * 0.006)) 
            
            for sym in portfolio:
                df = data[sym]
                if df.empty: continue
                
                curr = df['Close'].iloc[-1]
                ma120 = df['Close'].rolling(120).mean().iloc[-1]
                recent_high = df['Close'].rolling(20).max().iloc[-1]
                
                # [원칙 2] 네거티브 체크: 현재가가 0 이하일 수 없음
                self.negative_check(curr, f"{sym}_PRICE", min_limit=0.0001)
                
                drawdown = (curr / recent_high - 1) * 100
                gap_120 = (curr / ma120 - 1) * 100
                
                # 판정 로직 (형님의 기준 엄수)
                if curr < ma120:
                    action, icon = "🔴 [전량매도] 120일선 붕괴", "💀"
                elif drawdown < -12.0:
                    action, icon = f"🟠 [트레일링 스탑] 고점대비 {drawdown:.1f}% 하락", "🏃"
                elif (curr/ma120 - 1) > dynamic_limit:
                    action, icon = f"🚨 과열권 진입 (비중 {int(self.v8_p)}% 축소)", "🔥"
                else:
                    action, icon = "🟢 강력 홀딩", "💎"
                
                data_list.append({
                    "Symbol": sym, "Price": round(curr, 2), "Action": action, 
                    "Status_Icon": icon, "Gap_120": round(gap_120, 1), "DD": round(drawdown, 1)
                })
            
            self.floor_1_df = pd.DataFrame(data_list)
            return True
        except Exception as e:
            print(f"❌ 1층 분석 실패: {e}")
            return False

    def floor_2_hunting(self):
        """
        [무결성 검증] 3단계: 2층 신규 타켓 발굴
        - 로직 통합: Buy 신호 우선 필터링 + 부족 시 상위 종목 강제 추출 + 사유 기록
        """
        print("🧬 [Step 3] 2층 신규 타겟 정밀 스캔 및 로직 통합 중...")
        try:
            # 1. 파일 로드 (Shield 분석용 v7c 포함)
            v7c = self._smart_file_loader("COMMODITY_ANALYSIS_REPORT")
            v40_best = self._smart_file_loader("V40_BEST_TARGETS")
            v40_ten = self._smart_file_loader("V40_TEN_BAGGER_REPORT_0837")
            
            self.best_summary = ""
            self.ten_summary = ""
            combined_for_excel = [] 

            # --- [섹션 1: BEST TARGETS 필터링] ---
            # Status 컬럼 찾기
            best_status_col = [c for c in v40_best.columns if any(x in c for x in ['Status', 'Decision', '결정'])]
            if best_status_col:
                # 1순위: Buy 신호만 필터링
                best_buys = v40_best[v40_best[best_status_col[0]].str.contains('Buy', na=False, case=False)].copy()
                self.best_summary = f"({len(best_buys)}개 Buy 포착)"
                
                # 2순위: Buy가 부족하면? 그냥 상위 에너지 순으로 3개 채움 (형님 요청)
                if len(best_buys) < 3:
                    display_list = v40_best.sort_values(by='V_Energy', ascending=False).head(3).copy()
                else:
                    display_list = best_buys.sort_values(by='V_Energy', ascending=False).head(3).copy()
                
                self.best_targets_list = display_list
                
                # 엑셀 저장용 데이터 구성
                temp_best = display_list.copy()
                temp_best['Source'] = '🎯 BEST'
                combined_for_excel.append(temp_best)
            else:
                self.best_targets_list = pd.DataFrame()
                self.best_summary = "(Status 컬럼 확인불가)"

            # --- [섹션 2: TEN-BAGGER 필터링] ---
            ten_status_col = [c for c in v40_ten.columns if any(x in c for x in ['Status', 'Decision', '결정'])]
            if ten_status_col:
                # 1순위: Buy 신호 필터링
                ten_buys = v40_ten[v40_ten[ten_status_col[0]].str.contains('Buy', na=False, case=False)].copy()
                self.ten_summary = f"({len(ten_buys)}개 Buy 포착)"
                
                # 점수 컬럼 유연하게 찾기
                e_col_ten = 'Q_Score' if 'Q_Score' in v40_ten.columns else [c for c in v40_ten.columns if 'Score' in c or '점수' in c][0]
                
                # 2순위: Buy 부족 시 상위 점수 순 3개 강제 추출
                if len(ten_buys) < 3:
                    display_ten = v40_ten.sort_values(by=e_col_ten, ascending=False).head(3).copy()
                else:
                    display_ten = ten_buys.sort_values(by=e_col_ten, ascending=False).head(3).copy()
                
                self.ten_targets_list = display_ten
                
                # 엑셀 저장용 데이터 구성
                temp_ten = display_ten.copy()
                temp_ten['Source'] = '🚀 TEN-B'
                combined_for_excel.append(temp_ten)
            else:
                self.ten_targets_list = pd.DataFrame()
                self.ten_summary = "(Status 컬럼 확인불가)"

            # --- [섹션 3: Shield 데이터 통합 (선택사항)] ---
            if 'Grade' in v7c.columns:
                shield = v7c[v7c['Grade'].str.contains('Shield|A', na=False)].head(3).copy()
                if not shield.empty:
                    shield['Source'] = '🛡️ Shield'
                    combined_for_excel.append(shield)

            # --- [원칙 1] 데이터 통합 및 저장 준비 ---
            if combined_for_excel:
                self.floor_2_df = pd.concat(combined_for_excel, ignore_index=True)
            else:
                self.floor_2_df = pd.DataFrame(columns=['Symbol', 'V_Energy', 'Source'])

            return True

        except Exception as e:
            print(f"❌ 2층 분석 실패: {e}")
            return False
            
    def build_and_save_report(self):
        """
        [원칙 1] 1+1-1=Complete
        [수정] 중복 코드 제거 및 리턴 위치 정상화 (부족 시 사유 보고 포함)
        """
        kst_now = datetime.utcnow() + timedelta(hours=9)
        file_name = f"V40_Integrated_Report_{kst_now.strftime('%m%d_%H%M')}.xlsx"
        
        # 1. [원칙 1] 분석 데이터를 엑셀로 저장 (파일 저장이 최우선)
        try:
            with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
                if not self.floor_1_df.empty:
                    self.floor_1_df.to_excel(writer, sheet_name='1층_보유점검', index=False)
                if hasattr(self, 'floor_2_df') and not self.floor_2_df.empty:
                    self.floor_2_df.to_excel(writer, sheet_name='2층_신규발굴', index=False)
                
                macro_data = pd.DataFrame([{
                    "V7_Energy": self.v7_p, "V8_Cash": self.v8_p, 
                    "Market_State": self.market_state, "Report_Time": kst_now
                }])
                macro_data.to_excel(writer, sheet_name='시스템_파동', index=False)
            print(f"💾 [원칙 1] 데이터 저장 완료: {file_name}")
        except Exception as e:
            print(f"🚨 파일 저장 중 오류: {e}")
            return None

        # 2. 텔레그램용 리포트 텍스트 빌드
        weekday = kst_now.weekday()
        title = "📅 [V40 주초 개장상황 보고]" if weekday == 0 else "📊 [V40 주간 결산 보고]" if weekday == 5 else "👹 [V40 일일 관제 보고]"
        
        report = f"{title}\n\n"
        report += f"📊 [파동] V7:{self.v7_p:.1f}% | V8:{self.v8_p:.1f}%\n"
        report += f"📢 상태: {self.market_state}\n\n"
        
        report += "🏢 [1층 보유주 진단]\n"
        if not self.floor_1_df.empty:
            for _, r in self.floor_1_df.iterrows():
                report += f"{r['Status_Icon']} {r['Symbol']}: {r['Action']} (Gap:{r['Gap_120']}%)\n"
            
        report += f"\n🧬 [2층 신규 사냥터]\n"
        
        # --- [지수 라인: 상단 배치 및 nan 방어] ---
        indices = getattr(self, 'indices_report', "🧬 NBI: 수신 대기\n🚀 NGX: 수신 대기")
        indices = indices.replace('nan', '0.0')
        report += f"{indices}\n\n"

        # --- [BEST 출력: 부족하면 이유 보고] ---
        report += f"🎯 [BEST TARGETS] {getattr(self, 'best_summary', '')}\n"
        for i in range(3):
            if hasattr(self, 'best_targets_list') and i < len(self.best_targets_list):
                r = self.best_targets_list.iloc[i]
                report += f"  {i+1}. {r['Symbol']} | E:{r['V_Energy']:,.1f}\n"
            else:
                report += f"  {i+1}. ⚠️ [타겟 부재] 기준 만족 종목 없음\n"

        # --- [TEN-B 출력: 부족하면 이유 보고] ---
        report += f"\n🚀 [TEN-BAGGER] {getattr(self, 'ten_summary', '')}\n"
        for i in range(3):
            if hasattr(self, 'ten_targets_list') and i < len(self.ten_targets_list):
                r = self.ten_targets_list.iloc[i]
                # 에너지(점수) 컬럼 추출 안전장치
                score = r.get('Q_Score', r.get('V_Energy', 0))
                report += f"  {i+1}. {r['Symbol']} | E:{score:,.1f}\n"
            else:
                report += f"  {i+1}. ⚠️ [타겟 부재] 기준 만족 종목 없음\n"

        # 최종 리포트 저장 및 반환
        self.analysis_report = report
        return file_name # 여기서 모든 공정 종료

    def send_telegram(self, file_path):
        """[수정본] 초록불이든 빨간불이든, 형님께 보고는 무조건 합니다."""
        try:
            # 1. 텍스트 리포트 발송 (타임아웃 추가해서 무한대기 방지)
            requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                         json={"chat_id": self.chat_id, "text": self.analysis_report},
                         timeout=10)
            
            # 2. 파일 전송 조건 전면 수정
            # - 토요일(5)이거나 
            # - V7 에너지가 50을 넘는 '초록불' 상황이거나
            # - 형님이 스위치를 2 이상으로 올렸을 때 무조건 발송
            kst_now = datetime.utcnow() + timedelta(hours=9)
            if kst_now.weekday() == 5 or self.v7_p > 50 or self.macro_v8_switch >= 2:
                with open(file_path, 'rb') as f:
                    requests.post(f"https://api.telegram.org/bot{self.t_token}/sendDocument", 
                                 data={'chat_id': self.chat_id, 'caption': f"📊 V40 무결성 검증본 (V7:{self.v7_p:.1f}%)"}, 
                                 files={'document': f},
                                 timeout=20)
            print("✉️ 텔레그램 보고 완료")
        except Exception as e:
            print(f"❌ 보고 전송 장애: {e}")

    def run_process(self):
        """[수정본] 중간에 에러 나면 형님 텔레그램으로 '수정요청'을 직접 보냅니다."""
        try:
            if not self.calculate_macro_spectrum(): 
                raise ValueError("매크로 분석 실패")
            if not self.floor_1_action(): 
                raise ValueError("1층 보유주 진단 실패")
            if not self.floor_2_hunting(): 
                raise ValueError("2층 신규 사냥터 발굴 실패")
            
            report_file = self.build_and_save_report()
            if report_file:
                self.send_telegram(report_file)
            
            print("🏁 모든 공정 완료.")
            
        except Exception as e:
            # [원칙 3 준수] 에러 발생 시 즉시 형님께 SOS 텔레그램 발송
            error_msg = f"🚨 시스템 중단 알림\n내용: {e}\n\n📢 형님, 수식이나 파일 확인 부탁드립니다!"
            try:
                requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                             json={"chat_id": self.chat_id, "text": error_msg}, timeout=10)
            except:
                print("🚨 텔레그램 발송조차 실패했습니다.")
            print(f"\n🚨 에러 보고 완료: {e}")
            
            report_file = self.build_and_save_report()
            if report_file:
                self.send_telegram(report_file)
            
            print("🏁 모든 공정 완료.")
        except Exception as e:
            error_msg = f"🚨 시스템 중단 알림\n내용: {e}\n\n📢 형님, 수식이나 파일 확인 부탁드립니다!"
            requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                         json={"chat_id": self.chat_id, "text": error_msg})
            print(f"\n🚨 에러 보고 완료: {e}")

# --- 여기서부터는 클래스 밖입니다 ---
if __name__ == "__main__":
    # 스위치 2: 보수적 관점 유지
    engine = QuantumControlCenter(macro_v8_switch=2)
    engine.run_process()
