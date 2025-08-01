
import requests
import pandas as pd
from cfgs.cfgs import KAKAO_MAP_API_KEY, KAKAO_MAP_API

STANDARD_SIDO_MAPPING = {
    "서울": "서울특별시", "서울시": "서울특별시",
    "부산": "부산광역시", "부산시": "부산광역시",
    "대구": "대구광역시", "대구시": "대구광역시",
    "인천": "인천광역시", "인천시": "인천광역시",
    "광주": "광주광역시", "광주시": "광주광역시",
    "대전": "대전광역시", "대전시": "대전광역시",
    "울산": "울산광역시", "울산시": "울산광역시",
    "세종": "세종특별자치시", "세종시": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원도",
    "충북": "충청북도", "충남": "충청남도",
    "전북": "전라북도", "전남": "전라남도",
    "경북": "경상북도", "경남": "경상남도",
    "제주": "제주특별자치도", "제주도": "제주특별자치도"
}

GYEONGGI_CITY_NORMALIZATION = {
    "수원": "수원시",
    "성남": "성남시",
    "의정부": "의정부시",
    "안양": "안양시",
    "부천": "부천시",
    "광명": "광명시",
    "평택": "평택시",
    "동두천": "동두천시",
    "안산": "안산시",
    "고양": "고양시",
    "과천": "과천시",
    "구리": "구리시",
    "남양주": "남양주시",
    "오산": "오산시",
    "시흥": "시흥시",
    "군포": "군포시",
    "의왕": "의왕시",
    "하남": "하남시",
    "용인": "용인시",
    "파주": "파주시",
    "이천": "이천시",
    "김포": "김포시",
    "화성": "화성시",
    "광주": "광주시",
    "양주": "양주시",
    "포천": "포천시",
    "여주": "여주시",
    "송탄": "송탄시",
    "미금": "미금시",
    "안성": "안성시",
}

# ========================== 카카오맵 주소 불러오기 ===========================
def get_location_info(location_name: str):
    params = {'query': location_name}
    headers = {'Authorization': f"KakaoAK {KAKAO_MAP_API_KEY}"}

    resp = requests.get(KAKAO_MAP_API, params=params, headers=headers)

    return resp.json()

# ========================== 시군구 -> 법정동 코드 ===========================
def set_bjd_code_v1(query_structure, legal_dong_pdf):
    sido = query_structure.get('sido', '')
    sigu = query_structure.get('sigu', '')
    dong = query_structure.get('dong', '')

    # sido, sigu, dong 다 비어있고 주택 이름만 있으면 주소 채우기
    if not sido and not sigu and not dong:
        housing_name = query_structure.get('housing_name', '')

        if housing_name:
            res = get_location_info(housing_name)

            if res['documents']:
                add_name_lst = [document['address_name'] for document in res['documents']]
                # 일단은 1위 문서로
                add_name = add_name_lst[0]
                
                split_add_name = add_name.split(' ')
                if len(split_add_name) == 4:
                    sido = split_add_name[0]
                    sigu = split_add_name[1]
                    dong = split_add_name[2]
                elif len(split_add_name) == 5:
                    sido = split_add_name[0]
                    sigu = ' '.join(split_add_name[1:3])
                    dong = split_add_name[3]

                query_structure['sido'] = sido
                query_structure['sigu'] = sigu
                query_structure['dong'] = dong

    if sigu:
        sigu = sigu.replace(' ', '')

    bjd_code = -1
    if sigu and sido and dong:
        sigu_pdf = legal_dong_pdf[
            (legal_dong_pdf['sd_name'].str.contains(sido)) &
            (legal_dong_pdf['sgg_name'].str.contains(sigu)) &
            (legal_dong_pdf['dong_name'].str.contains(dong))
        ]
        bjd_code = sigu_pdf.iloc[0]['bjd_code']
    elif sigu and sido:
        sigu_pdf = legal_dong_pdf[
            (legal_dong_pdf['sd_name'].str.contains(sido)) &
            (legal_dong_pdf['sgg_name'].str.contains(sigu))
        ]
        bjd_code = sigu_pdf.iloc[0]['bjd_code']
    elif sido and dong:
        sigu_pdf = legal_dong_pdf[
            (legal_dong_pdf['sd_name'].str.contains(sido)) &
            (legal_dong_pdf['dong_name'].str.contains(dong))
        ]
        bjd_code = sigu_pdf.iloc[0]['bjd_code']
    elif sigu and dong:
        sigu_pdf = legal_dong_pdf[
            (legal_dong_pdf['sd_name'].str.contains(sido)) &
            (legal_dong_pdf['dong_name'].str.contains(dong))
        ]
        bjd_code = sigu_pdf.iloc[0]['bjd_code']
    elif dong:
        dong_pdf = legal_dong_pdf[legal_dong_pdf['dong_name'].str.contains(dong)]
        # 단순 bjd_code 가장 큰거 1개 뽑아오기
        bjd_code = (
            dong_pdf
            .sort_values(by='bjd_code', ascending=False)
            .iloc[0]['bjd_code']
        )
    elif sigu:
        sigu_pdf = legal_dong_pdf[
            (legal_dong_pdf['sgg_name'].str.contains(sigu)) &
            (legal_dong_pdf['dong_name'] == '')
        ]
        bjd_code = sigu_pdf.iloc[0]['bjd_code']
        
    elif sido:
        sido_pdf = legal_dong_pdf[
            (legal_dong_pdf['sd_name'].str.contains(sido)) &
            (legal_dong_pdf['sgg_name'] == '') &
            (legal_dong_pdf['dong_name'] == '')
        ]
    
        if not sido_pdf.empty:
            bjd_code = sido_pdf.iloc[0]['bjd_code']
        else: # 비어있으면 경기도인거니까 sgg로 다시 검사
            sigu_pdf = legal_dong_pdf[
                (legal_dong_pdf['sgg_name'].str.contains(sido)) &
                (legal_dong_pdf['dong_name'] == '')
            ]   
            bjd_code = sigu_pdf.iloc[0]['bjd_code']
    # 여기에 건물 이름만 있으면 주소 가져오는거 내용 추가
    # elif housing_name:
    else:
        bjd_code = -1

    query_structure['bjd_code'] = bjd_code
    return query_structure

