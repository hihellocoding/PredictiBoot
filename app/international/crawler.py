import yfinance as yf
import pandas as pd

def get_historical_data_international(ticker: str, period: str = "1y"):
    """
    Yahoo Finance에서 외국 주식의 과거 데이터를 가져옵니다.

    Args:
        ticker (str): 주식 티커 (예: 'AAPL', 'MSFT')
        period (str): 데이터 기간 (예: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')

    Returns:
        list: 과거 데이터 리스트 (딕셔너리 형태) 또는 에러 딕셔너리
    """
    try:
        # yfinance를 사용하여 데이터 다운로드
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            return {"error": f"No data found for ticker: {ticker} with period: {period}"}

        # 필요한 컬럼만 선택하고 이름 변경
        hist = hist.reset_index()
        hist.columns = hist.columns.str.lower() # 컬럼명을 소문자로 변경
        
        # 필요한 컬럼만 선택
        df = hist[['date', 'open', 'high', 'low', 'close', 'volume']]
        
        # 날짜 형식을 YYYY-MM-DD로 통일
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')

        return df.to_dict(orient='records')

    except Exception as e:
        return {"error": f"Failed to fetch data for {ticker}: {e}"}
