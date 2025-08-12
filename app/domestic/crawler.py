
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def get_stock_name(code: str) -> str:
    """
    네이버 금융에서 종목 코드로 종목 이름을 가져옵니다.
    """
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
    """
    네이버 금융에서 일별 시세 데이터를 크롤링합니다. (단일 페이지)
    """
    url = f"https://finance.naver.com/item/sise_day.nhn?code={code}&page={page}"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        table = soup.find('table', class_='type2')
        if table is None:
            return None # 데이터가 없는 페이지는 None 반환

        df = pd.read_html(str(table), header=0)[0]
        df = df.dropna()

        if df.empty:
            return None

        df = df.rename(columns={
            '날짜': 'date',
            '종가': 'closing_price',
            '전일비': 'change',
            '시가': 'opening_price',
            '고가': 'high_price',
            '저가': 'low_price',
            '거래량': 'volume'
        })

        return df.to_dict(orient='records')

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

def get_historical_data(code: str, years: int = 1):
    """
    지정된 기간(년)만큼의 일별 시세 데이터를 크롤링합니다.

    Args:
        code: 종목 코드
        years: 가져올 데이터 기간 (년 단위)

    Returns:
        지정된 기간의 일별 시세 데이터 리스트
    """
    all_data = []
    # 1년 거래일은 약 250일, 1페이지에 10일치 데이터 -> 1년당 약 26페이지 크롤링
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
    네이버 금융에서 최신 종목 뉴스를 크롤링합니다.

    Args:
        code: 종목 코드
        limit: 가져올 뉴스 기사 수

    Returns:
        최신 뉴스 리스트
    """
    news_list = []
    try:
        url = f"https://finance.naver.com/item/news.naver?code={code}"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(response.text) # HTML 내용 전체를 출력하여 구조 확인
        soup = BeautifulSoup(response.text, 'lxml')

        # 뉴스 테이블의 각 행(tr)을 순회합니다.
        news_table = soup.find('table', class_='type5')
        if not news_table:
            return []

        for row in news_table.find_all('tr')[:limit]:
            title_tag = row.find('a', class_='title')
            info_tag = row.find('td', class_='info')
            date_tag = row.find('td', class_='date')

            if title_tag and info_tag and date_tag:
                title = title_tag.text.strip()
                link = "https://finance.naver.com" + title_tag['href']
                source = info_tag.text.strip()
                date = date_tag.text.strip()

                news_list.append({
                    "title": title,
                    "link": link,
                    "source": source,
                    "date": date
                })
        return news_list
    except Exception as e:
        print(f"Error crawling news: {e}")
        return []


if __name__ == '__main__':
    # 삼성전자(005930) 1년치 데이터 크롤링 테스트
    samsung_yearly_data = get_historical_data('005930')
    print(f"총 {len(samsung_yearly_data)}일치 데이터를 가져왔습니다.")
    print(samsung_yearly_data[:5]) # 처음 5개 데이터 출력
