import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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

def get_daily_stock_data(code: str, page: int = 1):
    # ... (This function remains unchanged) ...
    url = f"https://finance.naver.com/item/sise_day.nhn?code={code}&page={page}"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        table = soup.find('table', class_='type2')
        if table is None:
            return None
        df = pd.read_html(str(table), header=0)[0]
        df = df.dropna()
        if df.empty:
            return None
        df = df.rename(columns={
            '날짜': 'date', '종가': 'closing_price', '전일비': 'change',
            '시가': 'opening_price', '고가': 'high_price', '저가': 'low_price', '거래량': 'volume'
        })
        return df.to_dict(orient='records')
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

def get_historical_data(code: str, years: int = 1):
    # ... (This function remains unchanged) ...
    all_data = []
    pages_to_crawl = years * 26
    for page in range(1, pages_to_crawl + 1):
        daily_data = get_daily_stock_data(code, page)
        if daily_data is None:
            break
        if isinstance(daily_data, dict) and "error" in daily_data:
            return daily_data
        all_data.extend(daily_data)
        time.sleep(0.1)
    return all_data

def get_stock_news(code: str, limit: int = 5):
    """
    네이버 금융에서 최신 종목 뉴스를 크롤링합니다. (Selenium과 Iframe 핸들링 사용)
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

        # CORRECTED: Wait for the iframe with ID 'news_frame' and switch to it.
        WebDriverWait(driver, 15).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "news_frame"))
        )

        # Now that we are in the frame, wait for the table to be present.
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'type5'))
        )

        soup = BeautifulSoup(driver.page_source, 'lxml')
        news_table = soup.find('table', class_='type5')
        
        if not news_table:
            return {"error": "Switched to iframe, but still could not find the news table."}

        news_list = []
        for row in news_table.find_all('tr'):
            if len(news_list) >= limit:
                break
            
            title_tag = row.find('a', class_='tit')
            info_tag = row.find('td', class_='info')
            date_tag = row.find('td', class_='date')

            if title_tag and info_tag and date_tag:
                title = title_tag.text.strip()
                if not title: # Skip empty titles that sometimes appear
                    continue
                
                link = title_tag['href']
                if not link.startswith('http'):
                    link = "https://finance.naver.com" + link
                
                source = info_tag.text.strip()
                date = date_tag.text.strip()
                news_list.append({"title": title, "link": link, "source": source, "date": date})
        
        if not news_list:
            return {"error": "News table was found, but no articles could be parsed."}
        print(news_list)
        return news_list

    except TimeoutException:
        return {"error": "A component (iframe 'news_frame' or table 'type5') was not found in time."}
    except Exception as e:
        return {"error": f"An unexpected error occurred with Selenium: {e}"}
    finally:
        if driver:
            driver.quit()