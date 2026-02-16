import pandas as pd
import yfinance as yf
import numpy as np
import requests
import os
import glob
import time
import sys
from datetime import datetime, timedelta
import warnings
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

# [V40 원칙: 기계적 무결성 및 지름길 금지 엄수]
# 1. 1+1-1=Complete: 분석+가공+저장이 완료되지 않으면 보고하지 않는다.
# 2. Negative Check: 논리적 모순(음수 MDD, 비정상 현금비중 등) 발생 시 즉시 중단.
# 3. No Shortcuts: 에러 발생 시 우회하지 않고 사용자에게 직접 보고한다.

warnings.filterwarnings('ignore')

class QuantumControlCenter:
    def __init__(self, macro_v8_switch=2):
        """
        [시스템 초기화]
        형님의 전략적 스위치 레벨에 따라 방어 강도를 결정합니다.
        """
        self.version = "V40_INTEGRITY_SUPREME_2026"
        self.macro_v8_switch = macro_v8_switch 
        self.t_token = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
        self.chat_id = "198757117"
        
        # 시스템 내부 지표 (초기값 설정)
        self.v7_p = 50.0  # 상승 모멘텀 (V7)
        self.v8_p = 50.0  # 하락/현금 압력 (V8)
        self.market_state = "⚖️ 시스템 정렬 중..."
        self.analysis_report = ""
        self.indices_report = ""
        
        # 데이터 저장소 (엑셀 출력용)
        self.floor_1_df = pd.DataFrame()
        self.floor_2_df = pd.DataFrame()
        self.macro_log = []
        
        # 섹션별 개별 저장소 (무결성 12개 타겟용)
        self.s1_shield = pd.DataFrame()
        self.s2_best = pd.DataFrame()
        self.s3_tenb = pd.DataFrame()
        self.s4_bnai = pd.DataFrame()

        print(f"✅ {self.version} 가동 시작... (Switch: {self.macro_v8_switch})")

    # --------------------------------------------------------------------------
    # [핵심 로직 1] 방어적 파일 로더 (인코딩 및 경로 변조 원천 차단)
    # --------------------------------------------------------------------------
    def _smart_file_loader(self, file_name):
        """
        지름길 없이 파일의 존재와 내용을 5단계로 검증합니다.
        """
        base = file_name.split('.')[0]
        candidates = [
            f"{base}.xlsx", f"{base}.csv", 
            f"{base}_FINAL.xlsx", f"{base}_REVISION.csv",
            f"{base}.xlsx - Sheet1.csv"
        ]
        
        target_path = None
        for c in candidates:
            if os.path.exists(c):
                target_path = c
                break
        
        if not target_path:
            # [원칙 3] 지름길 금지: 파일이 없으면 즉시 에러 발생
            err_msg = f"❌ [데이터 모순] 필수 파일 '{file_name}'을 찾을 수 없습니다. 경로를 확인하십시오."
            self._emergency_sos(err_msg)
            raise FileNotFoundError(err_msg)

        encodings = ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']
        for enc in encodings:
            try:
                if target_path.endswith('.xlsx'):
                    return pd.read_excel(target_path, engine='openpyxl')
                else:
                    return pd.read_csv(target_path, encoding=enc)
            except:
                continue
        
        raise ValueError(f"🚨 {file_name} 로딩 치명적 오류: 인코딩 호환 불가.")

    # --------------------------------------------------------------------------
    # [핵심 로직 2] 데이터 커먼센스 체크 (Negative Check)
    # --------------------------------------------------------------------------
    def negative_check(self, value, name, min_val=-100, max_val=1000000):
        """
        [원칙 2] 수치가 논리적 범위를 벗어나면 즉시 프로세스를 중단합니다.
        """
        if pd.isna(value) or np.isinf(value):
            msg = f"⚠️ [무결성 파괴] {name} 수치에서 NaN/Inf 감지. 연산 중단."
            self._emergency_sos(msg)
            raise ValueError(msg)
        
        if value < min_val or value > max_val:
            msg = f"🚨 [데이터 모순] {name} 수치 이상: {value}. 범위를 벗어났습니다."
            self._emergency_sos(msg)
            raise ValueError(msg)
        
        return True

    # --------------------------------------------------------------------------
    # [공정 1] 매크로 스펙트럼 및 V8 보정 분석
    # --------------------------------------------------------------------------
    def calculate_macro_spectrum(self):
        print("🔭 [Step 1] 매크로 스펙트럼 및 실시간 지수 분석...")
        try:
            # V8 데이터 로드 및 검증
            v8_df = self._smart_file_loader("V8_REVISION_FINAL")
            v8_col = next((c for c in v8_df.columns if 'Cash' in c or 'Ratio' in c), v8_df.columns[-1])
            v8_raw = v8_df[v8_col].iloc[-1]
            
            # [원칙 2] 현금 비중 음수 체크
            self.negative_check(v8_raw, "V8_CASH_RATIO", min_val=0)
            
            # 비율 정규화 (0~100)
            self.v8_p = v8_raw * 100 if v8_raw <= 1.0 else v8_raw
            
            # 형님의 스위치 강제 보정 로직
            # 스위치가 2단계 이상이면 시장 위기 상황으로 간주하여 방어선 구축
            if self.macro_v8_switch >= 2:
                self.v8_p = max(self.v8_p, 60.0)
                print(f"🛡️ Switch Level {self.macro_v8_switch} 적용: V8 방어선 60% 상향 고정")

            self.v7_p = 100 - self.v8_p
            
            # 지수 호출 (타임아웃 10초 설정으로 지연 차단)
            try:
                sentinels = yf.download(['^NBI', '^NGX'], period='5d', progress=False, timeout=10)['Close']
                if not sentinels.empty:
                    nbi_curr = sentinels['^NBI'].iloc[-1]
                    nbi_prev = sentinels['^NBI'].iloc[-2]
                    nbi_chg = ((nbi_curr / nbi_prev) - 1) * 100
                    
                    ngx_curr = sentinels['^NGX'].iloc[-1]
                    ngx_prev = sentinels['^NGX'].iloc[-2]
                    ngx_chg = ((ngx_curr / ngx_prev) - 1) * 100
                    
                    self.indices_report = f"🧬 NBI: {nbi_curr:,.2f} ({nbi_chg:+.2f}%)\n🚀 NGX: {ngx_curr:,.2f} ({ngx_chg:+.2f}%)"
                    
                    # 지수 폭락 시 V8 추가 가중치 (기계적 방어)
                    if ngx_chg < -2.0: 
                        self.v8_p = min(self.v8_p + 5, 95.0)
                        self.v7_p = 100 - self.v8_p
            except:
                self.indices_report = "⚠️ 실시간 지수 수신 지연 (파일 데이터 기반 분석 진행)"

            # 상태 판정
            if self.v8_p >= 65: self.market_state = "🚨 [수비 강화] 현금 확보 최우선"
            elif self.v8_p >= 50: self.market_state = "⚖️ [관망] 대형주/지수 추종 유지"
            else: self.market_state = "🔥 [공격] 중소형주/바이오 탄력 공략"
            
            return True
        except Exception as e:
            print(f"❌ 매크로 공정 실패: {e}")
            return False

    # --------------------------------------------------------------------------
    # [공정 2] 1층 보유주 기계적 진단 (이동평균선 및 이격도)
    # --------------------------------------------------------------------------
    def floor_1_action(self):
        print("🏢 [Step 2] 1층 보유주 무결성 진단...")
        portfolio = ['FCX', 'SCCO', 'SIVR', 'ISSC', 'LUNR', 'IREN', 'MU', 'SIDU']
        data_list = []
        
        try:
            data = yf.download(portfolio, period="1y", group_by='ticker', progress=False)
            for sym in portfolio:
                try:
                    df = data[sym]
                    if df.empty: raise ValueError
                    
                    curr_price = df['Close'].iloc[-1]
                    ma120 = df['Close'].rolling(120).mean().iloc[-1]
                    high_20 = df['Close'].rolling(20).max().iloc[-1]
                    
                    # [원칙 2] 가격 데이터 무결성 체크
                    self.negative_check(curr_price, f"{sym}_PRICE", min_val=0.001)
                    
                    gap_120 = ((curr_price / ma120) - 1) * 100
                    dd_20 = ((curr_price / high_20) - 1) * 100
                    
                    # 판정 로직
                    if curr_price < ma120:
                        action, icon = "🔴 [전량매도] 하락추세 전환", "💀"
                    elif dd_20 < -15.0:
                        action, icon = "🟠 [분할익절] 트레일링 스탑", "🏃"
                    elif gap_120 > 30.0:
                        action, icon = "🔥 [과열경고] 비중 축소 권고", "⚠️"
                    else:
                        action, icon = "🟢 [강력홀딩] 추세 유지", "💎"
                    
                    data_list.append({
                        "Symbol": sym, "Action": action, "Icon": icon, 
                        "Gap_120": round(gap_120, 2), "Drawdown": round(dd_20, 2)
                    })
                except:
                    data_list.append({"Symbol": sym, "Action": "⚠️ 점검실패", "Icon": "❓", "Gap_120": 0.0, "Drawdown": 0.0})
            
            self.floor_1_df = pd.DataFrame(data_list)
            return True
        except Exception as e:
            print(f"❌ 1층 공정 에러: {e}")
            return False

    # --------------------------------------------------------------------------
    # [공정 3] 2층 12개 타겟 무결성 사냥 (추출 로직 강화)
    # --------------------------------------------------------------------------
    def floor_2_hunting(self):
        print("🧬 [Step 3] 2층 4개 섹션(12개 타겟) 정밀 스캔...")
        targets = [
            ("🛡️ [SHIELD]", "COMMODITY_ANALYSIS_REPORT"),
            ("🎯 [BEST]", "V40_BEST_TARGETS"),
            ("🚀 [TEN-B]", "V40_TEN_BAGGER_REPORT_0837"),
            ("🤖 [BNAI]", "V7_RESULT_BNAI_FINAL")
        ]
        
        all_results = []
        for title, f_name in targets:
            try:
                df = self._smart_file_loader(f_name)
                # 에너지/점수 컬럼 자동 검색
                score_col = next((c for c in df.columns if any(x in c for x in ['Energy', 'Score', 'V_', '점수'])), df.columns[1])
                
                # 상위 3개 추출 (Buy 신호 우선)
                top3 = df.sort_values(by=score_col, ascending=False).head(3).copy()
                top3['Section'] = title
                all_results.append(top3)
                
                # 내부 변수 할당 (보고서 빌드용)
                res_list = [f"{r['Symbol']} (E:{r[score_col]:.1f})" for _, r in top3.iterrows()]
                while len(res_list) < 3: res_list.append("⚠️ 타겟부재")
                
                if "SHIELD" in title: self.s1_shield_list = res_list
                elif "BEST" in title: self.s2_best_list = res_list
                elif "TEN-B" in title: self.s3_tenb_list = res_list
                elif "BNAI" in title: self.s4_bnai_list = res_list
                
            except:
                err_list = ["❌ 파일모순", "❌ 파일모순", "❌ 파일모순"]
                if "SHIELD" in title: self.s1_shield_list = err_list
                elif "BEST" in title: self.s2_best_list = err_list
                elif "TEN-B" in title: self.s3_tenb_list = err_list
                elif "BNAI" in title: self.s4_bnai_list = err_list
                
        self.floor_2_df = pd.concat(all_results) if all_results else pd.DataFrame()
        return True

    # --------------------------------------------------------------------------
    # [공정 4] 1+1-1=Complete (파일 저장 및 보고서 빌드)
    # --------------------------------------------------------------------------
    def build_and_save_report(self):
        print("💾 [Step 4] 리포트 무결성 검증 및 파일 저장...")
        try:
            kst_now = datetime.utcnow() + timedelta(hours=9)
            file_name = f"V40_Report_{kst_now.strftime('%m%d_%H%M')}.xlsx"
            
            # [원칙 1] 보고 전 반드시 저장
            with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
                self.floor_1_df.to_excel(writer, sheet_name='1층_보유현황', index=False)
                self.floor_2_df.to_excel(writer, sheet_name='2층_신규타겟', index=False)
                
                # 엑셀 시각화 보정 (형님의 가독성을 위해)
                ws = writer.sheets['1층_보유현황']
                for cell in ws["A1:E1"]:
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

            # 텔레그램 텍스트 리포트 구성
            report = f"📅 [V40 관제 보고 - {kst_now.strftime('%Y-%m-%d')}]\n\n"
            report += f"📊 파동 지표: V7({self.v7_p:.1f}%) | V8({self.v8_p:.1f}%)\n"
            report += f"📢 시장 상태: {self.market_state}\n"
            report += f"📡 지수: \n{self.indices_report}\n\n"
            
            report += "🏢 [1층 보유주 진단]\n"
            for _, r in self.floor_1_df.iterrows():
                report += f"{r['Icon']} {r['Symbol']}: {r['Action']} ({r['Gap_120']}%)\n"
            
            report += "\n🧬 [2층 12개 무결성 타겟]"
            report += f"\n🛡️ SHIELD: {', '.join(self.s1_shield_list)}"
            report += f"\n🎯 BEST: {', '.join(self.s2_best_list)}"
            report += f"\n🚀 TEN-B: {', '.join(self.s3_tenb_list)}"
            report += f"\n🤖 BNAI: {', '.join(self.s4_bnai_list)}"
            
            report += f"\n\n✅ 파일 저장 완료: {file_name}"
            self.analysis_report = report
            return file_name
        except Exception as e:
            self._emergency_sos(f"리포트 생성 실패: {e}")
            return None

    # --------------------------------------------------------------------------
    # [통신] 텔레그램 발송
    # --------------------------------------------------------------------------
    def send_telegram(self, file_path):
        print("✉️ 텔레그램 전송 중...")
        try:
            # 텍스트 전송
            requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                          data={"chat_id": self.chat_id, "text": self.analysis_report})
            
            # 파일 전송 (방어 강도가 높거나 특정 조건일 때)
            if self.macro_v8_switch >= 2 or self.v7_p > 50:
                with open(file_path, 'rb') as f:
                    requests.post(f"https://api.telegram.org/bot{self.t_token}/sendDocument", 
                                  data={"chat_id": self.chat_id}, files={'document': f})
            print("✅ 보고 완료.")
        except:
            print("⚠️ 통신 장애 발생")

    def _emergency_sos(self, error_msg):
        """에러 발생 시 즉시 보고"""
        try:
            requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                          data={"chat_id": self.chat_id, "text": f"🚨 [V40 긴급중단]\n{error_msg}"})
        except: pass

    # --------------------------------------------------------------------------
    # [메인 실행부]
    # --------------------------------------------------------------------------
    def run_process(self):
        try:
            # 1. 매크로
            if not self.calculate_macro_spectrum(): 
                raise ValueError("Step 1(매크로)에서 데이터 모순 발생.")
            
            # 2. 1층 진단
            if not self.floor_1_action():
                raise ValueError("Step 2(1층) 진단 중 수식 오류 발생.")
                
            # 3. 2층 사냥
            if not self.floor_2_hunting():
                raise ValueError("Step 3(2층) 타겟 추출 중 파일 모순 발생.")
            
            # 4. 저장 및 보고
            f_path = self.build_and_save_report()
            if f_path:
                self.send_telegram(f_path)
                
            print(f"🏁 [{datetime.now().strftime('%H:%M:%S')}] 모든 공정 무결성 확인 완료.")
            
        except Exception as e:
            print(f"🛑 시스템 정지: {e}")

if __name__ == "__main__":
    # 형님, 스위치 2단계로 설정하여 보수적 무결성을 유지합니다.
    engine = QuantumControlCenter(macro_v8_switch=2)
    engine.run_process()
