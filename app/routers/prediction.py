from fastapi import APIRouter, Query, HTTPException
from ..domestic.crawler import get_daily_stock_data, get_historical_data, get_stock_name, get_stock_news
from ..domestic.predictor import predict_next_day_price
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
    news = get_stock_news(code, limit)
    # 뉴스가 없더라도 에러를 발생시키지 않고, 빈 리스트를 포함한 정상 응답을 반환합니다.
    return {"news": news}

@router.get("/domestic/predict", response_model=dict)
async def predict_domestic_stock(
    code: str = Query(..., description="Stock code to predict (e.g., '005930')"),
    years: int = Query(1, description="Number of years of historical data to use (1, 2, or 3)")
):
    if years not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Years must be 1, 2, or 3.")

    # 1. Crawl historical data and get stock name
    historical_data = get_historical_data(code, years)
    stock_name = get_stock_name(code)

    if not isinstance(historical_data, list) or not historical_data:
        raise HTTPException(status_code=404, detail="Could not retrieve historical data.")

    try:
        # 2. Predict the next day's price
        predicted_price = predict_next_day_price(historical_data)

        # 3. Determine the correct prediction date based on KST
        kst = pytz.timezone('Asia/Seoul')
        now_kst = datetime.datetime.now(kst)

        last_crawled_date_str = historical_data[0]['date']
        last_crawled_date = datetime.datetime.strptime(last_crawled_date_str, '%Y.%m.%d')

        prediction_target_date = last_crawled_date
        # Check if the latest data is from today and market is not closed yet
        if last_crawled_date.date() == now_kst.date() and now_kst.hour < 16:
            # Predict for today, as today's data is not final
            prediction_target_date = last_crawled_date
        else:
            # Predict for the next day, as today's data is final or latest data is from yesterday
            prediction_target_date = last_crawled_date + datetime.timedelta(days=1)

        # Find the next business day (handles weekends)
        while prediction_target_date.weekday() >= 5: # 5: Saturday, 6: Sunday
            prediction_target_date += datetime.timedelta(days=1)
        
        # 4. Format the response
        formatted_date = f"{prediction_target_date.month}월 {prediction_target_date.day}일"
        formatted_price = f"{locale.format_string('%d', int(predicted_price), grouping=True)}원"

        prediction_message = f"{stock_name}({code})의 {formatted_date} 예상 종가는 {formatted_price} 입니다."

        return {"prediction_message": prediction_message}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during prediction: {e}")

