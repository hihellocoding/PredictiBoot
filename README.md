# PredictiBoot

> 이 프로그램은 과거 1~3년간의 주가 데이터를 분석하여, 정교한 하이브리드 예측 모델을 통해 미래의 종가를 산출합니다.
> 단순 시계열 분석을 넘어, 최신 뉴스 기사를 자동 수집하고 대규모 언어 모델(LLM)의 종합적인 판단까지 더하여 투자 결정에 깊이를 더합니다.

## 🌟 주요 기능

📊 **고도화된 하이브리드 예측**: LSTM(시계열 특화)과 XGBoost(기술적 지표 특화) 모델의 장점을 결합한 스태킹(Stacking) 앙상블 모델을 통해 보다 정확하고 안정적인 예측을 수행합니다.

📰 **뉴스 분석 통합**: 관련 최신 뉴스 기사를 자동 수집하여 AI 분석의 근거 자료로 활용합니다.

🤖 **AI 종합 분석**: LLM이 예측된 가격과 최신 뉴스를 종합적으로 검토하여, 투자에 대한 다각적인 시각과 의견을 제시합니다.

💡 **의사결정 보조**: 데이터 기반의 예측과 AI의 정성적 분석을 결합하여, 사용자가 더 나은 투자 결정을 내릴 수 있도록 지원합니다.

---

## 🧠 예측 모델 아키텍처

본 프로젝트는 단일 모델의 한계를 극복하고 예측 정확도를 높이기 위해 **스태킹 앙상블(Stacking Ensemble)** 기법을 기반으로 한 하이브리드 모델을 채택했습니다.

### 1. 1차 예측 모델 (Base Models)

서로 다른 관점에서 주가를 분석하는 두 개의 독립적인 모델을 1차 예측기로 사용합니다.

#### 가. LSTM (Long Short-Term Memory)
- **역할**: 주가 데이터의 **시간적 순서(Temporal Sequence)** 와 장기 의존성을 학습하여 시계열 패턴을 파악합니다.
- **주요 입력 피처**: `종가`, `시가`, `고가`, `저가`, `거래량`
- **핵심 파라미터**:
    - **Sequence Length**: `60일`의 데이터를 하나의 시퀀스로 사용하여 다음 날을 예측합니다.
    - **모델 구조**: 2개의 LSTM 레이어와 2개의 Dropout 레이어를 포함한 심층 신경망 구조로, 과적합을 방지하고 일반화 성능을 높였습니다.
    - **학습**: `Adam` 옵티마이저와 `Mean Squared Error` 손실 함수를 사용합니다.

#### 나. XGBoost (eXtreme Gradient Boosting)
- **역할**: 다양한 **기술적 지표(Technical Indicators)** 들 간의 복잡한 비선형 관계를 학습합니다. 시계열 패턴보다는 특정 시점의 데이터 포인트를 기반으로 예측합니다.
- **주요 입력 피처**:
    - **이동 평균 (SMA)**: `5일`, `20일` 이동 평균선
    - **상대 강도 지수 (RSI)**: `14일` RSI
    - **가격 변동률**: 일일 가격 변동률
- **핵심 파라미터**:
    - **Objective**: `reg:squarederror` (회귀 문제)
    - **n_estimators**: `500`개의 결정 트리를 사용하여 부스팅 모델을 구성합니다.

### 2. 2차 메타 모델 (Meta-Model)

- **역할**: 1차 모델들(LSTM, XGBoost)이 각각 내놓은 예측 결과를 다시 입력으로 받아, 두 모델의 예측을 **지능적으로 결합**하는 최종 예측기를 학습합니다.
- **모델 종류**: **`LinearRegression` (선형 회귀)**
- **학습 과정**:
    1.  전체 학습 데이터 중 마지막 `60일`을 **메타 모델 학습용 데이터**로 분리합니다.
    2.  나머지 데이터로 LSTM과 XGBoost를 각각 학습시킨 후, 분리해 둔 `60일`치 데이터를 예측합니다.
    3.  이때 나온 **두 모델의 예측값**을 **입력 피처(X)** 로, **실제 주가**를 **타겟(y)** 으로 하여 메타 모델인 선형 회귀 모델을 학습시킵니다.
    4.  이 과정을 통해 메타 모델은 "LSTM 예측값이 이럴 때, XGBoost 예측값이 저럴 때는 실제 값에 더 가깝더라"와 같은 패턴을 학습하여, 각 모델의 예측 결과에 대한 최적의 가중치를 부여하는 것과 같은 효과를 냅니다.

### 3. 최종 예측 프로세스

1.  **전체 데이터 재학습**: 예측을 원하는 시점의 **전체 과거 데이터**를 사용하여 LSTM과 XGBoost 모델을 각각 재학습합니다.
2.  **1차 예측 생성**: 재학습된 두 모델로 다음 날의 종가를 각각 예측합니다.
3.  **최종 예측**: 두 모델의 예측값을 이미 학습된 **메타 모델**에 입력하여, 최종적이고 가장 정교한 단일 예측치를 산출합니다.

---

## ⚙️ 기술 스택 및 주요 라이브러리

*   **Python** 3.12.2
*   **FastAPI**: 빠르고 현대적인 API 개발용 웹 프레임워크
*   **Uvicorn**: 고성능 ASGI 서버
*   **Streamlit**: 데이터 기반 인터랙티브 앱 제작
*   **TensorFlow / Keras**: LSTM 딥러닝 모델 구축
*   **XGBoost**: 스태킹 모델의 한 축을 담당하는 고성능 그래디언트 부스팅 라이브러리
*   **Scikit-learn**: 머신러닝 모델 및 데이터 처리
*   **Pandas**: 데이터 분석, 시계열 처리, 통계 연산
*   **pykrx**: 한국거래소(KRX) 주식 데이터 수집
*   **Statsmodels**: 통계 분석과 모델링 도구
*   **BeautifulSoup4**: HTML·XML 데이터 파싱
*   **Requests**: 간단하고 강력한 HTTP 요청 라이브.

---

## 🚀 프로젝트 설정 및 실행

### 0. (macOS 사용자) 필수 라이브러리 설치
Homebrew를 사용하여 `xgboost`에 필요한 `libomp` 라이브러리를 설치합니다.
```bash
brew install libomp
```

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
백엔드 API 서버를 실행합니다.
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 5. Streamlit 앱 실행
**새로운 터미널**을 열고 프론트엔드 UI를 실행합니다.
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
scikit-learn
tensorflow
xgboost
```

---

## ⚖️ License

This software is provided under a custom, restrictive license.

Copyright (c) 2025 박규태 (gocyzhod@gmail.com)
All rights reserved.

본 소프트웨어와 그 소스코드는 제작자의 사전 서면 동의 없이 복제, 수정, 배포할 수 없습니다.
무단 사용 시 저작권법 및 관련 법률에 따라 민·형사상 책임을 물을 수 있습니다.


For more details, please refer to the `LICENSE` file in the repository root.
