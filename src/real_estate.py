import json
import requests
import xmltodict
import numpy as np
import pandas as pd
from itertools import product
from datetime import datetime, timedelta

from cfgs.cfgs import *

def get_today_one_month_ago():
    today = datetime.now()
    one_month_ago = today - timedelta(days=30)

    return one_month_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

def prepare_month_range(query_structure):
    start_date = query_structure['start_date']
    end_date = query_structure['end_date']
    
    if not start_date and not end_date:
        start_date, end_date = get_today_one_month_ago()
        
        query_structure['start_date'] = start_date
        query_structure['end_date'] = end_date
    elif start_date and not end_date:
        _, end_date = get_today_one_month_ago()
        
        query_structure['end_date'] = end_date
    elif not start_date and end_date:
        #*** 여기는 에러 처리 (자세한 날짜 입력해달라고 하자 -> 방금 입력 받은 '날짜'는 제거)
        return []
        
    start_date = pd.to_datetime(start_date).replace(day=1)
    
    month_range = pd.date_range(start=start_date, end=end_date, freq='MS')
    month_range = [''.join(str(date).split(' ')[0].split('-')[:2]) for date in month_range]

    return month_range

def get_real_estate_info(lawd_cd, deal_ymd, trans_type='APT_TRADE', num_of_rows=999999):
    if trans_type == 'APT_TRADE':
        url = URL_APT_TRADE
        cols = DICT_APT_TRADE
    elif trans_type == 'APT_RENT':
        url = URL_APT_RENT
        cols = DICT_APT_RENT
    elif trans_type == 'OFFI_TRADE':
        url = URL_OFFI_TRADE
        cols = DICT_OFFI_TRADE
    elif trans_type == 'OFFI_RENT':
        url = URL_OFFI_RENT
        cols = DICT_OFFI_RENT
    else:
        return None, None
        
    params = {
        'LAWD_CD': int(str(lawd_cd)[:5]), # 앞 5자리
        'DEAL_YMD': deal_ymd, # yyyymm
        'numOfRows': num_of_rows,
        'serviceKey': DATA_GO_API_KEY,
    }
    
    resp = requests.get(url, params=params).text
    
    resp = xmltodict.parse(resp)

    
    numOfRows = int(resp['response']['body']['numOfRows'])
    pageNo = int(resp['response']['body']['pageNo'])
    totalCount = int(resp['response']['body']['totalCount'])

    if totalCount:
        pdf = pd.DataFrame(resp['response']['body']['items']['item'])
    
        rename_cols = DICT_COMMON.copy()
        rename_cols.update(cols)
    
        pdf = pdf.rename(columns=rename_cols)
    
        return pdf
    else:
        return pd.DataFrame()

def get_real_estate_pdf(query_structure):
    month_range = prepare_month_range(query_structure)
    target = query_structure['target']
    bjd_code_lst = query_structure['bjd_code_lst']
    
    real_estate_pdf_lst = []
    if month_range:
        month_bjd_comb = list(product(month_range, bjd_code_lst))
        for deal_ymd, bjd_code in month_bjd_comb:
            _real_estate_pdf = get_real_estate_info(bjd_code, deal_ymd, target)
        
            if not _real_estate_pdf.empty:
                real_estate_pdf_lst.append(_real_estate_pdf)
        
        if real_estate_pdf_lst:
            real_estate_pdf = pd.concat(real_estate_pdf_lst, ignore_index=True)

            date_cols = {'year': real_estate_pdf['계약년도'], 'month': real_estate_pdf['계약월'], 'day': real_estate_pdf['계약일']}
            real_estate_pdf['계약일자'] = pd.to_datetime(date_cols)
            real_estate_pdf['계약일자'] = real_estate_pdf['계약일자'].map(lambda x: x.strftime("%Y-%m-%d"))
        else:
            real_estate_pdf = pd.DataFrame()
    
        return real_estate_pdf
    else:
        return pd.DataFrame()


