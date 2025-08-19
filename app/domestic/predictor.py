import pandas as pd
import numpy as np
import warnings
import xgboost as xgb
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

# 경고 무시
warnings.filterwarnings("ignore")


def _create_features(df: pd.DataFrame) -> pd.DataFrame:
    """XGBoost 모델을 위한 기술적 지표(피처)를 생성합니다."""
    df_new = df.copy()
    df_new['sma5'] = df_new['closing_price'].rolling(5).mean()
    df_new['sma20'] = df_new['closing_price'].rolling(20).mean()
    delta = df_new['closing_price'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df_new['rsi'] = 100 - (100 / (1 + rs))
    df_new['price_change_ratio'] = df_new['closing_price'].pct_change()
    return df_new

def _train_and_predict_lstm(train_df: pd.DataFrame, predict_df: pd.DataFrame) -> np.ndarray:
    """주어진 데이터로 LSTM을 학습하고 예측합니다."""
    features = ['closing_price', 'opening_price', 'high_price', 'low_price', 'volume']
    train_data = train_df[features].values
    
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaler.fit(train_data)
    train_data_scaled = scaler.transform(train_data)
    
    scaler_close = MinMaxScaler(feature_range=(0, 1))
    scaler_close.fit(train_df[['closing_price']])

    prediction_days = 60
    x_train, y_train = [], []
    for i in range(prediction_days, len(train_data_scaled)):
        x_train.append(train_data_scaled[i-prediction_days:i])
        y_train.append(train_data_scaled[i, 0])
    x_train, y_train = np.array(x_train), np.array(y_train)

    model = Sequential([
        LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], x_train.shape[2])),
        Dropout(0.2),
        LSTM(units=50, return_sequences=False),
        Dropout(0.2),
        Dense(units=25),
        Dense(units=1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(x_train, y_train, batch_size=32, epochs=50, verbose=0)

    # 예측할 데이터 준비
    total_data = pd.concat([train_df[features], predict_df[features]], axis=0)
    inputs = total_data[len(total_data) - len(predict_df) - prediction_days:].values
    inputs_scaled = scaler.transform(inputs)

    x_predict = []
    for i in range(prediction_days, len(inputs_scaled)):
        x_predict.append(inputs_scaled[i-prediction_days:i])
    x_predict = np.array(x_predict)

    predictions_scaled = model.predict(x_predict, verbose=0)
    predictions = scaler_close.inverse_transform(predictions_scaled)
    return predictions.flatten()

def predict_next_day_price_stacking_hybrid(historical_data: list) -> float:
    """
    스태킹(Stacking) 하이브리드 모델을 사용하여 다음 날의 종가를 예측합니다.
    1. LSTM과 XGBoost를 1차 모델로 사용하여 각각 예측을 생성합니다.
    2. 두 모델의 예측 결과를 입력으로 받아, 최종 예측을 생성하는 2차 모델(메타 모델)을 학습시킵니다.
    """
    if len(historical_data) < 90: # 학습 + 검증을 위해 최소 데이터 요구량 증가
        raise ValueError("Not enough historical data for Stacking model (requires at least 90 days).")

    df = pd.DataFrame(historical_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    
    # 'change' 컬럼 제거 (object 타입으로 인해 XGBoost 오류 발생 방지)
    if 'change' in df.columns:
        df = df.drop(columns=['change'])
    df.dropna(inplace=True)

    # --- XGBoost 모델을 위한 피처 및 타겟 생성 ---
    df_features = _create_features(df)
    # 예측 타겟(다음 날 종가) 생성
    df_features['target'] = df_features['closing_price'].shift(-1)
    df_features.dropna(inplace=True)

    # --- 데이터 분리 (학습용 / 메타 모델 학습용) ---
    meta_model_train_size = 60 # 마지막 60일을 메타 모델 학습에 사용
    
    # 원본 데이터프레임 분리
    train_df = df[df.index.isin(df_features.index)][:-meta_model_train_size]
    meta_train_df = df[df.index.isin(df_features.index)][-meta_model_train_size:]

    # 피처 데이터프레임 분리
    train_features_df = df_features[:-meta_model_train_size]
    meta_features_df = df_features[-meta_model_train_size:]

    # --- 1차 모델들로 메타 모델의 학습 데이터 생성 ---
    # LSTM 예측
    lstm_preds_for_meta = _train_and_predict_lstm(train_df, meta_train_df)
    
    # XGBoost 예측
    features_to_use = [col for col in df_features.columns if col not in ['target']]
    X_train_xgb = train_features_df[features_to_use]
    y_train_xgb = train_features_df['target']
    X_meta_xgb = meta_features_df[features_to_use]

    xgb_model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=500, random_state=42)
    xgb_model.fit(X_train_xgb, y_train_xgb)
    xgb_preds_for_meta = xgb_model.predict(X_meta_xgb)

    # --- 메타 모델 학습 ---
    X_meta_train = np.c_[lstm_preds_for_meta, xgb_preds_for_meta] # 두 모델의 예측을 피처로 사용
    y_meta_train = meta_features_df['target'].values

    meta_model = LinearRegression()
    meta_model.fit(X_meta_train, y_meta_train)

    # --- 최종 예측 (내일 예측) ---
    # 1. 전체 데이터로 LSTM 재학습 및 예측
    lstm_final_pred = _train_and_predict_lstm(df, df.iloc[[-1]])[0]

    # 2. 전체 데이터로 XGBoost 재학습 및 예측
    X_full_xgb = df_features[features_to_use]
    y_full_xgb = df_features['target']
    
    xgb_model_final = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=500, random_state=42)
    xgb_model_final.fit(X_full_xgb, y_full_xgb)
    
    # XGBoost 예측에는 마지막 피처 행 사용
    xgb_final_pred = xgb_model_final.predict(df_features[features_to_use].iloc[[-1]])[0]

    # 3. 학습된 메타 모델로 최종 결과 조합
    final_prediction = meta_model.predict(np.c_[[lstm_final_pred], [xgb_final_pred]])

    return float(final_prediction[0])