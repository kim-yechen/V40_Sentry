def get_v40_report():
    global vacuum_msg, oracle_res
    
    # [기존 설정 유지]
    observatories = ['SPY', 'XLK', 'SMH', 'XLB', 'XLE', 'COPX', 'GDX', '^IRX', 'BIL']
    hunting_targets = ['SI=F', 'HG=F', 'ERO', 'FCX', 'SCCO', 'PSLV', 'CEF']
    core_sectors = ['FCX', 'SCCO', 'PSLV', 'PPL', 'DTE', 'ASTS', 'SI=F', 'COPX']

    # (중략: 엑셀 티커 로드 로직 동일)
    actual_prey = list(set([t for t in hunting_targets + excel_tickers if str(t) not in observatories]))
    all_symbols = list(set(actual_prey + observatories))

    kings = []
    downgrades = []
    market_data = {}
    all_v_energies = [] # 3단계 보강: 시장 전체 에너지 평균용

    # 2. 전수 조사 실행
    for symbol in all_symbols:
        try:
            time.sleep(0.5)
            df = yf.download(symbol, period="300d", interval="1d", progress=False, auto_adjust=True, threads=False)
            
            if df.empty or len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # --- [V40-C 보강 로직 시작] ---
            # 10일 연속 수성 체크를 위해 최근 10일치 에너지 계산
            close = df['Close']
            energies_10d = []
            for i in range(10):
                # i일 전 데이터 슬라이싱
                sub_df = df.iloc[:len(df)-i] if i > 0 else df
                c_rsi = float(calculate_rsi(sub_df['Close']).iloc[-1])
                c_mfi = float(calculate_mfi(sub_df).iloc[-1])
                energies_10d.append((c_mfi * 0.6) + (c_rsi * 0.4))
            
            curr_v_energy = energies_10d[0]
            all_v_energies.append(curr_v_energy) # 시장 평균용 수집
            
            # 가속도(V_Accel) 계산: 오늘 vs 5일 전
            v_accel = (curr_v_energy - energies_10d[5]) / (energies_10d[5] + 1e-10) * 100
            
            # 10일 중 8일 이상 에너지 80 수성 여부
            succession_count = sum(1 for e in energies_10d if e >= 80)
            # --- [V40-C 보강 로직 끝] ---

            ma_series = close.rolling(200).mean()
            ma200 = ma_series.iloc[-1]
            ma200_slope = ma200 - ma_series.iloc[-5]
            curr_price = float(close.iloc[-1]); prev_price = float(close.iloc[-2])

            market_data[symbol] = {'df': df, 'price': curr_price, 'energy': curr_v_energy, 'accel': v_accel}

            if symbol in actual_prey:
                # 1단계 수정: 단순히 오늘 80이 아니라 "10일 중 8일 수성" 필터 적용
                if (curr_price > ma200) and (succession_count >= 8):
                    # 2단계 수정: 가속도와 에너지를 대조하여 Phase 태그 달기
                    phase = "💎 [요새]" if v_accel > 0 else "🚨 [식음]"
                    kings.append({'symbol': symbol, 'energy': curr_v_energy, 'accel': v_accel, 'phase': phase, 'core': symbol in core_sectors})
                
                elif (curr_price < ma200) and (prev_price >= ma_series.iloc[-2]):
                    downgrades.append(symbol)
                    
        except Exception as e: continue

    # 3단계 수정: 시장 전체 에너지 평균으로 과열 판단
    market_avg_energy = sum(all_v_energies) / len(all_v_energies) if all_v_energies else 0
    overheat_tag = "🚨 [시장 과열: 사냥 금지]" if market_avg_energy > 65 else "✅ [정상 유동성]"

    # (이면 분석 및 오라클 연산 로직 동일)

    # 5. 리포트 조립 (수정 지침 반영)
    kings = sorted(kings, key=lambda x: x['energy'], reverse=True)
    
    true_kings_report = ""
    for k in kings[:5]: # 상위 5개 노출
        mark = "🚀" if k['core'] else "🔥"
        true_kings_report += f"{mark} {k['symbol']}: {k['phase']} 에너지 {k['energy']:.1f} (가속 {k['accel']:+.1f}%)\n"

    report_1 = (
        f"🛡 *[V40-C: 진성 요새 기상도]*\n📅 {datetime.now().strftime('%m/%d %H:%M')}\n\n"
        f"🌀 *[시장 평균 에너지]*: {market_avg_energy:.1f}\n"
        f"⚠️ *[과열 판정]*: {overheat_tag}\n\n"
        f"👑 *[진성 승격 (10일 수성)]*\n{true_kings_report if true_kings_report else '수성 성공 종목 없음'}\n"
        f"💀 *[강등]*: {', '.join(downgrades[:5])}"
    )

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": report_1, "parse_mode": "Markdown"})
