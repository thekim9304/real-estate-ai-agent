from cfgs.cfgs import *
from src.openai_call import *

def make_query_summary(query_structure):
    start_date = query_structure['start_date']
    end_date = query_structure['end_date']
    sido = query_structure['sido']
    sigu = query_structure['sigu']
    dong = query_structure['dong']
    housing_name = query_structure['housing_name']
    intent = query_structure['intent']
    
    summary = f"{start_date}~{end_date} 기간 내 {sido} {sigu} {dong} {housing_name}의 {intent}를 제공했었습니다."
    
    return summary

def make_cache_key_name(query_structure):
    start_date = query_structure['start_date']
    end_date = query_structure['end_date']
    sido = query_structure['sido']
    sigu = query_structure['sigu']
    dong = query_structure['dong']
    housing_name = query_structure['housing_name']
    
    key_infos = [sido, sigu, dong, housing_name, start_date, end_date]
    
    valid_keys = [info for info in key_infos if info]
    
    return '_'.join(valid_keys)

def preprocess_query(query):
    query = query.replace('평데', '평대')
    return query

def get_today_year_month():
    today = datetime.today()
    return today.year, today.month, today.day
    
def gen_query_nlu_and_structure(client, query):
    query = preprocess_query(query)
    
    prompt = PROMPT_QUERY_STRUCTURE.copy()
    year, month, day = get_today_year_month()
    prompt['system_prompt'] = prompt['system_prompt'].format(year=year, month=month, day=day)
    prompt['user_prompt'] = prompt['user_prompt'].format(query=query)
    resp = call_openai(client, prompt)

    return resp