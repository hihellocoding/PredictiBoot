
import streamlit as st
import requests
import pandas as pd

# FastAPI 서버의 기본 URL
API_BASE_URL = "http://127.0.0.1:8000"

# 세션 상태 초기화
if 'search_results' not in st.session_state:
    st.session_state.search_results = None

st.title("📈 주가 예측 PredictiBoot")

st.markdown("---")

# --- 1. 종목 검색 기능 ---
st.header("1. 종목 코드 검색")
search_query = st.text_input("검색할 회사 이름을 입력하세요 (예: 삼성, 카카오)")

if st.button("검색하기"):
    if search_query:
        try:
            response = requests.get(f"{API_BASE_URL}/stocks/domestic/search", params={"query": search_query})
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data['results'])
            df.rename(columns={'code': '종목코드', 'name': '종목명'}, inplace=True)
            st.session_state.search_results = df  # 검색 결과를 세션에 저장
        except requests.exceptions.RequestException as e:
            st.session_state.search_results = None
            if e.response and e.response.status_code == 404:
                st.error(f"'{search_query}'에 대한 검색 결과가 없습니다.")
            else:
                st.error(f"API 요청 중 오류가 발생했습니다: {e}")
    else:
        st.warning("검색어를 입력해주세요.")
        st.session_state.search_results = None

# --- 검색 결과 및 뉴스 표시 ---
if st.session_state.search_results is not None and not st.session_state.search_results.empty:
    st.subheader("검색 결과")
    st.dataframe(st.session_state.search_results, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.subheader("최신 뉴스 조회")
    
    # 검색된 종목 리스트로 드롭다운 메뉴 생성
    df = st.session_state.search_results
    selected_stock = st.selectbox(
        "뉴스를 조회할 종목을 선택하세요:",
        options=df.to_dict('records'),
        format_func=lambda stock: f"{stock['종목명']} ({stock['종목코드']})" # 표시 형식 지정
    )

    if st.button("최신 뉴스 보기"):
        selected_code = selected_stock['종목코드']
        selected_name = selected_stock['종목명']
        with st.spinner(f"'{selected_name}'의 최신 뉴스를 가져오는 중..."):
            try:
                news_response = requests.get(f"{API_BASE_URL}/stocks/domestic/news", params={"code": selected_code, "limit": 5})
                news_response.raise_for_status()
                news_data = news_response.json().get('news', [])
                
                if news_data:
                    st.write(f"**'{selected_name}' 최신 뉴스 5건**")
                    for news_item in news_data:
                        st.markdown(f"- **[{news_item['title']}]({news_item['link']})**")
                        st.caption(f"{news_item['source']} | {news_item['date']}")
                else:
                    st.warning("최신 뉴스가 없습니다.")

            except requests.exceptions.RequestException:
                st.error("뉴스 정보를 가져오는 데 실패했습니다.")

st.markdown("---")

# --- 2. 주가 예측 기능 ---
st.header("2. 다음 거래일 종가 예측")

# 데이터 기간 선택
years_option = st.radio(
    "예측에 사용할 데이터 기간을 선택하세요:",
    ('1년', '2년', '3년'),
    horizontal=True,
    index=0 # 기본 선택을 '1년'으로
)
years_map = {'1년': 1, '2년': 2, '3년': 3}
years_to_fetch = years_map[years_option]

predict_code = st.text_input("예측할 종목의 코드를 입력하세요 (예: 005930)")

if st.button("예측 실행"):
    if predict_code:
        with st.spinner(f'{years_option}치 데이터를 기반으로 다음 거래일의 종가를 예측하는 중입니다...'):
            try:
                params = {"code": predict_code, "years": years_to_fetch}
                response = requests.get(f"{API_BASE_URL}/stocks/domestic/predict", params=params)
                response.raise_for_status()
                data = response.json()
                
                st.success(data['prediction_message'])

            except requests.exceptions.RequestException as e:
                if e.response and e.response.status_code == 404:
                    st.error(f"종목 코드 '{predict_code}'에 대한 데이터를 찾을 수 없습니다. 코드가 정확한지 확인해주세요.")
                elif e.response and e.response.status_code == 400:
                     st.error(f"예측에 필요한 데이터가 부족합니다. 다른 종목을 시도해보세요.")
                else:
                    st.error(f"API 요청 중 오류가 발생했습니다: {e}")
    else:
        st.warning("예측할 종목 코드를 입력해주세요.")
