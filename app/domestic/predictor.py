
import pandas as pd
import numpy as np
import warnings
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

def predict_next_day_price(historical_data: list) -> float:
    """
    과거 시세 데이터(OHLCV)를 사용하여 다음 날의 종가를 예측합니다.
    LSTM 신경망 모델을 사용합니다.

    Args:
        historical_data: 크롤링된 일별 시세 데이터 리스트

    Returns:
        예측된 다음 날의 종가
    """
    # LSTM 모델 학습을 위해 최소 60일의 데이터가 필요하다고 가정
    if not historical_data or len(historical_data) < 60:
        raise ValueError("Not enough historical data for LSTM model (requires at least 60 days).")

    # 1. 데이터 준비
    df = pd.DataFrame(historical_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df = df.sort_index()

    # 사용할 특성 선택 (종가, 시가, 고가, 저가, 거래량)
    features = ['closing_price', 'opening_price', 'high_price', 'low_price', 'volume']
    data = df[features].copy()
    
    # 거래량 데이터 타입 변환 및 오류 처리
    data['volume'] = pd.to_numeric(data['volume'], errors='coerce')
    data.dropna(inplace=True) # NaN 값이 있는 행 제거

    # 2. 데이터 정규화
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    
    # 종가 예측을 위해 종가 스케일러를 따로 만듦 (역변환에 사용)
    scaler_close = MinMaxScaler(feature_range=(0,1))
    scaler_close.fit_transform(data[['closing_price']])

    # 3. 훈련 데이터셋 생성
    prediction_days = 60  # 과거 60일 데이터를 기반으로 예측
    x_train, y_train = [], []

    for i in range(prediction_days, len(scaled_data)):
        x_train.append(scaled_data[i-prediction_days:i])
        y_train.append(scaled_data[i, 0]) # 0은 종가(closing_price) 인덱스

    x_train, y_train = np.array(x_train), np.array(y_train)

    # 4. LSTM 모델 구축
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], x_train.shape[2])))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(units=25))
    model.add(Dense(units=1)) # 최종 출력은 1개 (다음 날 종가)

    model.compile(optimizer='adam', loss='mean_squared_error')

    # 5. 모델 학습
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        model.fit(x_train, y_train, batch_size=32, epochs=20, verbose=0)

    # 6. 다음 날 종가 예측
    # 예측을 위해 최근 60일치 데이터 준비
    last_60_days = scaled_data[-prediction_days:]
    x_test = np.array([last_60_days])
    
    predicted_price_scaled = model.predict(x_test, verbose=0)

    # 7. 예측된 가격을 원래 스케일로 역변환
    predicted_price = scaler_close.inverse_transform(predicted_price_scaled)

    return float(predicted_price[0][0])
