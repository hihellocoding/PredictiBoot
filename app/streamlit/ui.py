import streamlit as st
import requests
import pandas as pd
import re
import sys
import os
import datetime # Added for date handling
import numpy as np # Added for np.nan

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
if 'stock_type' not in st.session_state:
    st.session_state.stock_type = 'Domestic' # 기본값은 국내

st.set_page_config(layout="wide")
st.title("🤖 AI 주가 예측 및 분석")
st.markdown("---")

# --- 사이드바: OpenAI API 키 입력 (원래 위치 유지) ---
st.sidebar.header("API 키 설정")
st.sidebar.caption("AI 분석 기능을 사용하려면 API 키가 필요합니다.")
openai_api_key = st.sidebar.text_input("OpenAI API 키를 입력하세요", type="password", help="API 키는 분석에만 사용되며 저장되지 않습니다.")

# --- 국내/해외 주식 선택 --- 
st.subheader("주식 시장 선택")
st.session_state.stock_type = st.radio(
    "분석할 주식 시장을 선택하세요:",
    ('국내', '해외'),
    horizontal=True,
    key="stock_market_selector"
)

st.markdown("---")

# --- 1. 종목 코드 검색 기능 ---
st.header("1. 종목 코드 검색")

if st.session_state.stock_type == '국내':
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

    # 국내 주식 검색 결과 표시
    if st.session_state.search_results is not None and not st.session_state.search_results.empty:
        st.subheader("검색 결과")
        df = st.session_state.search_results
        selected_index = st.radio(
            "분석할 종목을 선택하세요:",
            options=df.index,
            format_func=lambda i: f"{df.loc[i, 'name']} ({df.loc[i, 'code']})",
            key="domestic_search_radio"
        )
        st.session_state.stock_to_analyze = df.loc[selected_index]

else: # 해외 주식 선택 시
    st.caption("해외 주식은 티커(Ticker)를 직접 입력해주세요. (예: AAPL, MSFT)")
    st.session_state.search_results = None # 국내 검색 결과 초기화
    international_ticker_input = st.text_input("종목 티커 입력", placeholder="예: AAPL, MSFT")
    if international_ticker_input:
        st.session_state.stock_to_analyze = {'name': international_ticker_input, 'code': international_ticker_input} # 티커를 이름과 코드로 사용
    else:
        st.session_state.stock_to_analyze = None

st.markdown("---")

# --- 2. 예측 및 AI 분석 실행 ---
st.header("2. 예측 및 AI 분석 실행")

if st.session_state.stock_to_analyze is not None:
    selected_name = st.session_state.stock_to_analyze['name']
    selected_code = st.session_state.stock_to_analyze['code']
    st.info(f"선택된 종목: **{selected_name} ({selected_code})**")
else:
    st.warning("먼저 위에서 종목을 검색하고 선택해주세요. (해외 주식은 티커 직접 입력)")

