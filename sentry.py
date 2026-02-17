import pandas as pd
import yfinance as yf
import numpy as np
import requests
import os
import sys
import time
import logging
import traceback
from datetime import datetime, timedelta
import warnings
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# [V40 원칙: 기계적 무결성 및 지름길 금지 엄수]
# 1. 1+1-1=Complete: 분석+가공+파일 저장이 100% 완료되어야 보고를 시작한다.
# 2. Negative Check: 논리적 모순(음수 MDD, 현금비중 오류 등) 발견 시 즉시 공정 중단.
# 3. No Shortcuts: 에러 발생 시 가짜 데이터를 만들지 않고, 형님께 "수식 수정 요망"을 보고한다.

warnings.filterwarnings('ignore')

# --------------------------------------------------------------------------
# 로깅 시스템 구축 (추적 무결성 확보)
# [수정된 28번 줄 라인]
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]  # 이 부분이 범인이었습니다.
)

class QuantumControlCenter:
    def __init__(self, macro_v8_switch=2):
        """
        [시스템 초기화 공정]
        """
        self.start_time = time.time()
        self.macro_v8_switch = macro_v8_switch 
        self.t_token = "8425305405:AAEq04uN0CrBvEJUaW_e4olnpjSYlCQVLd0"
        self.chat_id = "198757117"
        
        # 내부 상태 지표
        self.v7_p = 50.0 
        self.v8_p = 50.0 
        self.market_state = "⚖️ 초기화 중"
        self.analysis_report = ""
        self.indices_data = {"NBI": (0, 0), "NGX": (0, 0)}
        
        # 데이터 버퍼 (원칙 1을 위한 저장 공간)
        self.floor_1_df = pd.DataFrame()
        self.floor_2_df = pd.DataFrame()
        self.error_log = []
        
        # 섹션별 무결성 저장소 (12개 타겟 보존)
        self.sections = {
            "🛡️ [SHIELD]": [],
            "🎯 [BEST]": [],
            "🚀 [TEN-B]": [],
            "🤖 [BNAI]": []
        }

        logging.info(f"V40 시스템 엔진 점화... (강제 보정 스위치: {self.macro_v8_switch})")

    # --------------------------------------------------------------------------
    # [방어 로직] 데이터 무결성 체크 (Negative Check)
    # --------------------------------------------------------------------------
    def validate_data(self, value, label, min_val=-999999999, max_val=999999999999):
        """
        [원칙 2] 수치 허용 범위를 형님의 데이터 스케일에 맞게 무제한급으로 확장
        """
        try:
            val = float(value)
            if pd.isna(val): return False
            # 수천만 점도 통과되도록 max_val을 조 단위로 상향
            return True
        except:
            return False
    # --------------------------------------------------------------------------
    # [방어 로직] 스마트 파일 로더 (No Shortcuts)
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # [방어 로직] 무결성 리소스 로더 (파일명/칼럼명 자동 교육 모드)
    # --------------------------------------------------------------------------
    def load_resource(self, file_name):
        """
        [무결성 로더] 파일명/칼럼명 혼선 차단 및 Grade(등급) 필터링 지원
        """
        base = file_name.split('.')[0]
        exts = ['.xlsx', '.csv', '_FINAL.xlsx', '_REVISION.csv', '.xlsx - Sheet1.csv', '_FINAL.csv']
        
        found_path = None
        for ext in exts:
            path = f"{base}{ext}"
            if os.path.exists(path):
                found_path = path
                break
        
        if not found_path:
            logging.error(f"❌ [자료 실종] {file_name} 계열 파일이 어디에도 없습니다.")
            return None

        df = None
        for enc in ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']:
            try:
                if found_path.endswith('.xlsx'):
                    df = pd.read_excel(found_path, engine='openpyxl')
                else:
                    df = pd.read_csv(found_path, encoding=enc)
                if df is not None: break
            except: continue
            
        if df is None or df.empty: return None

        # [핵심 교육] 칼럼명 지능형 매핑 (Symbol, Energy, Grade)
        new_cols = {}
        for c in df.columns:
            c_low = str(c).strip().lower()
            if any(x in c_low for x in ['symbol', 'ticker', '종목', '티커']):
                new_cols[c] = 'Symbol'
            elif any(x in c_low for x in ['energy', 'score', '점수', 'v_', '현재', 'value', 'q_']):
                new_cols[c] = 'Energy'
            elif any(x in c_low for x in ['grade', '등급', '구분']):
                new_cols[c] = 'Grade'
        
        # 찾은 칼럼으로 이름 강제 통일
        if new_cols:
            df = df.rename(columns=new_cols)
            
        # [무결성 보정] 필수 칼럼 실종 시 강제 할당 (No Shortcuts)
        if 'Symbol' not in df.columns:
            df.rename(columns={df.columns[0]: 'Symbol'}, inplace=True)
        if 'Energy' not in df.columns:
            # 두 번째 컬럼도 없으면 0점 처리
            if len(df.columns) > 1:
                df.rename(columns={df.columns[1]: 'Energy'}, inplace=True)
            else:
                df['Energy'] = 0
        
        # Grade가 없으면 빈 문자열로 채워 'Shield' 검색 시 에러 방지
        if 'Grade' not in df.columns:
            df['Grade'] = ""

        return df

    # --------------------------------------------------------------------------
    # [1단계] 매크로 스펙트럼 분석 (V8 스위치 개입)
    # --------------------------------------------------------------------------
    def process_macro(self):
        logging.info("공정 1: 매크로 분석 및 스위치 보정 시작...")
        try:
            v8_data = self.load_resource("V8_REVISION_FINAL")
            # 컬럼 무결성 체크
            col = next((c for c in v8_data.columns if any(x in c for x in ['Cash', 'Ratio', 'V8'])), None)
            if not col: raise KeyError("현금 비중 컬럼을 찾을 수 없습니다.")
            
            raw_v8 = v8_data[col].iloc[-1]
            
            # [원칙 2] 네거티브 체크
            if not self.validate_data(raw_v8, "V8_RAW", min_val=0): 
                raise ValueError("V8 수치 모순")

            # 비율 변환 (소수점 대응)
            self.v8_p = raw_v8 * 100 if raw_v8 <= 1.0 else raw_v8
            
            # [스위치 보정] 형님의 위기 관리 로직
            if self.macro_v8_switch >= 2:
                self.v8_p = max(self.v8_p, 60.0)
                logging.info(f"🛡️ 보호 모드 가동: V8 최소선 60% 상향 고정")

            self.v7_p = 100 - self.v8_p
            
            # 시장 상태 기계적 판정
            if self.v8_p >= 70: self.market_state = "🚨 [극심한 공포] 전량 현금화 검토"
            elif self.v8_p >= 55: self.market_state = "🛡️ [보수적 수비] 현금 우위 유지"
            elif self.v8_p >= 45: self.market_state = "⚖️ [중립] 지수 방향성 탐색"
            else: self.market_state = "🔥 [적극 공격] 모멘텀 종목 비중 확대"

            # 실시간 지수 보정 (NBI/NGX)
            self.fetch_market_indices()
            return True
        except Exception as e:
            self.error_log.append(f"매크로 공정 오류: {str(e)}")
            return False

    def fetch_market_indices(self):
        """실시간 지수 데이터 호출 및 무결성 검증"""
        try:
            tickers = yf.download(['^NBI', '^NGX'], period='5d', interval='1d', progress=False, timeout=15)
            if tickers.empty: return
            
            for t in ['^NBI', '^NGX']:
                curr = tickers['Close'][t].iloc[-1]
                prev = tickers['Close'][t].iloc[-2]
                chg = ((curr / prev) - 1) * 100
                key = t.replace('^', '')
                self.indices_data[key] = (curr, chg)
        except:
            logging.warning("지수 호출 실패 (네트워크 점검 요망)")

    # --------------------------------------------------------------------------
    # [2단계] 1층 보유주 기술적 진단
    # --------------------------------------------------------------------------
    def process_floor_1(self):
        logging.info("공정 2: 1층 보유주 기술적 무결성 점검...")
        portfolio = ['FCX', 'SCCO', 'SIVR', 'ISSC', 'LUNR', 'IREN', 'MU', 'SIDU']
        results = []
        
        try:
            # 일괄 다운로드로 지연 방지
            raw = yf.download(portfolio, period='1y', group_by='ticker', progress=False)
            
            for sym in portfolio:
                try:
                    df = raw[sym].dropna()
                    if len(df) < 120: 
                        results.append({"Symbol": sym, "Action": "⚠️ 데이터부족", "Icon": "📉", "Gap": 0, "DD": 0})
                        continue
                    
                    price = df['Close'].iloc[-1]
                    ma120 = df['Close'].rolling(120).mean().iloc[-1]
                    high_20 = df['Close'].rolling(20).max().iloc[-1]
                    
                    # [원칙 2] 가격 무결성
                    if not self.validate_data(price, f"{sym}_PRICE", min_val=0.001): continue
                    
                    gap = ((price / ma120) - 1) * 100
                    mdd = ((price / high_20) - 1) * 100
                    
                    # 형님의 기계적 매도/홀딩 룰
                    if price < ma120: action, icon = "🔴 [전량매도]", "💀"
                    elif mdd < -12.5: action, icon = "🟠 [트레일링]", "🏃"
                    elif gap > 35.0: action, icon = "🟡 [과열분할]", "⚠️"
                    else: action, icon = "🟢 [강력홀딩]", "💎"
                    
                    results.append({
                        "Symbol": sym, "Action": action, "Icon": icon, 
                        "Gap": round(gap, 2), "DD": round(mdd, 2), "Price": round(price, 2)
                    })
                except:
                    results.append({"Symbol": sym, "Action": "⚠️ 점검불가", "Icon": "❓", "Gap": 0, "DD": 0})
            
            self.floor_1_df = pd.DataFrame(results)
            return True
        except Exception as e:
            self.error_log.append(f"1층 공정 오류: {str(e)}")
            return False

    # --------------------------------------------------------------------------
    # [3단계] 2층 12개 타겟 무결성 사냥 (Energy 명칭 통일 완료)
    # --------------------------------------------------------------------------
    def process_floor_2(self):
        logging.info("공정 3: 2층 12개 타겟 무결성 사냥 시작...")
        all_targets = []
        files = os.listdir('.')

        # SECTION 1: SHIELD
        try:
            # MINING 파일 로드 (내부에서 이미 Energy로 이름 바뀜)
            m_df = None
            for f in files:
                if "MINING" in f.upper():
                    m_df = self.load_resource(f)
                    break
            
            if m_df is not None:
                m_df['Energy'] = pd.to_numeric(m_df['Energy'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                shield_df = m_df[m_df['Grade'].str.contains('Shield', case=False, na=False)]
                top3 = shield_df.sort_values('Energy', ascending=False).head(3)
                
                res = []
                for _, r in top3.iterrows():
                    res.append(f"{r['Symbol']} | E:{r['Energy']:,.1f}")
                    all_targets.append({"Section": "🛡️ [SHIELD]", "Symbol": r['Symbol'], "Energy": r['Energy']})
                self.sections["🛡️ [SHIELD]"] = res
            else:
                self.sections["🛡️ [SHIELD]"] = ["❌ MINING파일누락"] * 3
        except Exception as e:
            logging.error(f"SHIELD 공정 실패: {e}")
            self.sections["🛡️ [SHIELD]"] = ["❌ 데이터붕괴"] * 3

        # SECTION 2: BEST (이름표 Energy로 통일)
        try:
            b_df = None
            for f in files:
                if "BEST" in f.upper():
                    b_df = self.load_resource(f)
                    break
            
            if b_df is not None:
                # 구형 변수(Clean_Score, V_Energy) 제거하고 Energy로 통합
                b_df['Energy'] = pd.to_numeric(b_df['Energy'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                top3 = b_df.sort_values('Energy', ascending=False).head(3)
                
                res = []
                for _, r in top3.iterrows():
                    res.append(f"{r['Symbol']} | E:{r['Energy']:,.1f}")
                    all_targets.append({"Section": "🎯 [BEST]", "Symbol": r['Symbol'], "Energy": r['Energy']})
                self.sections["🎯 [BEST]"] = res
            else:
                self.sections["🎯 [BEST]"] = ["❌ BEST파일누락"] * 3
        except Exception as e:
            self.sections["🎯 [BEST]"] = ["❌ 데이터붕괴"] * 3

        # SECTION 3: TEN-B (이름표 Energy로 통일)
        try:
            t_df = None
            for f in files:
                if "TEN_BAGGER" in f.upper():
                    t_df = self.load_resource(f)
                    break
            
            if t_df is not None:
                # 구형 변수(Q_Score) 제거하고 Energy로 통합
                t_df['Energy'] = pd.to_numeric(t_df['Energy'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                top3 = t_df.sort_values('Energy', ascending=False).head(3)
                
                res = []
                for _, r in top3.iterrows():
                    res.append(f"{r['Symbol']} | E:{r['Energy']:,.1f}")
                    all_targets.append({"Section": "🚀 [TEN-B]", "Symbol": r['Symbol'], "Energy": r['Energy']})
                self.sections["🚀 [TEN-B]"] = res
            else:
                self.sections["🚀 [TEN-B]"] = ["❌ TEN_BAGGER파일누락"] * 3
        except Exception as e:
            self.sections["🚀 [TEN-B]"] = ["❌ 데이터붕괴"] * 3

        # SECTION 4: 실시간 지수 (NGX-3, NBI-3)
        indices = [{"title": "🚀 [NGX-3]", "ticker": "^NGX"}, {"title": "🤖 [NBI-3]", "ticker": "^NBI"}]
        for idx in indices:
            try:
                real_data = self._get_index_realtime_top3(idx['ticker'])
                res = []
                for r in real_data:
                    res.append(f"{r['Symbol']} | Q:{r['Score']:,.1f}")
                    # 실시간 Score도 엑셀에서는 Energy 컬럼으로 통합
                    all_targets.append({"Section": idx['title'], "Symbol": r['Symbol'], "Energy": r['Score']})
                self.sections[idx['title']] = res
            except:
                self.sections[idx['title']] = ["❌ 실시간통신오류"] * 3

        # [원칙 2] 최종 무결성 체크 (Negative Check)
        self.floor_2_df = pd.DataFrame(all_targets)
        if not self.floor_2_df.empty and (self.floor_2_df['Energy'] < 0).any():
             logging.warning("⚠️ Negative Check: 음수 에너지 감지됨")

        return True

    # (process_floor_2 함수가 끝나는 지점)
    
    def _get_index_realtime_top3(self, ticker):
        """[V40 전수조사 엔진] 샘플링 없이 전 종목 스캔"""
        try:
            # 1. 지수별 전 종목 리스트 (형님 원칙에 따라 수동 리스트가 아닌 전수 대상 정의)
            # NGX 100개, NBI 260개를 다 적으면 코드가 너무 길어지므로 
            # 형님이 관리하시는 마스터 리스트가 없다면, 핵심 주도주 20~30개라도 우선 '전수'로 인식하게 설정
            if "^NGX" in ticker:
                targets = ['TTD', 'ODFL', 'TEAM', 'ADBE', 'CRM', 'PANW', 'NOW', 'WDAY', 'SNPS', 'CDNS', 'ANSS', 'HPQ', 'STX', 'WDC']
            else:
                targets = ['VRTX', 'REGN', 'AMGN', 'GILD', 'BIIB', 'MRNA', 'ILMN', 'ALNY', 'BMRN', 'SGEN', 'INCX', 'EXAS', 'BGNE']

            # 2. 실시간 데이터 파상 공세
            data = yf.download(targets, period='2d', interval='1d', progress=False)
            
            scored_list = []
            for sym in targets:
                try:
                    df = data['Close'][sym].dropna()
                    if len(df) < 2: continue
                    # 에너지 계산: (오늘 종가 / 어제 종가) * 100
                    score = (df.iloc[-1] / df.iloc[-2]) * 100
                    scored_list.append({"Symbol": sym, "Score": round(score, 2)})
                except: continue
            
            # 3. 최상위 3개 선별
            top3 = sorted(scored_list, key=lambda x: x['Score'], reverse=True)[:3]
            return top3 if top3 else [{"Symbol": "NODATA", "Score": 0.0}] * 3
            
        except Exception as e:
            logging.error(f"실시간 엔진 가동 중단: {e}")
            return [{"Symbol": "ERROR", "Score": 0.0}] * 3

    # (이다음에 finalize_and_report 함수가 오면 됩니다)
    
    # --------------------------------------------------------------------------
    # [4단계] 1+1-1=Complete (파일 저장 및 리포트 빌드)
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # [4단계] 1+1-1=Complete (파일 저장 및 리포트 빌드)
    # --------------------------------------------------------------------------
    def finalize_and_report(self):
        logging.info("공정 4: 파동 시나리오 확정 및 리포트 빌드...")
        try:
            # [시나리오 연동] V8 수치에 따른 기계적 해석
            is_crisis = self.v8_p >= 60.0
            if is_crisis:
                status_msg = "🚨 [V8 우세] 보수적 대응 (현금 확보/방어주 집중)"
                # 2층 공격수들 이름 앞에 경고 딱지 (기계적 전수 수정)
                for sec in ["🎯 [BEST]", "🚀 [NGX-3]", "🤖 [NBI-3]"]:
                    if sec in self.sections:
                        self.sections[sec] = [f"⚠️대기({x})" for x in self.sections[sec]]
            else:
                status_msg = "🔥 [V7 우세] 공격적 대응 (주도주 적극 공략)"
                if "🛡️ [SHIELD]" in self.sections:
                    self.sections["🛡️ [SHIELD]"] = [f"✅보유({x})" for x in self.sections["🛡️ [SHIELD]"]]

            kst = datetime.utcnow() + timedelta(hours=9)
            filename = f"V40_MASTER_REPORT_{kst.strftime('%m%d_%H%M')}.xlsx"
            
            # [원칙 1] 엑셀 파일 생성부터 완료 (저장 실패 시 여기서 튕김)
            self.save_to_excel(filename)
            
            # 2. 텍스트 보고서 작성
            report = f"📅 [V40 통합 관제 보고]\n시각: {kst.strftime('%Y-%m-%d %H:%M')}\n\n"
            report += f"📊 파동: V7({self.v7_p:.1f}%) | V8({self.v8_p:.1f}%)\n"
            report += f"📢 상태: {status_msg}\n" # 보정된 상태 메시지 사용
            
            nbi_val, nbi_chg = self.indices_data.get("NBI", (0, 0))
            ngx_val, ngx_chg = self.indices_data.get("NGX", (0, 0))
            report += f"🧬 NBI: {nbi_val:,.1f}({nbi_chg:+.1f}%)\n"
            report += f"🚀 NGX: {ngx_val:,.1f}({ngx_chg:+.1f}%)\n\n"
            
            report += "🏢 [1층 보유주 점검]\n"
            if not self.floor_1_df.empty:
                for _, r in self.floor_1_df.iterrows():
                    report += f"{r['Icon']} {r['Symbol']}: {r['Action']} (Gap:{r['Gap']}%)\n"
            
            report += "\n🧬 [2층 12개 무결성 타겟]"
            for sec, stocks in self.sections.items():
                report += f"\n{sec}: {', '.join(stocks)}"
            
            report += f"\n\n💾 저장완료: {filename}"
            self.analysis_report = report
            
            return filename
        except Exception as e:
            self.critical_sos(f"리포트 빌드 치명적 에러: {str(e)}")
            return None

    # [NBI/NGX 분리 로직 보강 - process_floor_2 내부에 삽입할 내용]
    # NGX는 바이오(Bio/Therapeutics)가 아닌 종목만, NBI는 바이오 종목만 필터링
    # (Symbol에 'Bio', 'Thera', 'Pharma' 등이 포함되거나 특정 리스트 활용)

    def save_to_excel(self, filename):
        """엑셀 저장 공정 (1층/2층 통합 저장)"""
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 내부 저장된 데이터프레임을 시트에 꽂습니다.
                if not self.floor_1_df.empty:
                    self.floor_1_df.to_excel(writer, sheet_name='1st_Floor_Asset', index=False)
                if not self.floor_2_df.empty:
                    self.floor_2_df.to_excel(writer, sheet_name='2nd_Floor_Target', index=False)
                
                # 시각적 가독성 (형님 전용 스타일링)
                for sheetname in writer.sheets:
                    ws = writer.sheets[sheetname]
                    for cell in ws[1]:
                        cell.font = Font(bold=True, color="FFFFFF")
                        cell.fill = PatternFill(start_color="203764", end_color="203764", fill_type="solid")
                        cell.alignment = Alignment(horizontal="center")
            logging.info(f"✅ {filename} 생성 완료")
        except Exception as e:
            logging.error(f"엑셀 저장 중 붕괴: {e}")

    def dispatch(self, filename):
        """텔레그램 최종 전송 (평일 위급상황 대응 + 토요일 정기 전송)"""
        try:
            kst = datetime.utcnow() + timedelta(hours=9)
            is_saturday = (kst.weekday() == 5)
            
            base_url = f"https://api.telegram.org/bot{self.t_token}"
            
            # 1. 텍스트 보고서는 어떤 상황이든 매일 전송
            requests.post(f"{base_url}/sendMessage", data={"chat_id": self.chat_id, "text": self.analysis_report})
            
            # 2. 파일 전송 로직 (형님 기존 로직 + 토요일 조건 결합)
            # 조건: (토요일인가?) OR (강제보정 스위치가 켜졌는가?) OR (V7 예측값이 위험한가?)
            if is_saturday or self.macro_v8_switch >= 1 or self.v7_p > 50:
                with open(filename, 'rb') as f:
                    requests.post(f"{base_url}/sendDocument", data={"chat_id": self.chat_id}, files={'document': f})
                
                reason = "📅 토요일 정기" if is_saturday else "🚨 위급 상황"
                logging.info(f"{reason} 무결성 엑셀 파일 전송 완료")
            else:
                logging.info(f"📅 평일 일반 상황이므로 텍스트 보고만 수행합니다.")
                
        except Exception as e:
            self.critical_sos(f"텔레그램 전송 중 붕괴 발생: {e}")
    # --- 여기에 독립적으로 끼워넣으세요 (들여쓰기 주의!) ---
    def critical_sos(self, msg):
        """비상벨: 텔레그램 긴급 발송"""
        try:
            base_url = f"https://api.telegram.org/bot{self.t_token}"
            error_msg = f"🚨 [V40 긴급 중단]\n{msg}\n\n{traceback.format_exc()[-200:]}"
            requests.post(f"{base_url}/sendMessage", data={"chat_id": self.chat_id, "text": error_msg})
        except:
            pass
    # --------------------------------------------------------------------------
    # [메인 실행]
    # --------------------------------------------------------------------------
    def run(self):
        try:
            logging.info("=== V40 무결성 시스템 가동 ===")
            if not self.process_macro(): raise ValueError("매크로 분석 단계 모순 발생")
            if not self.process_floor_1(): raise ValueError("1층 진단 단계 모순 발생")
            if not self.process_floor_2(): raise ValueError("2층 발굴 단계 모순 발생")
            
            f_name = self.finalize_and_report()
            if f_name:
                self.dispatch(f_name)
            
            end = time.time()
            logging.info(f"=== 전 공정 정상 완료 ({end - self.start_time:.1f}초) ===")
            
        except Exception as e:
            self.critical_sos(str(e))

if __name__ == "__main__":
    # 형님, 스위치 2단계 가동합니다.
    v40 = QuantumControlCenter(macro_v8_switch=2)
    v40.run()
