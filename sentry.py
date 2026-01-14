import os
import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0); down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / (ema_down + 1e-10)
    return 100 - (100 / (1 + rs))

def calculate_mfi(df, period=14):
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    rmf = tp * df['Volume']
    up_mf = pd.Series(0.0, index=df.index); dn_mf = pd.Series(0.0, index=df.index)
    up_mf[tp > tp.shift(1)] = rmf[tp > tp.shift(1)]
    dn_mf[tp < tp.shift(1)] = rmf[tp < tp.shift(1)]
    m_r = up_mf.rolling(window=period).sum() / (dn_mf.rolling(window=period).sum() + 1e-10)
    return 100 - (100 / (1 + m_r))

def get_v40_report():
    # SPY를 기준으로 상대 강도(RS)를 계산하기 위해 리스트에 추가
    sectors = ['XLK', 'XLE', 'XLB', 'COPX', 'GDX', 'SMH', 'SPY']
    essentials = ['SI=F', 'HG=F', '^IRX', 'SLV', 'BIL', 'ERO', 'FCX', 'SCCO']
    targets = list(set(sectors + essentials))

    market_data = {}
    rs_scores = {}

    # 1. 전 종목 데이터 수집 및 기본 지표 계산
    for symbol in targets:
        try:
            time.sleep(0.7)
            df = yf.download(symbol, period="300d", interval="1d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            close = df['Close']
            market_data[symbol] = {
                'df': df,
                'price': float(close.iloc[-1]),
                'rsi': calculate_rsi(close).iloc[-1],
                'mfi': calculate_mfi(df).iloc[-1],
                'change': (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]
            }
        except: continue

    # 2. [이면 분석] RS Matrix (상대 강도) 계산
    if 'SPY' in market_data:
        spy_close = market_data['SPY']['df']['Close']
        for sec in ['XLK', 'XLE', 'XLB', 'COPX', 'GDX', 'SMH']:
            if sec in market_data:
                sec_close = market_data[sec]['df']['Close']
                # 시장 대비 상대 강도 비율 (Sector / SPY)
                rs_ratio = sec_close / spy_close
                # RS 기울기 (최근 5일간의 변화율)
                rs_slope = (rs_ratio.iloc[-1] - rs_ratio.iloc[-5]) / rs_ratio.iloc[-5] * 100
                rs_scores[sec] = rs_slope

    # 3. [유동성 진공 지수] 기술주(SMH/XLK) vs 실물(COPX/GDX/XLB)
    vacuum_msg = ""
    if rs_scores:
        tech_rs = (rs_scores.get('XLK', 0) + rs_scores.get('SMH', 0)) / 2
        real_rs = (rs_scores.get('XLB', 0) + rs_scores.get('COPX', 0) + rs_scores.get('GDX', 0)) / 3
        
        vacuum_msg = "\n🌀 *[유동성 진공/전이 지수]*\n"
        if tech_rs < 0 and real_rs > 0:
            vacuum_msg += f"└ 🚀 **[전이 포착]:** 기술주(-{abs(tech_rs):.1f}%) → 실물(+{real_rs:.1f}%)로 돈이 탈출 중!\n"
        elif tech_rs > 0 and real_rs < 0:
            vacuum_msg += f"└ ⚠️ **[블랙홀]:** 실물이 죽고 기술주(+{tech_rs:.1f}%)가 유동성을 흡수 중입니다.\n"
        else:
            vacuum_msg += f"└ 🚦 **[혼조]:** 돈의 방향성이 아직 모호합니다. (Tech: {tech_rs:.1f}% / Real: {real_rs:.1f}%)\n"

    # --- 오라클 섹션 구성 ---
    oracle_section = "\n🔮 *[V40 오라클: 3중 스위치 분석]*\n"
    
    # 은/금리 로직 (형님의 보정값 유지)
    silver = market_data.get('SI=F') or market_data.get('SLV')
    if silver and 'SI=F' not in market_data:
        silver['rsi'] *= 1.02
        silver['source'] = "ETF(SLV)*1.02"
    elif silver:
        silver['source'] = "선물(SI=F)"

    rate_change = market_data.get('^IRX', {}).get('change')
    if rate_change is None and 'BIL' in market_data:
        rate_change = market_data['BIL']['change'] * -1

    if silver and rate_change is not None:
        if silver['rsi'] > 60 and silver['mfi'] > 60:
            status = "⚡ *붕괴:* [악성 인플레이션]" if rate_change > 0 else "🌀 *유동성 중첩:* [실물 강세]"
            oracle_section += f"{status}\n└ 근거: {silver['source']} 기반\n"
        else:
            oracle_section += "✅ 특이 붕괴 없음 (인과율 안정적)\n"

    # 최종 보고서 조립
    final_msg = f"🛡 *[V40 전략 리포트]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n"
    final_msg += vacuum_msg + oracle_section
    
    # 텔레그램 발송
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_report()
