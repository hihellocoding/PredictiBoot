# PredictiBoot

> TODO: 이 프로젝트에 대한 간략한 설명을 추가해주세요. (예: FastAPI를 사용하여 주식 데이터를 예측하는 API 서버)

---

## ⚙️ 기술 스택 및 주요 라이브러리

*   **Python** (TODO: 파이썬 버전을 입력해주세요. 예: 3.11)
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
git clone <your-repository-url>
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
*   `--reload` 옵션은 코드 변경 시 서버를 자동으로 재시작해주는 개발용 옵션입니다.

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
```
