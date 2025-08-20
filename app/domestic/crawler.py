import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import datetime # Added for date filtering
from pykrx import stock # Added for intraday data

def get_stock_name(code: str) -> str:
    # ... (This function remains unchanged) ...
    try:
        url = f"https://finance.naver.com/item/main.nhn?code={code}"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        company_wrap = soup.find('div', class_='wrap_company')
        if company_wrap:
            name_tag = company_wrap.find('a')
            if name_tag:
                return name_tag.text
        return "알 수 없는 종목"
    except Exception:
        return "알 수 없는 종목"

def get_historical_data(code: str, years: int = 1):
    """
    pykrx를 사용하여 특정 종목의 과거 시세 데이터를 가져옵니다.
    네이버 금융 페이징 방식 대신 날짜 범위 지정 방식으로 변경하여 정확성을 높입니다.
    """
    try:
        today = datetime.datetime.now()
        start_date = today - datetime.timedelta(days=years * 365)
        
        # pykrx는 YYYYMMDD 형식의 날짜를 사용합니다.
        today_str = today.strftime('%Y%m%d')
        start_date_str = start_date.strftime('%Y%m%d')

        print(f"DEBUG: Fetching historical data for {code} from {start_date_str} to {today_str} using pykrx.")
        
        df = stock.get_market_ohlcv(start_date_str, today_str, code)
        
        if df.empty:
            print(f"DEBUG: No historical data found for {code} in the given range.")
            return []

        # 데이터프레임을 기존 형식(list of dicts)으로 변환
        df = df.reset_index() # '날짜' 컬럼을 인덱스에서 컬럼으로 변환
        df = df.rename(columns={
            '날짜': 'date', '종가': 'closing_price', '시가': 'opening_price',
            '고가': 'high_price', '저가': 'low_price', '거래량': 'volume', '등락률': 'change'
        })
        # 날짜 형식을 'YYYY.MM.DD'로 변경
        df['date'] = df['date'].dt.strftime('%Y.%m.%d')
        
        # '전일비' 컬럼은 predictor에서 사용하지 않으므로 'change' 컬럼(등락률)을 그대로 둠
        
        # 필요한 컬럼만 선택
        df = df[['date', 'closing_price', 'change', 'opening_price', 'high_price', 'low_price', 'volume']]

        print(f"DEBUG: Successfully fetched {len(df)} records using pykrx.")
        # 데이터를 역순으로 정렬 (최신 날짜가 위로 오도록)
        return df.sort_values(by='date', ascending=True).to_dict(orient='records')

    except Exception as e:
        print(f"DEBUG: An error occurred in get_historical_data with pykrx: {e}")
        return {"error": f"An unexpected error occurred with pykrx: {e}"}

def get_stock_news(code: str, limit: int = 5):
    """
    네이버 금융에서 최신 종목 뉴스를 크롤링합니다. (Selenium과 Iframe 핸들링 사용)
    이제 기사 본문도 함께 수집합니다.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        url = f"https://finance.naver.com/item/news.naver?code={code}"
        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "news_frame"))
        )

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'type5'))
        )

        soup = BeautifulSoup(driver.page_source, 'lxml')
        news_table = soup.find('table', class_='type5')
        
        if not news_table:
            return {"error": "Switched to iframe, but still could not find the news table."}

        news_list = []
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}

        for row in news_table.find_all('tr'):
            if len(news_list) >= limit:
                break
            
            title_tag = row.find('a', class_='tit')
            info_tag = row.find('td', class_='info')
            date_tag = row.find('td', class_='date')

            if title_tag and info_tag and date_tag:
                title = title_tag.text.strip()
                if not title:
                    continue
                
                link = title_tag['href']
                if not link.startswith('http'):
                    link = "https://finance.naver.com" + link
                
                source = info_tag.text.strip()
                date = date_tag.text.strip()
                
                # --- 기사 본문 수집 로직 추가 ---
                content = "본문 수집에 실패했습니다."
                try:
                    article_response = requests.get(link, headers=headers, timeout=5)
                    article_response.raise_for_status()
                    article_soup = BeautifulSoup(article_response.text, 'lxml')
                    
                    # 네이버 금융 뉴스 본문 선택자 (실제 구조에 따라 변경될 수 있음)
                    content_tag = article_soup.find('div', id='newsct_article')
                    if content_tag:
                        content = content_tag.get_text(strip=True, separator='\n')
                    else:
                        # 다른 가능한 선택자 시도
                        content_tag = article_soup.find('div', id='articeBody')
                        if content_tag:
                            content = content_tag.get_text(strip=True, separator='\n')

                except Exception as e:
                    content = f"본문 수집 중 오류 발생: {e}"
                # ---------------------------------

                news_list.append({"title": title, "link": link, "source": source, "date": date, "content": content})
        
        if not news_list:
            return {"error": "News table was found, but no articles could be parsed."}
        
        return news_list

    except TimeoutException:
        return {"error": "A component (iframe 'news_frame' or table 'type5') was not found in time."}
    except Exception as e:
        return {"error": f"An unexpected error occurred with Selenium: {e}"}
    finally:
        if driver:
            driver.quit()

def get_intraday_data(code: str, date_str: str):
    """
    특정 종목의 특정 날짜 분봉 데이터를 가져옵니다.
    Args:
        code: 종목 코드 (예: '005930')
        date_str: 날짜 문자열 (YYYYMMDD 형식)
    Returns:
        분봉 데이터 리스트 (시간, 시가, 고가, 저가, 종가, 거래량)
    """
    try:
        print(f"DEBUG: get_intraday_data called for code: {code}, date: {date_str}")
        # pykrx는 'YYYYMMDD' 형식의 날짜를 받음
        try:
            print(f"DEBUG: Calling pykrx.stock.get_market_ohlcv with date_str: {date_str}, code: {code}")
            # df = stock.get_market_ohlcv(date_str, date_str, code, interval="1m")
            # df = stock.get_market_ohlcv(date_str, date_str, code)
            # df = stock.get_market_ohlcv_by_time(
            #     date_str,
            #     date_str,
            #     code,
            #     interval="1m"  # 1분봉
            # )
            df = stock.get_market_ohlcv(date_str, date_str, code, "m")
            print(df)
            print(f"DEBUG: pykrx call returned. df.empty: {df.empty}, df.shape: {df.shape if not df.empty else 'N/A'}")
        except Exception as e:
            print(f"DEBUG: pykrx call failed: {e}")
            return {"error": f"Failed to fetch data: {e}"}
        
        if df.empty:
            print(f"DEBUG: DataFrame is empty for code: {code}, date: {date_str}")
            return []

        # 인덱스(시간)를 문자열로 변환하고 필요한 컬럼만 선택
        df['time'] = df.index.strftime('%H:%M')
        df = df.rename(columns={
            '시가': 'opening_price', '고가': 'high_price', '저가': 'low_price',
            '종가': 'closing_price', '거래량': 'volume'
        })
        
        # 필요한 컬럼만 선택하여 리스트로 반환
        result = df[['time', 'opening_price', 'high_price', 'low_price', 'closing_price', 'volume']].to_dict(orient='records')
        print(f"DEBUG: Successfully processed {len(result)} intraday records.")
        return result
    except Exception as e:
        print(f"DEBUG: Error in get_intraday_data: {e}") # ADDED FOR DEBUGGING
        return {"error": f"Failed to fetch intraday data: {e}"}
