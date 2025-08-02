import re
import json
from datetime import datetime
from prompts.query_intent import *
from prompts.gen_response import *


def call_openai(client, prompt: dict, model="gpt-4o") -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": prompt['system_prompt']
            },
            {
                "role": "user",
                "content": prompt['user_prompt']
            }
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()

def extract_json_from_response(response_text: str) -> dict:
    """
    GPT 응답에서 ```json ... ``` 블록을 추출하고 딕셔너리로 변환
    """
    # ```json 블록만 추출
    match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # 혹시 그냥 JSON 문자열로 오는 경우
        json_str = response_text.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("JSON 디코딩 에러:", e)
        return {}

def gen_final_answer(client, query_structure, res_data_json):
    prompt = PROMPT_COMMON.copy()
    prompt['user_prompt'] = prompt['user_prompt'].format(
        query_text=query_structure['query_text'],
        structured_query=query_structure,
        dataframe_json=res_data_json,
        instructions=RESPONSE_INSTRUCTIONS[query_structure['intent']]
    )
    resp = call_openai(client, prompt)

    return resp