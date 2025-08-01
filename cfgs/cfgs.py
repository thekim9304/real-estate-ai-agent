import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATA_GO_API_KEY = os.getenv('DATA_GO_API_KEY')
KAKAO_MAP_API_KEY = os.getenv("KAKAO_DEVELOPERS_API_KEY")

KAKAO_MAP_API = "https://dapi.kakao.com/v2/local/search/keyword.json?page=1&size=1&sort=accuracy"

URL_APT_TRADE = 'http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade'
URL_APT_RENT = 'http://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent'
URL_OFFI_TRADE = 'http://apis.data.go.kr/1613000/RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade'
URL_OFFI_RENT = 'http://apis.data.go.kr/1613000/RTMSDataSvcOffiRent/getRTMSDataSvcOffiRent'

TRADE_USE_COLUMNS = ['단지명', '건축년도', '계약일자', '전용면적', '층', '법정동', '거래금액']
RENT_USE_COLUMNS = ['단지명', '건축년도', '계약기간', '계약구분', '계약일자', '전용면적', '층', '법정동', '보증금액', '월세금액']

MAX_REAL_ESTATE_PER_AREA = 10

DICT_COMMON = {
    'resultCode': '결과코드',
    'resultMsg': '결과메시지',
    'sggCd': '지역코드',
    'umdNm': '법정동',
    'jibun': '지번',
    'excluUseAr': '전용면적',
    'dealYear': '계약년도',
    'dealMonth': '계약월',
    'dealDay': '계약일',
    'floor': '층',
    'buildYear': '건축년도',
    'numOfRows': '한 페이지 결과 수',
    'pageNo': '페이지 번호',
    'totalCount': '전체 결과 수'
}

DICT_APT_TRADE = {
    'aptNm': '단지명',
    
    'dealAmount': '거래금액',
    'cdealType': '해제여부',
    'cdealDay': '해제사유발생일',
    'dealingGbn': '거래유형',
    'estateAgentSggNm': '중개사소재지',
    'rgstDate': '등기일자',
    'aptDong': '아파트 동명',
    'slerGbn': '매도자',
    'buyerGbn': '매수자',
    'landLeaseholdGbn': '토지임대부 아파트 여부'
}

DICT_APT_RENT = {
    'aptNm': '단지명',
    
    'deposit': '보증금액',
    'monthlyRent': '월세금액',
    'contractTerm': '계약기간',
    'contractType': '계약구분',
    'useRRRight': '갱신요구권사용',
    'preDeposit': '종전계약보증금',
    'preMonthlyRent': '종전계약월세'
}

DICT_OFFI_TRADE = {
    'offiNm': '단지명',
    'sggNm': '시군구',
    
    'dealAmount': '거래금액',
    'cdealType': '해제여부',
    'cdealDay': '해제사유발생일',
    'dealingGbn': '거래유형',
    'estateAgentSggNm': '중개사소재지',
    'slerGbn': '매도자',
    'buyerGbn': '매수자'
    
}

DICT_OFFI_RENT = {
    'offiNm': '단지명',
    'sggNm': '시군구',
    
    'deposit': '보증금액',
    'monthlyRent': '월세금액',
    'contractTerm': '계약기간',
    'contractType': '계약구분',
    'useRRRight': '갱신요구권사용',
    'preDeposit': '종전계약보증금',
    'preMonthlyRent': '종전계약월세'
}