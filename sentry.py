import os, yfinance as yf, pandas as pd, requests, numpy as np
from datetime import datetime

# --- [환경 변수: 형님의 금고] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID: 
        print(text) # 토큰 없으면 화면에 출력
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def check_squeeze(df, window=20):
    """[신념 1: 병목 추적] 가격 변동성은 줄고 에너지는 응축되는가?"""
    try:
        # 1. 볼린저 밴드 폭(BB Width)으로 변동성 압착 측정
        std = df['Close'].rolling(window=window).std()
        mean = df['Close'].rolling(window=window).mean()
        bb_width = (std * 4) / mean
        
        # 최근 5일간의 변동성이 이전 20일 평균보다 낮은지 확인 (압착 구간)
        is_squeezing = bb_width.iloc[-1] < bb_width.rolling(window=window).mean().iloc[-1]
        return is_squeezing
    except: return False

def calculate_real_alpha(df, market_df):
    """[신념 2: 진성 알파] 거래대금 가중치를 고려한 시장 대비 초과 수익률"""
    try:
        stock_ret = df['Close'].tail(5).pct_change().sum()
        market_ret = market_df.tail(5).pct_change().sum()
        # 거래량이 실린 상승인지 확인 (보조지표)
        vol_confirm = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]
        return (stock_ret - market_ret), vol_confirm
    except: return 0.0, False

def get_v40_quantum_sentry():
    # 1. V2 리포트 자동 동기화 (업그레이드된 기준점 로드)
    file_name = 'V40_NEW_HUMAN_V2_UPGRADE.xlsx'
    if not os.path.exists(file_name):
        print(f"❌ 형님, {file_name} 파일이 없습니다. 경로를 확인하십시오.")
        return

    try:
        v2_data = pd.read_excel(file_name)
        # 엑셀에서 형님이 정해둔 등급과 MDD 제한을 가져옴
        target_info = v2_data.set_index('Symbol')[['V2_Group', 'V2_MDD_Limit', 'V2_Priority_Score']].to_dict('index')
        hunting_targets = list(target_info.keys())
    except Exception as e:
        print(f"❌ 엑셀 로드 실패: {e}")
        return

    # 2. 시장 기준점 확보
    market_df = yf.download("SPY", period="30d", progress=False, auto_adjust=True)['Close']

    squeezing_gold, exploding_spear, danger_zone = [], [], []

    for symbol in hunting_targets:
        try:
            df = yf.download(symbol, period="250d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 50: continue
            
            curr_price = float(df['Close'].iloc[-1])
            peak_250 = df['Close'].max()
            mdd = ((curr_price - peak_250) / peak_250) * 100
            
            # 형님이 정하신 종목별 MDD Limit (A그룹 -35%, B그룹 -15% 등)
            limit_mdd = target_info[symbol]['V2_MDD_Limit']
            v2_group = target_info[symbol]['V2_Group']
            
            # 알파 및 병목(Squeeze) 확인
            alpha, vol_ok = calculate_real_alpha(df, market_df)
            is_squeezed = check_squeeze(df)
            
            res = {'Symbol': symbol, 'MDD': mdd, 'Alpha': alpha, 'Group': v2_group}

            # 3. [신념 기반 분류]
            # MDD 한도 내에 있고, 병목(압착) 중인 진성 텐배거 후보
            if mdd >= limit_mdd:
                if is_squeezed:
                    squeezing_gold.append(res)
                elif alpha > 0 and vol_ok:
                    exploding_spear.append(res)
            else:
                # 형님이 정한 맷집 한도를 넘어선 놈
                danger_zone.append(res)
                
        except: continue

    # 4. 형님 전용 언어로 무전 발송
    header = f"🛡️ **[V40-Sentry v3.0 보고]**\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"
    status_msg = f"📊 V2 타겟 감시: {len(hunting_targets)}개 동기화 완료\n"
    report_body = ""

    if squeezing_gold:
        report_body += f"\n💎 **[진성 텐배거: 압착구간]**\n(매집 적기 - 힘이 고이고 있습니다)"
        for t in squeezing_gold[:3]:
            report_body += f"\n📍 {t['Symbol']} (MDD:{t['MDD']:.1f}% / {t['Group']})"

    if exploding_spear:
        report_body += f"\n\n🚀 **[신인류: 발발구간]**\n(추격 타격 - 에너지가 뿜어져 나옵니다)"
        for t in exploding_spear[:3]:
            report_body += f"\n🔥 {t['Symbol']} (Alpha:+{t['Alpha']:.2%})"

    if danger_zone:
        report_body += f"\n\n💀 **[경고: 맷집 초과]**\n소각 검토: {', '.join([d['Symbol'] for d in danger_zone[:5]])}"

    if not squeezing_gold and not exploding_spear:
        report_body = "\n✅ **현재 압착/발발 종목 없음**\n형님, 잉여 현금을 보존하며 매복하십시오."

    send_telegram(header + status_msg + report_body)

if __name__ == "__main__":
    get_v40_quantum_sentry()
