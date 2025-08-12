# PredictiBoot

> 이 프로그램은 과거 1~3년간의 주가 데이터(고가·종가 등) 를 분석하여, 예측 알고리즘을 통해 현재 시점의 종가를 산출합니다.
뿐만 아니라, 최신 뉴스 기사를 자동 수집하여 대규모 언어 모델(LLM)에 예측 가격과 함께 제공함으로써,
인공지능의 종합적인 판단과 해석을 더해 보다 신뢰도 높은 예측 결과를 제공합니다.

주요 기능

📊 데이터 기반 예측: 과거 주가 데이터를 분석하여 미래 종가를 계산

📰 뉴스 분석 통합: 관련 최신 뉴스 기사 자동 수집

🤖 AI 분석 지원: LLM을 활용한 종합 평가 및 의견 제시

💡 의사결정 보조: 데이터와 AI 판단을 결합한 투자 참고 정보 제공

---

## ⚙️ 기술 스택 및 주요 라이브러리

* **Python** 3.12.2
* **FastAPI**: 빠르고 현대적인 API 개발용 웹 프레임워크
* **Uvicorn**: 고성능 ASGI 서버, FastAPI와 궁합이 뛰어남
* **Streamlit**: 데이터 기반 앱을 쉽고 빠르게 제작·공유
* **Pandas**: 데이터 분석, 시계열 처리, 통계 연산에 강력
* **pykrx**: 한국거래소(KRX) 주식 데이터 수집
* **Statsmodels**: 통계 분석과 모델링 도구
* **BeautifulSoup4**: HTML·XML 데이터 파싱
* **Requests**: 간단하고 강력한 HTTP 요청 라이브러리


---

## 🚀 프로젝트 설정 및 실행

### 1. 저장소 복제 및 디렉토리 이동
```bash
git clone https://github.com/hihellocoding/PredictiBoot.git
cd PredictiBoot
```

### 2. 가상 환경 생성 및 활성화
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 필요 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 4. FastAPI 서버 실행
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Streamlit 앱 실행
```bash
streamlit run app/streamlit/ui.py
```

---

## 📚 API 문서 (Swagger UI)

FastAPI 서버가 실행되면, 웹 브라우저에서 아래 주소로 접속하여 API 문서를 확인하고 테스트할 수 있습니다.

*   **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
*   **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📦 전체 라이브러리 목록

`requirements.txt` 파일에 명시된 전체 라이브러리 목록입니다.

```
fastapi
uvicorn
requests
beautifulsoup4
pandas
lxml
statsmodels
pytz
pykrx
streamlit
selenium
openai
yfinance
```

---

## ⚖️ License

This software is provided under a custom, restrictive license.

Copyright (c) 2025 박규태 (gocyzhod@gmail.com)
All rights reserved.

본 소프트웨어와 그 소스코드는 제작자의 사전 서면 동의 없이 복제, 수정, 배포할 수 없습니다.
무단 사용 시 저작권법 및 관련 법률에 따라 민·형사상 책임을 물을 수 있습니다.


For more details, please refer to the `LICENSE` file in the repository root.
