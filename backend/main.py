from fastapi import FastAPI
from pydantic import BaseModel

# 요청 본문을 위한 Pydantic 모델
class Query(BaseModel):
    text: str

app = FastAPI()

# AI 질의응답 API
@app.post("/ask")
def ask_agent(query: Query):
    import time
    time.sleep(10)
    
    response_text = f"'{query.text}'에 대한 AI 답변입니다."
    return {"answer": response_text}