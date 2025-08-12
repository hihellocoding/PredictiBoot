# PredictiBoot

> 1~3년 주식 고가 종가 등의 데이터를 기반으로 예측 알고리즘을 통해 현재일 기준으로 종가를 예측하는 프로그램.
> 또한, 기사 스크랩을 통해 LLM 에 기사와 예측가를 던짐으로써 인공지능의 판단까지 더한다.

---

## ⚙️ 기술 스택 및 주요 라이브러리

*   **Python** 3.12.2
*   **FastAPI**: Modern, fast (high-performance), web framework for building APIs.
*   **Uvicorn**: Lightning-fast ASGI server.
*   **Streamlit**: The fastest way to build and share data apps.
*   **Pandas**: Powerful data structures for data analysis, time series, and statistics.
*   **pykrx**: KRX (Korea Exchange) stock market data scraper.
*   **Statsmodels**: Statistical computation and modeling.
*   **BeautifulSoup4**: For pulling data out of HTML and XML files.
*   **Requests**: Simple, yet elegant, HTTP library.

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