import streamlit as st
import requests

# --- 페이지 설정 ---
st.set_page_config(page_title="부동산 QA AI 에이전트", page_icon="🤖")
st.title("🤖 부동산 QA AI 에이전트")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None # 세션 ID 초기화

# --- 세션 상태 관리 ---
# st.session_state에 'messages'가 없으면, 초기 메시지를 설정합니다.
# 이 'messages' 리스트가 대화의 전체 기록을 저장하는 '기억' 역할을 합니다.
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 부동산에 대해 무엇이든 물어보세요."}
    ]

# --- 대화 기록 표시 ---
# '기억'에 저장된 모든 메시지를 순서대로 화면에 그립니다.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 사용자 입력 처리 ---
# st.chat_input은 화면 하단에 고정된 입력창을 생성합니다.
if prompt := st.chat_input("질문을 입력해주세요..."):
    # 1. 사용자의 메시지를 대화 기록에 추가하고 화면에 표시합니다.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. AI의 답변을 생성하고 표시합니다.
    with st.chat_message("assistant"):
        with st.spinner("답변을 생각하고 있어요..."):
            try:
                response = requests.post(
                    "http://backend:8000/ask", 
                    json={
                        "session_id": st.session_state.session_id,
                        "messages": st.session_state.messages
                    }
                )
                ai_response = response.json()
                
                # 백엔드로부터 받은 세션 ID 업데이트
                st.session_state.session_id = ai_response.get("session_id")
                
                # 1. 사용자 화면에는 'agent_answer' (에이전트 답변)를 보여줍니다.
                st.markdown(ai_response.get("agent_answer"))
                
                # 2. 다음 대화를 위해 st.session_state.messages 에는 'summary' (요약본)를 저장합니다.
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ai_response.get("agent_answer"),
                    "summary": ai_response.get("summary")
                })
                
            except requests.exceptions.RequestException as e:
                st.error(f"오류가 발생했습니다: {e}")
                
# 사이드바에 디버깅용 섹션 추가
with st.sidebar:
    st.header("디버깅 영역")
    # '세션 상태 확인'이라는 제목의 접고 펼 수 있는 섹션 생성
    with st.expander("st.session_state.messages 내용 보기"):
        # st.json을 사용하면 리스트와 딕셔너리를 깔끔하게 보여줌
        st.json(st.session_state)