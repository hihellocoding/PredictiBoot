
from pykrx import stock
import pandas as pd

def find_stock_code(query: str) -> list:
    """
    회사 이름으로 종목 코드를 검색합니다.

    Args:
        query: 검색할 회사 이름 (일부만 입력해도 가능)

    Returns:
        검색된 종목 리스트 ([{'code': '005930', 'name': '삼성전자'}, ...])
    """
    try:
        # KOSPI와 KOSDAQ의 모든 종목 티커를 가져옵니다.
        tickers_kospi = stock.get_market_ticker_list(market="KOSPI")
        tickers_kosdaq = stock.get_market_ticker_list(market="KOSDAQ")
        all_tickers = tickers_kospi + tickers_kosdaq

        results = []
        for ticker in all_tickers:
            name = stock.get_market_ticker_name(ticker)
            if query.lower() in name.lower():
                results.append({
                    "code": ticker,
                    "name": name
                })
        
        return results

    except Exception as e:
        print(f"Error finding stock code: {e}")
        return []

if __name__ == '__main__':
    # 검색 기능 테스트
    search_results = find_stock_code('삼성')
    print(search_results)
