import openai
import sys
import logging

# 강제로 stdout 인코딩을 UTF-8로 설정 (환경 문제 우회용)
sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers: # Ensure a handler is added if not already present
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def analyze_prediction_with_llm(api_key: str, stock_name: str, prediction_message: str, predicted_price_value: str, news_articles: list):
    print("--- LLM Analyzer: Function Entry (via print) ---")
    logger.info("--- LLM Analyzer: Function Entry (via logger) ---")

    print(f"Stock Name: {stock_name}")
    print(f"Prediction Message: {prediction_message}")
    print(f"Predicted Price Value: {predicted_price_value}")
    print(f"Number of News Articles: {len(news_articles)}")

    if not api_key:
        print("--- LLM Analyzer: Error - API Key not provided (via print) ---")
        logger.error("--- LLM Analyzer: Error - API Key not provided (via logger) ---")
        return "오류: OpenAI API 키가 제공되지 않았습니다."

    try:
        print("--- LLM Analyzer: Initializing OpenAI client (via print) ---")
        logger.info("--- LLM Analyzer: Initializing OpenAI client (via logger) ---")
        client = openai.OpenAI(api_key=api_key)
        print("--- LLM Analyzer: OpenAI client initialized (via print) ---")
        logger.info("--- LLM Analyzer: OpenAI client initialized (via logger) ---")
    except Exception as e:
        print(f"--- LLM Analyzer: Error - Client initialization failed: {e} (via print) ---")
        logger.error(f"--- LLM Analyzer: Error - Client initialization failed: {e} (via logger) ---")
        return f"오류: OpenAI 클라이언트 초기화에 실패했습니다. {e}"

    # 뉴스 기사들을 하나의 문자열로 조합
    news_summary = "\n".join([
        f"- 제목: {article['title']}\n  출처: {article['source']}\n  날짜: {article['date']}"
        for article in news_articles
    ])

    if not news_articles:
        news_summary = "제공된 최신 뉴스가 없습니다."

    print("--- LLM Analyzer: News Summary constructed (via print) ---")
    logger.info("--- LLM Analyzer: News Summary constructed (via logger) ---")

    # LLM에게 보낼 프롬프트 구성
    prompt = f"""
    당신은 수년간의 경험을 가진 전문 주식 트레이더입니다. 당신 앞에는 자체 개발한 예측 프로그램의 결과와 관련 최신 뉴스가 있습니다. 
    
    **분석 대상 정보:**
    1. **종목명:** {stock_name}
    2. **예측 프로그램 결과:** {prediction_message}
    3. **예측된 종가:** {predicted_price_value}
    4. **관련 최신 뉴스:**
    {news_summary}

    **분석 요청:**
    이 정보를 바탕으로, 예측 프로그램의 결과가 다음 거래일에 실현될 가능성에 대해 어떻게 생각하십니까? 특히 예측된 종가({predicted_price_value})가 현재 뉴스 상황을 고려했을 때 합리적인 가격인지 평가해주세요. 아래 형식에 맞춰 답변해주세요.

    1.  **예측 실현 확률:** 예측 결과가 맞을 확률을 퍼센트(%)로 제시해주세요.
    2.  **긍정적 의견:** 주가에 긍정적인 영향을 줄 수 있는 뉴스는 무엇이며, 왜 그렇게 생각하는지 요약해주세요.
    3.  **부정적 의견:** 주가에 부정적인 영향을 줄 수 있는 뉴스는 무엇이며, 왜 그렇게 생각하는지 요약해주세요.
    4.  **최종 결론:** 위 내용을 종합하여 당신의 최종 의견을 말해주세요.
    """

    print("--- LLM Analyzer: Prompt constructed (via print) ---")
    logger.info("--- LLM Analyzer: Prompt constructed (via logger) ---")
    # print(f"Full Prompt: {prompt[:500]}...") # 프롬프트가 너무 길면 터미널에 부담

    try:
        print("--- LLM Analyzer: Calling OpenAI API (via print) ---")
        logger.info("--- LLM Analyzer: Calling OpenAI API (via logger) ---")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 수년간의 경험을 가진 전문 주식 트레이더입니다."},
                {"role": "user", "content": prompt.encode('utf-8').decode('utf-8')} # Force UTF-8 encoding/decoding
            ],
            temperature=0.5,
        )
        print("--- LLM Analyzer: OpenAI API call successful (via print) ---")
        logger.info("--- LLM Analyzer: OpenAI API call successful (via logger) ---")
        return response.choices[0].message.content

    except openai.APIConnectionError as e:
        print(f"--- LLM Analyzer: Error - API Connection Failed: {e} (via print) ---")
        logger.error(f"--- LLM Analyzer: Error - API Connection Failed: {e} (via logger) ---")
        return f"OpenAI 서버 연결에 실패했습니다: {e}"
    except openai.RateLimitError as e:
        print(f"--- LLM Analyzer: Error - Rate Limit Exceeded: {e} (via print) ---")
        logger.error(f"--- LLM Analyzer: Error - Rate Limit Exceeded: {e} (via logger) ---")
        return f"OpenAI API 사용량 한도 초과입니다: {e}"
    except openai.AuthenticationError as e:
        print(f"--- LLM Analyzer: Error - Authentication Failed: {e} (via print) ---")
        logger.error(f"--- LLM Analyzer: Error - Authentication Failed: {e} (via logger) ---")
        return f"OpenAI API 키가 유효하지 않거나 인증에 실패했습니다: {e}"
    except openai.APIStatusError as e:
        print(f"--- LLM Analyzer: Error - API Status Error ({e.status_code}): {e.response} (via print) ---")
        logger.error(f"--- LLM Analyzer: Error - API Status Error ({e.status_code}): {e.response} (via logger) ---")
        return f"OpenAI API 에러가 발생했습니다 (상태 코드: {e.status_code}): {e.response}"
    except Exception as e:
        print(f"--- LLM Analyzer: Error - Unexpected Error: {e} (via print) ---")
        logger.error(f"--- LLM Analyzer: Error - Unexpected Error: {e} (via logger) ---")
        return f"예상치 못한 오류가 발생했습니다: {e}"