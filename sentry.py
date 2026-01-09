# (상단 import 및 calculate_rsi 부분은 동일)

def get_v40_test_report():
    # 테스트를 위해 형님의 핵심 종목 4개 + 지수 1개 강제 할당
    targets = ['ERO', 'FCX', 'SCCO', 'SLV', 'SPY'] 
    
    alerts = "⚠️ *[테스트: 신분 변동 체크]*\n"
    hits = "\n🏟️ *[테스트: 모든 신인류 강제 노출]*\n"
    tracking = "\n🔍 *[추적 및 관망]*\n"
    
    for symbol in targets:
        try:
            df = yf.download(symbol, period="250d", interval="1d", progress=False)
            c_today = df['Close'].iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rsi = calculate_rsi(df['Close']).iloc[-1]

            # 테스트를 위해 조건을 확 풀어버립니다 (RSI 90 이하 모두 출력)
            if c_today > ma200:
                hits += f"- {symbol}: RSI {rsi:.1f} (작동 확인용) ✅\n"
            else:
                tracking += f"- {symbol}: RSI {rsi:.1f} (200일선 아래)\n"
        except Exception as e:
            hits += f"- {symbol}: 에러 발생({e})\n"

    final_msg = "🧪 *[시스템 정상 작동 테스트]*\n" + alerts + hits + tracking
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    get_v40_test_report()
