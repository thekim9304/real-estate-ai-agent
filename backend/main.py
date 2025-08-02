from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import uuid

from src.helpers import *


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

# --- 임시 캐시 메모리 (레디스로 교체 예정)) ---
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
    
    if len(history) <= 1:
        agent_answer, query_summary = handle_new_query(last_user_query, session_id, data_cache)
    else:
        nlu_result = get_nlu_result(history, session_id, data_cache)
        print(json.dumps(nlu_result, indent=4, ensure_ascii=False))
        
        if nlu_result['action'] == 'NEW_API_CALL':
            agent_answer, query_summary = handle_new_query(last_user_query, session_id, data_cache)
        elif nlu_result['action'] == 'ANSWER_FROM_CACHE':
            agent_answer, query_summary = answer_from_cache(nlu_result.get('parameters', {}), history, session_id, data_cache)
        else:
            agent_answer = "죄송합니다, 질문의 의도를 명확히 이해하지 못했습니다. 다시 질문해주세요."
            query_summary = "질문 의도 파악 실패"
        
    
    # 3. 답변과 함께 세션 ID를 반환
    return {
        "role": "assistant", 
        "agent_answer": agent_answer, 
        "summary": query_summary,
        "session_id": session_id
    }