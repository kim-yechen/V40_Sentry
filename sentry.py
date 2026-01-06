import os
import requests

# [네거티브 체크] 서랍에서 열쇠를 꺼낼 때, 없으면 '없음'이라고 확실히 표시
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', 'MISSING')
CHAT_ID = os.environ.get('CHAT_ID', 'MISSING')

def check_keys():
    if TELEGRAM_TOKEN == 'MISSING' or CHAT_ID == 'MISSING':
        print(f"🚨 [치명적 에러] 금고에서 열쇠를 못 가져왔습니다!")
        print(f"현황 -> 토큰: {'✅' if TELEGRAM_TOKEN != 'MISSING' else '❌ 없음'}")
        print(f"현황 -> ID: {'✅' if CHAT_ID != 'MISSING' else '❌ 없음'}")
        exit(1) # 여기서 멈춰야 형님이 18번 줄을 다시 안 보십니다.

if __name__ == "__main__":
    check_keys()
    # 이 아래로 기존 분석 코드들이 이어짐...