def postprocess_real_estate(total_real_estate_pdf, query_structure, debug=False):
    filtered_pdf = total_real_estate_pdf.copy()
    
    if 'TRADE' in query_structure['target']:
        cost_name = '거래금액'
    
        filtered_pdf = filtered_pdf.assign(
            거래금액=filtered_pdf[cost_name].str.replace(',', '', regex=False).astype(int),
            전용면적=filtered_pdf['전용면적'].astype(float).astype(int)
        )

        filtered_pdf = filtered_pdf[TRADE_USE_COLUMNS]
    elif 'RENT' in query_structure['target']:
        cost_name = '보증금액'
    
        filtered_pdf = filtered_pdf.assign(
            보증금액=filtered_pdf[cost_name].str.replace(',', '', regex=False).astype(int),
            월세금액=filtered_pdf['월세금액'].str.replace(',', '', regex=False).astype(int),
            전용면적=filtered_pdf['전용면적'].astype(float).astype(int)
        )

        if query_structure['deal_type'] == '월세':
            filtered_pdf = filtered_pdf[filtered_pdf['월세금액'] != 0]
        elif query_structure['deal_type'] == '전세':
            filtered_pdf = filtered_pdf[filtered_pdf['월세금액'] == 0]
        
        if query_structure.get('min_monthly_rent'):
            min_monthly_rent = int(query_structure['min_monthly_rent'] / 10000)
            filtered_pdf = filtered_pdf[filtered_pdf['월세금액'] >= min_monthly_rent]
        
        if query_structure.get('max_monthly_rent'):
            max_monthly_rent = int(query_structure['max_monthly_rent'] / 10000)
            filtered_pdf = filtered_pdf[filtered_pdf['월세금액'] <= max_monthly_rent]

        filtered_pdf = filtered_pdf[RENT_USE_COLUMNS]
    else:
        return filtered_pdf
        #*** return error
    
    ## 공통 필터링
    if query_structure.get('min_price'):
        min_price = int(query_structure['min_price'] / 10000)
        filtered_pdf = filtered_pdf[filtered_pdf[cost_name] >= min_price]
    
    if query_structure.get('max_price'):
        max_price = int(query_structure['max_price'] / 10000)
        filtered_pdf = filtered_pdf[filtered_pdf[cost_name] <= max_price]
        
    if query_structure.get('start_date'):
        filtered_pdf = filtered_pdf[filtered_pdf['계약일자'] >= query_structure['start_date']]
        
    if query_structure.get('end_date'):
        filtered_pdf = filtered_pdf[filtered_pdf['계약일자'] <= query_structure['end_date']]

    if query_structure.get('min_area') and query_structure.get('max_area'):
        if query_structure.get('min_area') == query_structure.get('max_area'):
            filtered_pdf = filtered_pdf[filtered_pdf['전용면적'] == query_structure['min_area']]
            
    if query_structure.get('min_area'):
        filtered_pdf = filtered_pdf[filtered_pdf['전용면적'] >= query_structure['min_area']]
    
    if query_structure.get('max_area'):
        filtered_pdf = filtered_pdf[filtered_pdf['전용면적'] <= query_structure['max_area']]
    
    if query_structure.get('housing_name'):
        # 일부만 일치해도 찾도록
        housing_name = query_structure['housing_name']
        housing_name = housing_name.replace('아파트', '').replace(' ', '')
        filtered_pdf = filtered_pdf[filtered_pdf['단지명'].str.contains(housing_name)]
    
    if query_structure.get('dong'):
        filtered_pdf = filtered_pdf[filtered_pdf['법정동'] == query_structure['dong']]

    return filtered_pdf


# 후처리 결과 검토 코드
def post_filtering_check(pdf):
    from IPython.display import display

    print(f"🔢 전체 행 개수: {len(pdf)}")

    # 계약일자 변환 (요약 min/max 계산 위해)
    pdf['계약일자'] = pd.to_datetime(pdf['계약일자'])

    if '거래금액' in pdf.columns:
        if pdf['거래금액'].dtype == 'object':
            pdf['거래금액'] = pdf['거래금액'].str.replace(',', '', regex=False).astype(int)

        pdf['전용면적'] = pdf['전용면적'].astype(float)

        summary_df = pdf.agg({
            '거래금액': ['min', 'max'],
            '전용면적': ['min', 'max'],
            '계약일자': ['min', 'max']
        }).transpose().rename(columns={'min': 'min', 'max': 'max'})

    elif '보증금액' in pdf.columns:
        if pdf['보증금액'].dtype == 'object':
            pdf['보증금액'] = pdf['보증금액'].str.replace(',', '', regex=False).astype(int)
        if pdf['월세금액'].dtype == 'object':
            pdf['월세금액'] = pdf['월세금액'].str.replace(',', '', regex=False).astype(int)

        pdf['전용면적'] = pdf['전용면적'].astype(float)

        summary_df = pdf.agg({
            '보증금액': ['min', 'max'],
            '월세금액': ['min', 'max'],
            '전용면적': ['min', 'max'],
            '계약일자': ['min', 'max']
        }).transpose().rename(columns={'min': 'min', 'max': 'max'})

    print("📌 법정동:")
    print(pdf['법정동'].unique())

    print("\n📌 단지명:")
    print(pdf['단지명'].unique())

    display(summary_df)

# post_filtering_check(total_real_estate_pdf.copy())
# print("="*50)
# post_filtering_check(filtered_pdf)

