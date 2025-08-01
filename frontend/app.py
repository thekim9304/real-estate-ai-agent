import streamlit as st
import requests

# --- 페이지 설정 ---
st.set_page_config(page_title="부동산 QA AI 에이전트", page_icon="🤖")
st.title("🤖 부동산 QA AI 에이전트")

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
    # 'role'에 따라 사용자 또는 어시스턴트의 채팅 버블을 사용합니다.
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
                # FastAPI 백엔드 API에 전체 대화 기록을 보낼 수 있도록 수정
                # (지금은 간단히 마지막 질문만 보냅니다)
                response = requests.post(
                    "http://backend:8000/ask", 
                    json={"text": prompt}
                )
                response.raise_for_status()
                
                ai_response_content = response.json().get("answer")
                st.markdown(ai_response_content)
                
                # 3. AI의 답변도 대화 기록에 추가합니다.
                st.session_state.messages.append({"role": "assistant", "content": ai_response_content})

            except requests.exceptions.RequestException as e:
                st.error(f"오류가 발생했습니다: {e}")
                
# 사이드바에 디버깅용 섹션 추가
with st.sidebar:
    st.header("디버깅 영역")
    # '세션 상태 확인'이라는 제목의 접고 펼 수 있는 섹션 생성
    with st.expander("st.session_state.messages 내용 보기"):
        # st.json을 사용하면 리스트와 딕셔너리를 깔끔하게 보여줌
        st.json(st.session_state.messages)