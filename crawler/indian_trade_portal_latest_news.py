import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class IndianTradePortalLatestNewsCrawler:
    def __init__(self, url, output_path):
        self.url = url
        self.output_path = output_path
        self.titles = []
        self.urls = []
        self.article_published_dates = []

    def fetch_page(self):
        logging.info("Fetching the page content.")
        response = requests.get(self.url)
        if response.status_code == 200:
            logging.info("Page fetched successfully.")
            return response.text
        else:
            logging.error("Failed to fetch the page. Status code: %d", response.status_code)
            return None

    def parse_page(self, html_content):
        logging.info("Parsing the page content.")
        soup = BeautifulSoup(html_content, 'html.parser')
        rows = soup.find_all('tr', class_='rowHover')

        self.titles = [row.find('a').text for row in rows]
        self.urls = [row.find('a')['href'] for row in rows]
        self.article_published_dates = [row.find_all('td')[2].find('a').text for row in rows]
        logging.info("Page content parsed successfully.")

    def save_to_csv(self):
        logging.info("Saving data to CSV.")
        df = pd.DataFrame({
                'title': self.titles,
                'url': self.urls,
                'article_published_date': pd.to_datetime(self.article_published_dates),
        })
        df.to_csv(self.output_path, index=False)
        logging.info("Data saved to CSV at %s.", self.output_path)

    def run(self):
        html_content = self.fetch_page()
        if html_content:
            self.parse_page(html_content)
            self.save_to_csv()
        else:
            logging.error("No content to parse.")


# 사용 예시
INDIAN_TRADE_PORTAL_LATEST_NEWS_URL = 'https://www.indiantradeportal.in/news.jsp?lang=0'
OUTPUT_PATH = 'india_trade_portal_latest_news.csv'

crawler = IndianTradePortalLatestNewsCrawler(url=INDIAN_TRADE_PORTAL_LATEST_NEWS_URL, output_path=OUTPUT_PATH)
crawler.run()