# # v1
# def prepare_data_for_llm(intent, df):
#     if intent in ['지역 시세 조회', '시계열 추이 조회']:
#         # 3번 방식: 통계 정보를 계산하여 전달
#         stats = {
#             "total_count": len(df),
#             "average_price": df['거래금액'].mean(),
#             "average_price": df['거래금액'].mean(),
#             "median_price": df['거래금액'].median(), # 중앙값 (이상치 영향 적음)
#             "max_price": df['거래금액'].max(),
#             "min_price": df['거래금액'].min(),
#             # 단위 면적(㎡)당 평균 가격
#             "avg_price_per_area": (df['거래금액'] / df['전용면적']).mean()
#         }

#         for key, value in stats.items():
#             if isinstance(value, (np.integer, np.int64)):
#                 stats[key] = int(value)
#             elif isinstance(value, (np.floating, np.float64)):
#                 stats[key] = float(value)
        
#         return json.dumps(stats, ensure_ascii=False, indent=4)
#     else: # 단일 매물 조회, 조건 기반 매물 탐색
#         df = df.sort_values(by='계약일자', ascending=False)
#         df = df.head(10)
#         # 1번 방식: 기본값으로 JSON 전달
#         return df.to_json(orient='records', force_ascii=False)

# --- [사전 준비] 헬퍼 함수들 ---

def add_pyeong_type_column(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame에 '평형대' 컬럼을 추가합니다."""
    if df.empty or '전용면적' not in df.columns:
        return df
    
    # 전용면적(㎡)을 평(Pyeong)으로 변환 후, 대표 평형으로 그룹화
    # 예: 25.7평 -> 25평형, 34.1평 -> 34평형
    # 여기서는 간단하게 반올림하여 정수로 만듭니다.
    df['대표평형'] = (df['전용면적'] / 3.30578).round().astype(int)
    df['평형대'] = df['대표평형'].astype(str) + "평형"
    return df

def calculate_summary_stats(df: pd.DataFrame) -> dict:
    """주어진 DataFrame의 주요 통계 지표를 계산합니다."""
    if df.empty:
        return {"total_count": 0, "average_price": 0, "median_price": 0, "max_price": 0, "min_price": 0}

    if '거래금액' in df.columns:
        stats = {
            "total_count": len(df),
            "average_price": int(df['거래금액'].mean()),
            "median_price": int(df['거래금액'].median()),
            "max_price": int(df['거래금액'].max()),
            "min_price": int(df['거래금액'].min())
        }
    elif '보증금액' in df.columns:
        stats = {
            "total_count": len(df),
            "average_price": int(df['보증금액'].mean()),
            "median_price": int(df['보증금액'].median()),
            "max_price": int(df['보증금액'].max()),
            "min_price": int(df['보증금액'].min()),

            "average_monthly_rent_price": int(df['월세금액'].mean()),
            "median_monthly_rent_price": int(df['월세금액'].median()),
            "max_monthly_rent_price": int(df['월세금액'].max()),
            "min_monthly_rent_price": int(df['월세금액'].min())
        }
    return stats


# --- [핵심] 수정된 메인 함수 ---

def prepare_data_for_llm_by_pyeong(intent: str, df: pd.DataFrame) -> str:
    """
    DataFrame을 평형대별로 그룹화하고, 인텐트에 따라 데이터를 처리하여 JSON으로 반환합니다.
    """
    # 1. 평형대 컬럼 추가
    df_with_pyeong = add_pyeong_type_column(df)
    
    # 최종 결과를 담을 딕셔너리
    result_data = {}
    
    # 2. 평형대별로 그룹화하여 순회
    for pyeong_type, group_df in df_with_pyeong.groupby('평형대'):
        
        # 3. 각 그룹(평형대)에 대해 인텐트별 로직 적용
        if intent in ['지역 시세 조회', '시계열 추이 조회']:
            # 통계 정보를 계산하여 저장
            stats = calculate_summary_stats(group_df)
            result_data[pyeong_type] = stats
            
        else:  # '단일 매물 조회', '조건 기반 매물 탐색'
            # 날짜 컬럼이 있다고 가정하고, 최신순으로 정렬 후 상위 10개 선택
            # '계약일자' 컬럼이 미리 생성되어 있어야 합니다.
            # df['계약일자'] = pd.to_datetime(...)
            
            # sorted_group = group_df.sort_values(by='계약일자', ascending=False).head(10)
            
            # (예시 코드에서는 '계약일자'가 없으므로 정렬 생략)
            sorted_group = group_df.head(MAX_REAL_ESTATE_PER_AREA)

            # JSON 직렬화를 위해 일부 컬럼만 선택하고 레코드로 변환
            if '거래금액' in df.columns:
                records = sorted_group[['단지명', '거래금액', '전용면적', '층', '대표평형']].to_dict(orient='records')
            elif '보증금액' in df.columns:
                records = sorted_group[['단지명', '보증금액', '월세금액', '전용면적', '층', '대표평형']].to_dict(orient='records')
            result_data[pyeong_type] = records
            
    # 4. 최종 딕셔너리를 JSON 문자열로 변환하여 반환
    return json.dumps(result_data, ensure_ascii=False, indent=4)