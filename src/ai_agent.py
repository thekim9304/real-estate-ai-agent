from cfgs.cfgs import *
from prompts.query_intent import *
from prompts.gen_response import *
from src.openai_call import *
from src.location import *
from src.real_estate import *
from src.query import *

import pandas as pd
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

legal_dong_pdf = pd.read_csv("/home/jovyan/project/data/data_go_kr/legal_dong_clean.csv")
legal_dong_pdf = legal_dong_pdf.fillna('')
legal_dong_pdf = legal_dong_pdf[legal_dong_pdf['dong_name'].str.endswith('동')]
legal_dong_pdf = legal_dong_pdf[legal_dong_pdf['sd_name'].isin(['서울특별시', '경기도'])]
legal_dong_pdf['bjd_code'] = legal_dong_pdf['bjd_code'].map(lambda x: int(str(x)[:5]))

def process_query(query: str):
    # 1-1) query -> structure with LLM
    resp = gen_query_nlu_and_structure(client, query)
    query_structure = extract_json_from_response(resp)
    
    answer = ''
    if query_structure.get('intent') == '해당 없음':
        return "죄송합니다, 해당 질문은 제가 답변하기 어려운 유형입니다. 부동산(아파트 혹은 오피스텔) 거래 정보에 대해 질문해주세요.", None, None, None
    try:
        # 1-2) Fill bjd name
        ## 1-2-1) Show Candidate bjd name list
        sd_sgg_dong_lst = get_candidate_bjd_name_lst(query_structure, legal_dong_pdf) 
    
        if not sd_sgg_dong_lst:
            return "죄송합니다, 정확한 지역(or건물)명을 입력해주세요. 현재 저희 서비스는 수도권(서울, 경기) 지역의 정보만 제공하고 있습니다.", None, None, None

        ###### (실제로는 여기서 사용자에게 후보를 보여주고 선택받는 로직 필요)
        bjd_name = sd_sgg_dong_lst[0] # 테스트를 위해 첫 번째 후보 자동 선택
        query_structure = set_bjd_name(query_structure, bjd_name)
        query_structure = get_bjd_code_v3(query_structure, legal_dong_pdf)

        # 데이터 호출 및 후처리
        total_real_estate_pdf = get_real_estate_pdf(query_structure)
        filtered_pdf = postprocess_real_estate(total_real_estate_pdf, query_structure)
        
        # 데이터가 없는 경우 처리
        if filtered_pdf.empty:
            return "요청하신 조건에 맞는 거래 내역을 찾지 못했습니다.", None, None, None

        # 답변 생성
        res_data_json = prepare_data_for_llm_by_pyeong(query_structure['intent'], filtered_pdf)
        final_answer = gen_final_answer(client, query_structure, res_data_json)
        
        return final_answer, res_data_json, make_query_summary(query_structure), make_cache_key_name(query_structure)

    except Exception as e:
        # 파이프라인 중간에 알 수 없는 오류 발생 시 처리
        print(f"오류 발생: {e}")
        return "요청을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", None, None, None

    