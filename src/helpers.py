
from pydantic import BaseModel
from typing import List, Optional
from prompts.query_intent import PROMPT_QUERY_INTENT
from prompts.gen_response import PROMPT_CACHE_RESPONSE

import json
from openai import OpenAI

from cfgs.cfgs import OPENAI_API_KEY
from src.openai_call import call_openai, extract_json_from_response
from src.ai_agent import process_query

client = OpenAI(api_key=OPENAI_API_KEY)


class Message(BaseModel):
    role: str
    content: str

#--- Helper Functions ---
def get_nlu_result(history: List[Message], session_id: str, data_cache: dict):
    """NLU 모델을 호출하여 사용자의 의도를 파악합니다."""
    history_str = ""
    for message in history:
        history_str += f'- {message.role}: "{message.content}"\n'  
    
    cache_keys_str = "\n".join([f"- {key}" for key in data_cache.get(session_id, {}).keys()])
    
    prompt = PROMPT_QUERY_INTENT.copy()
    prompt['user_prompt'] = prompt['user_prompt'].format(
        history=history_str, 
        cached_data_name=cache_keys_str,
        new_query=history[-1].content
    )
    
    resp_str = call_openai(client, prompt)
    return extract_json_from_response(resp_str)

def handle_new_query(query: str, session_id:str, data_cache: dict):
    """새로운 API 호출이 필요할 때의 로직을 처리합니다."""
    agent_answer, use_data_csv, query_summary, cache_key = process_query(query)
    
    # 캐시에 데이터 저장
    data_cache.setdefault(session_id, {})[cache_key] = use_data_csv
    
    return agent_answer, query_summary

def answer_from_cache(params: dict, history: List[Message], session_id: str, data_cache: dict):
    """캐시 데이터를 사용하여 답변을 생성합니다."""
    cache_keys = params.get('target_data_keys', [])
    
    print("캐쉬 키 : ", cache_keys)
    
    cached_data_str = ""
    for key in cache_keys:
        # get()을 사용하여 키가 없을 때의 오류 방지
        data = data_cache.get(session_id, {}).get(key)
        if data:
            cached_data_str += f"- {key}: {data}\n"

    # 슬라이딩 윈도우로 최근 대화만 포함
    conversation_history_str = ""
    window_size = 4 # 최근 4개 메시지 (2턴)
    for message in history[-window_size:]:
        conversation_history_str += f'- {message.role}: "{message.content}"\n'
    
    # 캐시 기반 답변 생성 프롬프트 구성
    prompt = PROMPT_CACHE_RESPONSE.copy()
    prompt['user_prompt'] = prompt['user_prompt'].format(
        conversation_history=conversation_history_str,
        cached_data=cached_data_str,
        new_query=history[-1].content
    )
    
    agent_answer = call_openai(client, prompt)
    query_summary = f"캐시 데이터 {params.get('target_data_keys')}를 사용하여 '{params.get('analysis_type')}' 분석을 수행함."
    
    return agent_answer, query_summary