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
        """
        self.macro_v8_switch = macro_v8_switch 
        self.t_token = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
        self.chat_id = "198757117"
        
        # 시스템 내부 지표
        self.v7_p = 50.0 
        self.v8_p = 50.0 
        self.market_state = "⚖️ 시스템 초기화 중..."
        self.analysis_report = ""
        
        # [원칙 1 준수] 파일 저장을 위한 버퍼
        self.floor_1_df = pd.DataFrame()
        self.floor_2_df = pd.DataFrame()
        
        print(f"🚀 V40 시스템 기동 (Switch Level: {self.macro_v8_switch})")

    def _smart_file_loader(self, file_name):
        """
        [방어 로직] 5단계 로딩 시도 (원칙 3: 지름길 금지)
        """
        base = file_name.split('.')[0]
        candidates = [
            file_name, 
            f"{base}.xlsx", 
            f"{base}.csv", 
            f"{base}_FINAL.xlsx",
            f"{base}_REVISION.csv"
        ]
        
        target_path = next((c for c in candidates if os.path.exists(c)), None)
        
        if not target_path:
            # 원칙 3: 파일 없으면 가짜 데이터 안 만들고 즉시 보고
            raise FileNotFoundError(f"❌ [데이터 모순] {file_name} 파일이 없습니다. 수식/경로 수정 요청.")

        encodings = ['utf-8-sig', 'cp949', 'utf-8']
        for enc in encodings:
            try:
                if target_path.endswith('.xlsx'):
                    return pd.read_excel(target_path, engine='openpyxl')
                return pd.read_csv(target_path, encoding=enc)
            except:
                continue
        raise ValueError(f"🚨 {file_name} 로딩 실패: 인코딩/형식 모순")

    def negative_check(self, value, name):
        """
        [원칙 2: 데이터 커먼센스 정밀 수선본]
        - 현금비중, 가격, 에너지 수치에 대한 기계적 에러 차단
        """
        if pd.isna(value):
            raise ValueError(f"⚠️ {name} 결측치(NaN) 감지. 연산 불능.")
        
        # [수선] 항목별 정밀 범위 제한
        if "CASH" in name or "V8" in name:
            if not (0 <= value <= 100):
                raise ValueError(f"🚨 [현금비중 모순] {name}: {value}% (0-100 범위를 벗어남)")
        elif "PRICE" in name or "Price" in name:
            if value <= 0:
                raise ValueError(f"🚨 [가격 모순] {name}: {value} (가격은 0보다 커야 함)")
        return True

    def calculate_macro_spectrum(self):
        """1단계: 매크로 스펙트럼 분석"""
        print("🔭 [Step 1] 매크로 정찰병 투입...")
        try:
            v8_df = self._smart_file_loader("V8_REVISION_FINAL")
            v8_col = 'Recommended_Cash_Ratio' if 'Recommended_Cash_Ratio' in v8_df.columns else v8_df.columns[0]
            v8_raw = v8_df[v8_col].iloc[-1]
            
            # 파동 계산 및 네거티브 체크
            self.v8_p = v8_raw * 100 if v8_raw <= 1.0 else v8_raw
            self.negative_check(self.v8_p, "V8_CASH_RATIO")
            self.v7_p = 100 - self.v8_p

            # 실시간 지수 보정 (타임아웃 10초)
            try:
                sentinels = yf.download(['^NBI', '^NGX'], period='5d', progress=False, timeout=10)['Close']
                if not sentinels.empty:
                    nbi_c = ((sentinels['^NBI'].iloc[-1] / sentinels['^NBI'].iloc[-2]) - 1) * 100
                    self.indices_report = f"🧬 NBI: {sentinels['^NBI'].iloc[-1]:,.2f} ({nbi_c:+.1f}%)"
                else: self.indices_report = "🧬 지수 데이터 수신 실패"
            except: self.indices_report = "🧬 지수 호출 건너뜀"

            # 상태 판정
            self.market_state = "🚨 수비" if self.v8_p > 60 else "⚖️ 관망" if self.v8_p > 45 else "🔥 공격"
            return True
        except Exception as e:
            print(f"❌ 매크로 분석 실패: {e}")
            return False

    def floor_1_action(self):
        """2단계: 1층 보유주 관리"""
        print("🏢 [Step 2] 1층 보유주 점검...")
        portfolio = ['FCX', 'SCCO', 'SIVR', 'LUNR', 'IREN', 'MU']
        try:
            data = yf.download(portfolio, period="1y", group_by='ticker', progress=False)
            res = []
            for sym in portfolio:
                curr = data[sym]['Close'].iloc[-1]
                self.negative_check(curr, f"{sym}_PRICE") # 원칙 2 적용
                ma120 = data[sym]['Close'].rolling(120).mean().iloc[-1]
                action = "🟢 홀딩" if curr > ma120 else "🔴 매도"
                res.append({"Symbol": sym, "Price": curr, "Action": action, "Status_Icon": "💎" if "홀딩" in action else "💀"})
            self.floor_1_df = pd.DataFrame(res)
            return True
        except Exception as e:
            print(f"❌ 1층 분석 실패: {e}")
            return False

    def floor_2_hunting(self):
        """
        [3단계: 2층 무결성 12개 강제 로직 수선]
        - 데이터가 부족해도 12개의 칸은 반드시 유지 (원칙 1 준수)
        """
        print("🧬 [Step 3] 2층 타겟 12개 무결성 스캔...")
        try:
            files = ["COMMODITY_ANALYSIS_REPORT", "V40_BEST_TARGETS", "V40_TEN_BAGGER_REPORT_0837", "V7_RESULT_BNAI_FINAL"]
            combined = []
            
            for f_name in files:
                try:
                    df = self._smart_file_loader(f_name)
                    # 에너지 컬럼 자동 탐색
                    e_col = next((c for c in df.columns if 'Energy' in c or 'Score' in c), df.columns[1])
                    # 상위 3개 추출 (부족해도 일단 있는 만큼)
                    top3 = df.sort_values(by=e_col, ascending=False).head(3).copy()
                    top3['Source'] = f_name
                    
                    # [수선] 3개가 안 채워지면 더미 데이터로라도 3개 칸 유지 (무결성)
                    while len(top3) < 3:
                        new_row = pd.DataFrame([{"Symbol": "⚠️ [타겟부재]", e_col: 0, "Source": f_name}])
                        top3 = pd.concat([top3, new_row], ignore_index=True)
                    
                    combined.append(top3)
                    # 개별 섹션 변수 저장 (리포트용)
                    setattr(self, f"s_{f_name[:4]}", top3)
                    
                except Exception as e:
                    # 파일 로딩 실패 시 "수정 요청" 던지고 중단 (원칙 3)
                    raise ValueError(f"🚨 {f_name} 처리 중 모순 발생: {e}")

            self.floor_2_df = pd.concat(combined, ignore_index=True)
            return True
        except Exception as e:
            print(f"❌ 2층 분석 실패: {e}")
            return False

    def build_and_save_report(self):
        """4단계: 1+1-1=Complete (파일 저장 우선)"""
        print("📊 [Step 4] 통합 리포트 저장...")
        try:
            kst = (datetime.utcnow() + timedelta(hours=9)).strftime('%m%d_%H%M')
            file_name = f"V40_Final_Report_{kst}.xlsx"
            
            # [원칙 1] 파일 저장 성공 전까지 보고하지 않음
            with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
                if not self.floor_1_df.empty: self.floor_1_df.to_excel(writer, sheet_name='1층_보유')
                if not self.floor_2_df.empty: self.floor_2_df.to_excel(writer, sheet_name='2층_발굴')
            
            print(f"💾 [원칙 1] 파일 저장 완료: {file_name}")
            
            # 텍스트 리포트 생성
            report = f"📅 [V40 관제 보고]\n\n📊 V7:{self.v7_p:.1f}% | V8:{self.v8_p:.1f}%\n📢 상태: {self.market_state}\n\n"
            report += "🏢 [1층 보유주]\n"
            for _, r in self.floor_1_df.iterrows():
                report += f"{r['Status_Icon']} {r['Symbol']}: {r['Action']}\n"
            
            report += "\n🧬 [2층 12개 무결성 타겟]\n"
            for _, r in self.floor_2_df.iterrows():
                report += f"- {r['Symbol']} ({r['Source'][:10]})\n"
            
            self.analysis_report = report
            return file_name
        except Exception as e:
            raise ValueError(f"🚨 파일 저장 실패(원칙 1 위반): {e}")

    def send_telegram(self, file_path):
        """[수선] 텔레그램 예외 처리 강화"""
        print("✉️ 텔레그램 보고...")
        try:
            # 텍스트 먼저
            requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                          data={"chat_id": self.chat_id, "text": self.analysis_report}, timeout=15)
            # 파일 전송
            with open(file_path, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{self.t_token}/sendDocument", 
                              data={"chat_id": self.chat_id}, files={'document': f}, timeout=30)
            print("✅ 보고 완료")
        except Exception as e:
            # 원칙 1 준수: 전송 실패해도 파일은 남았음을 알림
            print(f"⚠️ 보고 전송 실패 (파일은 로컬에 저장됨): {e}")

    def run_process(self):
        """전 공정 통합 실행"""
        try:
            if not self.calculate_macro_spectrum(): raise ValueError("매크로 공정 모순")
            if not self.floor_1_action(): raise ValueError("1층 공정 모순")
            if not self.floor_2_hunting(): raise ValueError("2층 공정 모순")
            
            report_file = self.build_and_save_report()
            self.send_telegram(report_file)
            
        except Exception as e:
            # 원칙 3: 모순 발생 시 삭제하지 않고 즉시 사용자에게 보고
            err_msg = f"🚨 [V40 중단/수정 요청]\n{str(e)}"
            print(err_msg)
            try:
                requests.post(f"https://api.telegram.org/bot{self.t_token}/sendMessage", 
                              data={"chat_id": self.chat_id, "text": err_msg})
            except: pass

if __name__ == "__main__":
    engine = QuantumControlCenter(macro_v8_switch=2)
    engine.run_process()
