
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import warnings

def predict_next_day_price(historical_data: list) -> float:
    """
    과거 시세 데이터를 사용하여 다음 날의 종가를 예측합니다.

    Args:
        historical_data: 크롤링된 일별 시세 데이터 리스트

    Returns:
        예측된 다음 날의 종가
    """
    if not historical_data or len(historical_data) < 20: # ARIMA 모델 학습을 위해 최소 데이터 수 확보
        raise ValueError("Not enough historical data to make a prediction.")

    # 1. 데이터 준비
    df = pd.DataFrame(historical_data)
    # 날짜를 datetime 객체로 변환하고 인덱스로 설정
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    # 크롤링된 데이터가 최신순이므로, 시간 순서대로 (과거 -> 현재) 정렬
    df = df.sort_index()

    # 종가(closing_price) 데이터만 사용
    ts_data = df['closing_price']

    # 2. ARIMA 모델 학습
    # ARIMA(p,d,q) - p: AR(자기회귀) 차수, d: 차분 차수, q: MA(이동평균) 차수
    # 여기서는 일반적인 값인 (5,1,0)을 사용합니다.
    order = (5, 1, 0)
    
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore") # 수렴 경고 등 무시
        model = ARIMA(ts_data, order=order)
        model_fit = model.fit()

    # 3. 다음 날 예측
    # forecast(steps=1)는 다음 1개의 데이터를 예측합니다.
    prediction = model_fit.forecast(steps=1)

    return prediction.iloc[0]
