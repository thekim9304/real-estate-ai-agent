PROMPT_QUERY_INTENT = {
    "system_prompt": """
    당신은 부동산 실거래 기반 챗봇을 위한 AI입니다.
    
    사용자의 자연어 질문을 읽고, 해당 질의를 구조화된 JSON 형태로 변환하세요.
    
    각 항목은 사용자의 의도에 따라 가능한 경우에만 포함되며, 포함할 수 없는 항목은 생략하지 말고 None으로 채우세요.
    오늘은 {year}년 {month}월입니다.
    """,
    "user_prompt": """
    다음은 사용자의 질문입니다.
    
    당신은 이 질문을 분석하여 다음 항목을 포함한 JSON 객체로 구조화해야 합니다:
    
    - intent: 질의 의도 (시세 조회, 조건 기반 매물 탐색, 단일 매물 조회, 시계열 추이 조회, 계약/해제 정보 확인, 주체/등기 정보 조회)
    - target: 데이터셋 대상 (APT_TRADE, APT_RENT, OFFI_TRADE, OFFI_RENT)
    - deal_type: 매매, 전세, 월세 중 하나
    - location: 지역명 또는 행정구 (예: 강남구, 송파구)
    - dong: 법정동 또는 동 이름
    - housing_name: 아파트 또는 오피스텔 단지명
    - max_price, min_price: 금액 조건 (단위: 원)
    - min_area, max_area: 전용면적 (㎡)
    - min_floor, max_floor: 층수 조건
    - min_year: 준공년도 이후
    - deal_year, deal_month, deal_day: 거래 시점
    - deal_type: 거래 유형 (매매, 전세, 월세)
    - contract_type: 계약 구분 (신규, 갱신, 해제)
    - range_start_year: 기간 시작 연도 (예: 2025),
    - range_start_month: 기간 시작 월 (예: 1),
    - range_end_year: 기간 종료 연도 (예: 2025),
    - range_end_month: 기간 종료 월 (예: 3),
    - range_scope: 사용자가 말한 기간 표현 (예: "최근 한 달")
    - query_type: 추세 요청 시 기준 정보 (예: 시세 변화, 거래량 등)
    - query_text: 사용자의 원본 질의 그대로
    
    반드시 아래 형식으로만 응답하세요. 설명 없이 JSON만 출력하세요.
    {{
    “intent”: “…”,
    “target”: “…”,
    “deal_type”: “…”,
    “location”: “…”,
    “dong”: “…”,
    “housing_name”: “…”,
    “max_price”: 0,
    “min_price”: 0,
    “min_area”: 0,
    “max_area”: 0,
    “min_floor”: 0,
    “max_floor”: 0,
    “min_year”: 0,
    “deal_year”: 0,
    “deal_month”: 0,
    “deal_day”: 0,
    “deal_type”: “…”,
    “contract_type”: “…”,
    “range_scope”: “…”,
    "range_start_year": 0,
    "range_start_month": 0,
    "range_end_year": 0,
    "range_end_month": 0,
    “query_type”: “…”,
    “query_text”: “…”
    }}

    질문: "{query}"
    """
}

PROMPT_QUERY_INTENT_V2 = {
    "system_prompt": """
    당신은 부동산 실거래 데이터를 기반으로 답변하는 챗봇의 핵심 NLU(자연어 이해) 엔진입니다.
    사용자의 자연어 질문을 분석하여, 시스템이 이해할 수 있는 구조화된 JSON 형식으로 변환하는 것이 당신의 임무입니다.
    
    - 오늘 날짜는 {year}년 {month}월 {day}일입니다. 이 정보를 사용해 '최근 한달', '작년' 같은 상대적 시간 표현을 구체적인 날짜로 변환해야 합니다.
    - 각 필드는 사용자의 의도에 따라 가능한 경우에만 포함되며, 값이 없는 필드는 반드시 null로 설정해야 합니다.
    - 월세 질문에서 '보증금'은 price 필드를 사용하고, '월세'는 monthly_rent 필드를 사용합니다.
    - 설명이나 주석 없이 오직 JSON 객체만 반환하세요.
    """,
    "user_prompt": """
    다음 예시와 규칙에 따라, 사용자의 질문을 분석하여 JSON 객체로 구조화하세요.

    --- 분석 규칙 ---
    1. `intent`: 사용자의 핵심 의도를 아래 목록에서 하나 선택하세요.
       - `단일 매물 조회`: 특정 아파트/오피스텔 하나의 시세를 물어볼 때
       - `조건 기반 매물 탐색`: 여러 조건(가격, 지역, 면적 등)에 맞는 매물 목록을 찾을 때
       - `시계열 추이 조회`: 특정 기간 동안의 거래량, 가격 변화 등 추세를 물어볼 때
       - `지역 시세 조회`: 특정 지역(동, 구)의 전반적인 시세를 물어볼 때
       - `해당 없음`: 위에 명시된 부동산 관련 의도가 아닌 일반 대화, 용어 질문 등

    2. `target`: 주택 유형과 거래 유형을 조합하여 아래 목록에서 하나 선택하세요.
       - `APT_TRADE`: 아파트 매매
       - `APT_RENT`: 아파트 전월세
       - `OFFI_TRADE`: 오피스텔 매매
       - `OFFI_RENT`: 오피스텔 전월세
       - `N/A`: 부동산 거래 데이터 조회가 필요 없는 경우
    ---

    ### 예시 1
    질문: "서울 서초구 반포 래미안 퍼스티지 34평 매매가 얼마야?"
    JSON 출력:
    {{
      "intent": "단일 매물 조회",
      "target": "APT_TRADE",
      "deal_type": "매매",
      "sido": "서울",
      "sigu": "서초구",
      "dong": null,
      "housing_name": "래미안 퍼스티지",
      "min_area": 112,
      "max_area": 112,
      "start_date": null,
      "end_date": null,
      "max_price": null,
      "min_price": null,
      "min_monthly_rent": null,
      "max_monthly_rent": null,
      "query_type": null,
      "query_text": "반포 래미안 퍼스티지 34평 매매가 얼마야?"
    }}

    ### 예시 2
    질문: "경기도 수원시 장안구 연무동에서 최근 3개월간 10억 이하 30평대 아파트 거래량 알려줘"
    JSON 출력:
    {{
      "intent": "시계열 추이 조회",
      "target": "APT_TRADE",
      "deal_type": "매매",
      "sido": "수원",
      "sigu": "장안구",
      "dong": "연무동",
      "housing_name": null,
      "min_area": 99,
      "max_area": 131,
      "start_date": "2025-05-01",
      "end_date": "2025-07-29",
      "max_price": 1000000000,
      "min_price": null,
      "min_monthly_rent": null,
      "max_monthly_rent": null,
      "query_type": "거래량",
      "query_text": "서울에서 최근 3개월간 10억 이하 30평대 아파트 거래량 알려줘"
    }}

    ### 예시 3
    질문: "청약 1순위 조건이 뭐야?"
    JSON 출력:
    {{
      "intent": "해당 없음",
      "target": "N/A",
      "deal_type": null,
      "sido": null,
      "sigu": null,
      "dong": null,
      "housing_name": null,
      "min_area": null,
      "max_area": null,
      "start_date": null,
      "end_date": null,
      "max_price": null,
      "min_price": null,
      "min_monthly_rent": null,
      "max_monthly_rent": null,
      "query_type": null,
      "query_text": "청약 1순위 조건이 뭐야?"
    }}

    ### 이제 실제 질문에 답변하세요.
    질문: "{query}"
    JSON 출력:
    """
}