# ======= 후보 주소 물어보기위한 리스트 추출
def get_candidate_bjd_name_lst(query_structure, legal_dong_pdf):
    sido = query_structure.get('sido')
    sigu = query_structure.get('sigu')
    dong = query_structure.get('dong')
    housing_name = query_structure.get('housing_name')

    sd_sgg_dong_lst = []
    if sido and not sigu and not dong:
        if '서울' in sido or '경기' in sido:
            dong_pdf = legal_dong_pdf[
            legal_dong_pdf['sd_name'].str.contains(sido)
            ].copy()
            dong_pdf['sd_sgg_dong_name'] = dong_pdf['sd_name'] + '-' + dong_pdf['sgg_name']
            sd_sgg_dong_lst = dong_pdf['sd_sgg_dong_name'].drop_duplicates().tolist()
    elif not sigu and dong:
        dong_pdf = legal_dong_pdf[
            legal_dong_pdf['dong_name'].str.contains(dong)
        ].copy()
        dong_pdf['sd_sgg_dong_name'] = dong_pdf['sd_name'] + '-' + dong_pdf['sgg_name'] + '-' + dong_pdf['dong_name']
        sd_sgg_dong_lst = dong_pdf['sd_sgg_dong_name'].drop_duplicates().tolist()
    elif sigu and dong:
        dong_pdf = legal_dong_pdf[
            (legal_dong_pdf['sgg_name'].str.contains(sigu)) &
            (legal_dong_pdf['dong_name'].str.contains(dong))
        ].copy()
        dong_pdf['sd_sgg_dong_name'] = dong_pdf['sd_name'] + '-' + dong_pdf['sgg_name'] + '-' + dong_pdf['dong_name']
        sd_sgg_dong_lst = dong_pdf['sd_sgg_dong_name'].drop_duplicates().tolist()
    elif sigu and not dong:
        dong_pdf = legal_dong_pdf[
            (legal_dong_pdf['sgg_name'].str.contains(sigu))
        ].copy()
        dong_pdf['sd_sgg_dong_name'] = dong_pdf['sd_name'] + '-' + dong_pdf['sgg_name']
        sd_sgg_dong_lst = dong_pdf['sd_sgg_dong_name'].drop_duplicates().tolist()
    elif not sigu and not dong and housing_name:
        sd_sgg_dong_lst = get_housing_location_name(housing_name)

    return sd_sgg_dong_lst

def get_housing_location_name(housing_name):
    resp = get_location_info(housing_name)

    sd_sgg_dong_lst = []
    for document in resp['documents']:
        split_addr = document['address_name'].split(' ')[:-1]
    
        if split_addr[-1].endswith('동'):
            if split_addr[0] == '서울':
                sd_sgg_dong_lst.append('-'.join(split_addr))
            elif split_addr[0] == '경기':
                if len(split_addr) == 4:
                    sgg = ''.join(split_addr[1:3])
                    sd_sgg_dong_lst.append(f"{split_addr[0]}-{sgg}-{split_addr[3]}")
                else:
                    sgg = split_addr[1]
                    sd_sgg_dong_lst.append(f"{split_addr[0]}-{sgg}-{split_addr[2]}")
                    
    return list(set(sd_sgg_dong_lst))

def set_bjd_name(query_structure, bjd_name):
    split_sgd = bjd_name.split('-')
    sd, sgg, dong = (split_sgd + [None]*3)[:3]
    
    query_structure['sido'] = sd
    query_structure['sigu'] = sgg
    query_structure['dong'] = dong

    return query_structure

def get_bjd_code_v2(query_structure, legal_dong_pdf):
    bjd_code_lst = legal_dong_pdf[
                        (legal_dong_pdf['sd_name'].str.contains(query_structure['sido'])) & 
                        (legal_dong_pdf['sgg_name'].str.contains(query_structure['sigu'])) & 
                        (legal_dong_pdf['dong_name'].str.contains(query_structure['dong']))
                    ]['bjd_code'].drop_duplicates().tolist()

    query_structure['bjd_code_lst'] = bjd_code_lst
    return query_structure

def get_bjd_code_v3(query_structure, legal_dong_pdf):
    sido = query_structure.get('sido')
    sigu = query_structure.get('sigu')
    dong = query_structure.get('dong')

    cond = (
        legal_dong_pdf['sd_name'].str.contains(sido) &
        legal_dong_pdf['sgg_name'].str.contains(sigu)
    )
    if dong:
        cond &= legal_dong_pdf['dong_name'].str.contains(dong)

    bjd_code_lst = legal_dong_pdf[cond]['bjd_code'].drop_duplicates().tolist()
    query_structure['bjd_code_lst'] = bjd_code_lst
    
    return query_structure