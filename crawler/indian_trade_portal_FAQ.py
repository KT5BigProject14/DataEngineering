import re
import logging
from datetime import datetime

import requests
import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class IndianTradePortalFAQCrawler:
    def __init__(self, urls, output_path):
        self.urls = urls
        self.output_path = output_path
        self.questions = []
        self.answers = []
        self.topics = []
        self.page_urls = []
        self.crawling_dates = []
        self.pattern = r'\?([A-Z])'

    def fetch_page(self, url):
        logging.info(f"Fetching data from {url}")
        response = requests.get(url)
        if response.status_code == 200:
            logging.info("Page fetched successfully.")
            return response.text
        else:
            logging.error(f"Failed to fetch the page. Status code: {response.status_code}")
            return None

    def parse_page(self, html_content):
        logging.info("Parsing the page content.")
        soup = BeautifulSoup(html_content, 'html.parser')
        topic = soup.select_one('#inner-left-side > div > div:nth-child(2) > p > font > strong > span').text
        data = soup.select('#accordion')
        if data:
            data = data[0].text.replace('\xa0', '').replace('Question:', '\nQuestion:').replace('“', '').replace('”', '').replace("'", '').replace('Answer: ', '?').replace('Answer:', '?').replace('??', '?').replace('RatesThe', 'Rates?The').replace('cost.The', 'cost?The').replace('exporters.The', 'exporters?The').strip()
            results = re.sub(self.pattern, self.replace_match, data).split('\n')
            results = [result for result in results if result != '']
            logging.info("Page content parsed successfully.")
            return topic, results
        else:
            logging.warning("No data found in the page content.")
            return topic, []

    def replace_match(self, match):
        if match.group(1).isupper():
            return f"?\n{match.group(1)}"
        return match.group(0)

    def process_results(self, url, topic, results):
        logging.info("Processing results.")
        questions = []
        answers = []

        for index in range(len(results)):
            if index % 2 == 0:
                questions.append(results[index])
            else:
                answers.append(results[index])

        topics = [topic] * (len(results) // 2)
        page_urls = [url] * (len(results) // 2)
        crawling_dates = [datetime.today().strftime('%Y-%m-%d')] * (len(results) // 2)
        
        logging.info("Results processed successfully.")
        return questions, answers, topics, page_urls, crawling_dates

    def gather_all_data(self):
        logging.info("Gathering all data from provided URLs.")
        for url in self.urls:
            html_content = self.fetch_page(url)
            if html_content:
                topic, results = self.parse_page(html_content)
                if results:
                    question, answer, topic, page_url, crawling_date = self.process_results(url, topic, results)
                    self.questions += question
                    self.answers += answer
                    self.topics += topic
                    self.page_urls += page_url
                    self.crawling_dates += crawling_date
        logging.info("All data gathered successfully.")

    def save_to_csv(self):
        logging.info("Saving data to CSV.")
        df = pd.DataFrame({
            'question': self.questions,
            'answer': self.answers,
            'topic': self.topics,
            'url': self.page_urls,
            'crawling_date': self.crawling_dates,
        })
        df.to_csv(self.output_path, index=False)
        logging.info(f"Data saved to CSV at {self.output_path}")

    def run(self):
        logging.info("Starting the crawling process.")
        self.gather_all_data()
        self.save_to_csv()
        logging.info("Crawling process completed successfully.")


# 사용 예시
INDIAN_TRADE_PORTAL_FAQ_URLS = [
    'https://www.indiantradeportal.in/vs.jsp?lang=0&id=0,55,276',
    'https://www.indiantradeportal.in/vs.jsp?lang=0&id=0,55,287',
    'https://www.indiantradeportal.in/vs.jsp?lang=0&id=0,55,280',
    'https://www.indiantradeportal.in/vs.jsp?lang=0&id=0,55,15502',
    'https://www.indiantradeportal.in/vs.jsp?lang=0&id=0,55,284',
    'https://www.indiantradeportal.in/vs.jsp?lang=0&id=0,55,286',
    'https://www.indiantradeportal.in/vs.jsp?lang=0&id=0,55,283',
    'https://www.indiantradeportal.in/vs.jsp?lang=0&id=0,55,15627',
    'https://www.indiantradeportal.in/vs.jsp?lang=0&id=0,55,15535',
    'https://www.indiantradeportal.in/vs.jsp?lang=0&id=0,55,288',
    'https://www.indiantradeportal.in/vs.jsp?lang=0&id=0,55,15549',
    'https://www.indiantradeportal.in/vs.jsp?lang=0&id=0,55,23222',
]
OUTPUT_PATH = 'indian_trade_portal_faq.csv'

crawler = IndianTradePortalFAQCrawler(urls=INDIAN_TRADE_PORTAL_FAQ_URLS, output_path=OUTPUT_PATH)
crawler.run()