# 데이터 기간 선택 옵션
years_option = st.radio(
    "예측에 사용할 데이터 기간을 선택하세요:",
    ('1년', '2년', '3년', '5년'),
    horizontal=True,
    index=0
)
years_map = {'1년': 1, '2년': 2, '3년': 3, '5년': 5}
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

        # 주식 유형에 따른 API 기본 경로 설정
        api_path_base = "domestic" if st.session_state.stock_type == '국내' else "international"

        with st.spinner(f"{years_option}치 데이터를 기반으로 예측 및 분석을 시작합니다..."):
            try:
                # 예측 API 호출
                if api_path_base == "domestic":
                    predict_params = {"code": stock_code, "years": years_to_fetch}
                    predict_response = requests.get(f"{API_BASE_URL}/stocks/{api_path_base}/predict", params=predict_params)
                    predict_response.raise_for_status()
                    prediction_message = predict_response.json().get('prediction_message', "예측 실패")
                else: # 해외 주식
                    # 해외 주식 예측은 아직 구현되지 않았으므로, 과거 데이터만 가져옴
                    predict_params = {"ticker": stock_code, "period": f"{years_to_fetch}y"}
                    predict_response = requests.get(f"{API_BASE_URL}/stocks/{api_path_base}/historical", params=predict_params)
                    predict_response.raise_for_status()
                    prediction_message = f"해외 주식 예측은 아직 구현되지 않았습니다. {stock_code}의 {years_to_fetch}치 과거 데이터를 가져왔습니다."

                # 예측 메시지에서 가격 추출 (국내 주식에만 해당)
                predicted_price_value = "N/A"
                if api_path_base == "domestic":
                    # Updated regex to extract the single predicted price from the new message format
                    price_match = re.search(r'예상 종가는 \*\*(\d{1,3}(?:,\d{3})*)\*\* 원', prediction_message)
                    if price_match:
                        predicted_price_value = price_match.group(1)
                        predicted_price_value = predicted_price_value.replace(',', '') # Remove commas for numeric conversion
                        predicted_price_value = float(predicted_price_value) # Convert to float

                # 뉴스 API 호출
                if api_path_base == "domestic":
                    news_params = {"code": stock_code, "limit": 15}
                    news_response = requests.get(f"{API_BASE_URL}/stocks/{api_path_base}/news", params=news_params)
                    news_response.raise_for_status()
                    news_articles = news_response.json().get('news', [])
                else:
                    st.warning("해외 주식 뉴스 가져오기는 아직 구현되지 않았습니다.")

                # --- 오늘 주가 차트 데이터 가져오기 (국내 주식만) ---
                intraday_data_df = pd.DataFrame()
                if api_path_base == "domestic":
                    today_date_str = datetime.datetime.now().strftime("%Y%m%d")
                    intraday_params = {"code": stock_code, "date": today_date_str}
                    intraday_response = requests.get(f"{API_BASE_URL}/stocks/{api_path_base}/intraday", params=intraday_params)
                    intraday_response.raise_for_status()
                    intraday_raw_data = intraday_response.json().get('intraday_data', [])
                    
                    # Always go to else block for now to show "개발 대기중"
                    # if intraday_raw_data:
                    #     intraday_data_df = pd.DataFrame(intraday_raw_data)
                    #     intraday_data_df['time'] = pd.to_datetime(intraday_data_df['time'], format='%H:%M').dt.time # Convert to time object
                    #     intraday_data_df.set_index('time', inplace=True)
                        
                    #     # 예측 가격을 차트에 표시하기 위한 데이터 준비
                    #     # '오늘 종가'와 '예측 종가'를 함께 표시
                    #     plot_df = pd.DataFrame(index=intraday_data_df.index)
                    #     plot_df['오늘 종가'] = intraday_data_df['closing_price']
                        
                    #     # 예측 가격을 마지막 시간대에만 표시
                    #     if predicted_price_value != "N/A":
                    #         # Create a series for predicted price, with NaN for all but the last index
                    #         predicted_series = pd.Series(np.nan, index=plot_df.index)
                    #         predicted_series.iloc[-1] = predicted_price_value
                    #         plot_df['예측 종가'] = predicted_series
                        
                    #     # Streamlit 차트 표시
                    #     with col1: # Display chart in col1
                    #         st.subheader(f"📈 {stock_name} ({stock_code}) 오늘 주가 흐름")
                    #         st.line_chart(plot_df)
                    # else:
                    with col1:
                        st.warning("분봉 차트 기능은 현재 개발 대기중입니다. (데이터 가져오기 문제)")
                # --- 차트 데이터 가져오기 끝 ---

            except requests.exceptions.RequestException as e:
                st.error(f"API 요청 실패: {e}")
                st.stop()
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
            print(f"DEBUG UI: prediction_message: {prediction_message}") # ADDED FOR DEBUGGING
            print(f"DEBUG UI: predicted_price_value: {predicted_price_value}") # ADDED FOR DEBUGGING
            with st.spinner("AI가 뉴스를 기반으로 예측을 분석하는 중입니다. 잠시만 기다려주세요..."):
                analysis_result = analyze_prediction_with_llm(
                    api_key=openai_api_key,
                    stock_name=stock_name,
                    prediction_message=prediction_message,
                    predicted_price_value=predicted_price_value, # Pass the numeric predicted value
                    news_articles=news_articles
                )
                print(f"DEBUG UI: analysis_result (before markdown): {analysis_result[:200]}...") # ADDED FOR DEBUGGING
                try:
                    st.markdown(analysis_result.encode('utf-8').decode('utf-8'))
                except UnicodeEncodeError as e:
                    st.error(f"분석 결과 표시 오류: {e}. 터미널 인코딩을 확인해주세요.")
                    st.markdown(analysis_result.encode('ascii', 'replace').decode('ascii')) # 대체 표시

