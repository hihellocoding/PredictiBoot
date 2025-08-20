from fastapi import APIRouter, Query, HTTPException
from ..domestic.crawler import get_historical_data, get_stock_name, get_stock_news, get_intraday_data
from ..domestic.predictor import predict_next_day_price_stacking_hybrid
from ..domestic.search import find_stock_code
import pandas as pd
import datetime
import pytz
import locale

# 가격을 원화(KRW) 형식으로 포맷하기 위해 로케일 설정
locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')

router = APIRouter(
    prefix="/stocks",
    tags=["stocks"],
)

@router.get("/domestic/search")
async def search_stock_code(
    query: str = Query(..., description="Name of the company to search for (e.g., '삼성')")
):
    """
    Search for stock codes by company name.
    """
    results = find_stock_code(query)
    if not results:
        raise HTTPException(status_code=404, detail=f"No stocks found for query: '{query}'")
    return {"results": results}

@router.get("/domestic/news")
async def get_domestic_stock_news(
    code: str = Query(..., description="Stock code to get news for (e.g., '005930')"),
    limit: int = Query(5, description="Number of news articles to fetch")
):
    """
    Get the latest news for a given stock code.
    """
    news_result = get_stock_news(code, limit)
    
    if isinstance(news_result, dict) and "error" in news_result:
        raise HTTPException(status_code=500, detail=news_result["error"])
    
    return {"news": news_result}

@router.get("/domestic/predict", response_model=dict)
async def predict_domestic_stock(
    code: str = Query(..., description="Stock code to predict (e.g., '005930')"),
    years: int = Query(1, description="Number of years of historical data to use (1, 2, 3, or 5)")
):
    if years not in [1, 2, 3, 5]:
        raise HTTPException(status_code=400, detail="Years must be 1, 2, 3, or 5.")

    # 1. Get stock name and current time in KST
    stock_name = get_stock_name(code)
    kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.datetime.now(kst)
    market_close_time = datetime.time(15, 30)

    # 2. Fetch historical data
    historical_data = get_historical_data(code, years)
    if not isinstance(historical_data, list) or not historical_data:
        raise HTTPException(status_code=404, detail="Could not retrieve historical data.")

    try:
        # 3. Determine data range based on current time
        if now_kst.time() < market_close_time:
            # Before market close: Use data up to yesterday to predict for today
            today_str = now_kst.strftime('%Y.%m.%d')
            data_for_prediction = [d for d in historical_data if d.get('date') != today_str]
            prediction_type_message = "오늘"
        else:
            # After market close: Use data up to today to predict for tomorrow
            data_for_prediction = historical_data
            prediction_type_message = "내일"

        if not data_for_prediction:
            raise HTTPException(status_code=404, detail="Not enough historical data to make a prediction.")

        # 4. Predict the next day's price
        predicted_price = predict_next_day_price_stacking_hybrid(data_for_prediction)

        # 5. Determine the target date for the prediction message
        last_data_date_str = data_for_prediction[-1]['date']
        last_data_date = datetime.datetime.strptime(last_data_date_str, '%Y.%m.%d')
        
        prediction_target_date = last_data_date + datetime.timedelta(days=1)
        # Skip weekends to find the next business day
        while prediction_target_date.weekday() >= 5:  # 5: Saturday, 6: Sunday
            prediction_target_date += datetime.timedelta(days=1)

        # 6. Format the response
        formatted_date = f"{prediction_target_date.month}월 {prediction_target_date.day}일"
        formatted_price = f"{locale.format_string('%d', int(predicted_price), grouping=True)}원"

        prediction_message = f"{stock_name}({code})의 {formatted_date}({prediction_type_message}) 예상 종가는 **{formatted_price}** 입니다. (스태킹 하이브리드 모델)"

        return {"prediction_message": prediction_message}

    except ValueError as e:
        print(f"DEBUG: ValueError occurred: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during prediction: {e}")


@router.get("/domestic/intraday")
async def get_domestic_intraday_data(
    code: str = Query(..., description="Stock code to get intraday data for (e.g., '005930')"),
    date: str = Query(..., description="Date for intraday data (YYYYMMDD format, e.g., '20250819')")
):
    """
    Get intraday (minute-by-minute) stock data for a given stock code and date.
    """
    intraday_data = get_intraday_data(code, date)
    
    if isinstance(intraday_data, dict) and "error" in intraday_data:
        raise HTTPException(status_code=500, detail=intraday_data["error"])
    
    if not intraday_data:
        raise HTTPException(status_code=404, detail=f"No intraday data found for {code} on {date}.")
        
    return {"intraday_data": intraday_data}

