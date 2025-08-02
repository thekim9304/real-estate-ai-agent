from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import uuid

from src.ai_agent import process_query
from prompts.query_intent import PROMPT_QUERY_INTENT
from prompts.gen_response import PROMPT_CACHE_RESPONSE
from cfgs.cfgs import *
from src.openai_call import *

from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

class Query(BaseModel):
    text: str
    
class Message(BaseModel):
    role: str
    content: str
    
class Conversation(BaseModel):
    session_id: Optional[str] = None
    messages: List[Message]

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "백엔드 서버가 실행 중입니다."}


# 임시 캐시 메모리 (레디스로 교체 예정))
data_cache = {}

@app.post("/ask")
def ask_agent(conversation: Conversation):
    # 세션 ID 셋팅
    session_id = conversation.session_id
    ## 없으면 새로 생성
    if not session_id:
        session_id = str(uuid.uuid4())
        data_cache[session_id] = {}
    
    # 전체 대화 기록을 객체로 받음
    history = conversation.messages
    # 사용자의 마지막 질의
    last_user_query = history[-1].content
    
    print(data_cache)
    if len(history) > 1:
        conversation_history_str = ""
        for message in history:
            conversation_history_str += f'- {message.role}: "{message.content}"\n'  
        
        cache_key_str = ""
        for cache_key in list(data_cache[session_id].keys()):
            cache_key_str += f'- {cache_key}\n'
        
        prompt_query_nlu = PROMPT_QUERY_INTENT.copy()
        prompt_query_nlu['user_prompt'] = prompt_query_nlu['user_prompt'].format(
            history=conversation_history_str, 
            cached_data_name=cache_key_str,
            new_query=last_user_query
            )
        
        resp = call_openai(client, prompt_query_nlu)
        resp = extract_json_from_response(resp)
        print(resp)
        print()
        if resp['action'] == 'NEW_API_CALL':
            # 1. AI Agent 응답 불러오기 (단일)
            agent_answer, use_data_json, query_summary, cache_key = process_query(last_user_query)
        
            # 2. 조회된 데이터를 세션 ID와 함께 캐시에 저장
            if session_id not in data_cache:
                data_cache[session_id] = {cache_key: use_data_json}
            else:
                data_cache[session_id][cache_key] = use_data_json
        elif resp['action'] == 'ANSWER_FROM_CACHE':
            params =  resp['parameters']
            cache_keys = params['target_data_keys']
            cached_data_str = ""
            for cache_key in cache_keys:
                cached_data_str += f"- {cache_key} : {data_cache[session_id][cache_key]}\n"
            # anal_type = params['analysis_type'] # `analysis_type` (e.g., `comparison`, `filter`, `sort`, `summary`).
            
            conversation_history = ""
            window_size = 3
            for message in history[-(window_size*2):]:
                conversation_history += f'- {message.role}: "{message.content}"\n'
            
            
            prompt_cache_response = PROMPT_CACHE_RESPONSE.copy()
            prompt_cache_response['user_prompt'] = prompt_cache_response['user_prompt'].format(
                conversation_history=conversation_history,
                cached_data=cached_data_str
            )
            agent_answer = call_openai(client, prompt_cache_response)
            query_summary = f"{resp['parameters']['target_data_keys']} - {resp['parameters']['analysis_type']}"
        else:
            agent_answer = "질문을 이해할 수 없습니다."
            query_summary = "질문을 이해하지 못함"
        
        print(resp)
    else:
        # 1. AI Agent 응답 불러오기 (단일)
        agent_answer, use_data_json, query_summary, cache_key = process_query(last_user_query)
    
        # 2. 조회된 데이터를 세션 ID와 함께 캐시에 저장
        if session_id not in data_cache:
            data_cache[session_id] = {cache_key: use_data_json}
        else:
            data_cache[session_id][cache_key] = use_data_json
    
    # 3. 답변과 함께 세션 ID를 반환
    return {
        "role": "assistant", 
        "agent_answer": agent_answer, 
        "summary": query_summary,
        "session_id": session_id
    }