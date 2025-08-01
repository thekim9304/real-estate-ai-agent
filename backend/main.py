from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import uuid

# 요청 본문을 위한 Pydantic 모델
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


data_cache = {}

# --- API 엔드포인트 ---
@app.post("/ask")
# conversation 파라미터가 Conversation 모델을 사용합니다.
def ask_agent(conversation: Conversation):
    session_id = conversation.session_id
    
    # 1. 세션 ID가 없으면 새로 생성
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # 전체 대화 기록을 객체로 받음
    history = conversation.messages
    
    # 여기서 history를 활용하여 AI 로직을 처리합니다.
    print("프론트엔드에서 전달받은 전체 대화기록:")
    print(history)
    
    # 마지막 사용자 질문
    last_user_query = history[-1].content
    
    # (가짜 데이터 조회 로직)
    # 실제로는 여기서 API를 호출하여 데이터를 가져옵니다.
    retrieved_data = [
        {'아파트명': '광교중흥S클래스', '거래금액': 180000},
        {'아파트명': '힐스테이트 광교', '거래금액': 165000}
    ]
    # 2. 조회된 데이터를 세션 ID와 함께 캐시에 저장
    data_cache[session_id] = retrieved_data
    print(f"캐시 저장됨 (세션 ID: {session_id}):", data_cache[session_id])

    # 3. 캐시의 데이터를 사용해 답변 생성 (RAG)
    # final_prompt = create_final_prompt(conversation.messages, retrieved_data, ...)
    response_text = "네, 두 개의 아파트 정보를 찾았습니다. 광교중흥S클래스와 힐스테이트 광교입니다."

    # 4. 답변과 함께 세션 ID를 반환
    return {"role": "assistant", "content": response_text, "session_id": session_id}