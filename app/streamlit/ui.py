import streamlit as st
import requests
import pandas as pd
import re
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.llm_analyzer import analyze_prediction_with_llm

# FastAPI 서버의 기본 URL
API_BASE_URL = "http://127.0.0.1:8000"

# --- 세션 상태 초기화 ---
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'stock_to_analyze' not in st.session_state:
    st.session_state.stock_to_analyze = None

st.set_page_config(layout="wide")
st.title("🤖 AI 주가 예측 및 분석")
st.markdown("--- ")

# --- 사이드바: OpenAI API 키 입력 ---
st.sidebar.header("API 키 설정")
st.sidebar.caption("AI 분석 기능을 사용하려면 API 키가 필요합니다.")
openai_api_key = st.sidebar.text_input("OpenAI API 키를 입력하세요", type="password", help="API 키는 분석에만 사용되며 저장되지 않습니다.")

# --- 1. 종목 코드 검색 기능 ---
st.header("1. 분석할 종목 검색")
st.caption("분석하고 싶은 종목의 코드를 모를 때 사용하세요.")
search_query = st.text_input("회사 이름을 입력하세요", placeholder="예: 삼성전자, 카카오")

if st.button("종목 검색"):
    st.session_state.stock_to_analyze = None # 새로운 검색 시 선택 초기화
    if search_query:
        try:
            response = requests.get(f"{API_BASE_URL}/stocks/domestic/search", params={"query": search_query})
            response.raise_for_status()
            data = response.json()
            st.session_state.search_results = pd.DataFrame(data['results'])
        except requests.exceptions.RequestException as e:
            st.session_state.search_results = None
            if e.response and e.response.status_code == 404:
                st.error(f"'{search_query}'에 대한 검색 결과가 없습니다.")
            else:
                st.error(f"API 요청 중 오류가 발생했습니다: {e}")
    else:
        st.warning("검색할 회사 이름을 입력해주세요.")
        st.session_state.search_results = None

# --- 2. 분석할 종목 선택 --- 
if st.session_state.search_results is not None and not st.session_state.search_results.empty:
    st.subheader("검색 결과")
    df = st.session_state.search_results
    selected_index = st.radio(
        "분석할 종목을 선택하세요:",
        options=df.index,
        format_func=lambda i: f"{df.loc[i, 'name']} ({df.loc[i, 'code']})",
        label_visibility="collapsed"
    )
    st.session_state.stock_to_analyze = df.loc[selected_index]

st.markdown("--- ")

# --- 3. 예측 및 AI 분석 실행 ---
st.header("2. 예측 및 AI 분석 실행")

if st.session_state.stock_to_analyze is not None:
    selected_name = st.session_state.stock_to_analyze['name']
    selected_code = st.session_state.stock_to_analyze['code']
    st.info(f"선택된 종목: **{selected_name} ({selected_code})**")
else:
    st.warning("먼저 위에서 종목을 검색하고 선택해주세요.")

# 데이터 기간 선택 옵션 (복원)
years_option = st.radio(
    "예측에 사용할 데이터 기간을 선택하세요:",
    ('1년', '2년', '3년'),
    horizontal=True,
    index=0
)
years_map = {'1년': 1, '2년': 2, '3년': 3}
years_to_fetch = years_map[years_option]

if st.button("분석 시작 🚀", use_container_width=True, disabled=(st.session_state.stock_to_analyze is None)):
    if not openai_api_key:
        st.error("사이드바에 OpenAI API 키를 입력해주세요.")
    else:
        col1, col2 = st.columns(2)
        prediction_message = None
        news_articles = []
        stock_name = st.session_state.stock_to_analyze['name']
        stock_code = st.session_state.stock_to_analyze['code']

        with st.spinner(f"{years_option}치 데이터를 기반으로 예측 및 분석을 시작합니다..."):
            try:
                predict_params = {"code": stock_code, "years": years_to_fetch}
                predict_response = requests.get(f"{API_BASE_URL}/stocks/domestic/predict", params=predict_params)
                predict_response.raise_for_status()
                prediction_message = predict_response.json().get('prediction_message', "예측 실패")

                # 예측 메시지에서 가격 추출
                predicted_price_value = "가격 정보 없음"
                price_match = re.search(r'(\d{1,3}(?:,\d{3})*)원', prediction_message)
                if price_match:
                    predicted_price_value = price_match.group(1)
                    predicted_price_value = predicted_price_value.replace('원', '').strip() # '원' 기호 제거
                    predicted_price_value = predicted_price_value.replace(',', '') # 쉼표 제거 (LLM이 숫자로 인식하기 쉽게)

                # 종목명 추출 (예측 메시지에서)
                if '(' in prediction_message:
                    stock_name = prediction_message.split('(')[0]

                news_params = {"code": stock_code, "limit": 5}
                news_response = requests.get(f"{API_BASE_URL}/stocks/domestic/news", params=news_params)
                news_response.raise_for_status()
                news_articles = news_response.json().get('news', [])

            except requests.exceptions.RequestException as e:
                st.error(f"API 요청 실패: {e}")
                st.stop()
        
        with col1:
            st.subheader("📈 자체 예측 결과")
            st.success(prediction_message)
            st.subheader("📰 관련 최신 뉴스")
            if news_articles:
                for news_item in news_articles:
                    st.markdown(f"- **[{news_item['title']}]({news_item['link']})**")
                    st.caption(f"{news_item['source']} | {news_item['date']}")
            else:
                st.warning("수집된 뉴스가 없습니다.")

        with col2:
            st.subheader("🤖 LLM 기반 종합 분석")
            with st.spinner("AI is analyzing prediction based on news. Please wait..."):
                analysis_result = analyze_prediction_with_llm(
                    api_key=openai_api_key,
                    stock_name=stock_name,
                    prediction_message=prediction_message,
                    predicted_price_value=predicted_price_value,
                    news_articles=news_articles
                )
                try:
                    st.markdown(analysis_result.encode('utf-8').decode('utf-8'))
                except UnicodeEncodeError as e:
                    st.error(f"Error displaying analysis result: {e}. Please check terminal encoding.")
                    st.markdown(analysis_result.encode('ascii', 'replace').decode('ascii')) # Fallback to show something
