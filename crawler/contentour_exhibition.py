import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ContentourExhibitionCrawler:
    def __init__(self, output_path):
        self.output_path = output_path
        self.urls = []
        self.base_url = 'https://contentour.co.kr'

    def fetch_page(self, url):
        logging.info(f"Fetching page: {url}")
        response = requests.get(url)
        return response.text

    def parse_exhibition_urls(self, html_content):
        logging.info("Parsing exhibition URLs.")
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('tbody')
        links = table.find_all('a', href=True)
        urls = [self.base_url + link['href'] for link in links]
        logging.info(f"Extracted {len(urls)} URLs.")
        return urls

    def extract_exhibition_urls(self):
        logging.info("Extracting exhibition URLs from categories.")
        # 국가종합전시회
        CONTENTOUR_COMPREHENSIVE_EXHIBITION_URL = 'https://contentour.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ec%a0%95%eb%b3%b4/%ed%95%b4%ec%99%b8%ec%a0%84%ec%8b%9c%ed%9a%8c/?mod=list&pageid=1&category5=&category1=%EA%B5%AD%EA%B0%80%EC%A2%85%ED%95%A9%EC%A0%84%EC%8B%9C%ED%9A%8C&category2=%EC%9D%B8%EB%8F%84&category3=&category4='

        # 식품/음료/호텔
        CONTENTOUR_FOOD_URL = 'https://contentour.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ec%a0%95%eb%b3%b4/%ed%95%b4%ec%99%b8%ec%a0%84%ec%8b%9c%ed%9a%8c/?mod=list&pageid=1&category5=&category1=%EC%8B%9D%ED%92%88%2F%EC%9D%8C%EB%A3%8C%2F%ED%98%B8%ED%85%94%2F%ED%94%84%EB%A0%8C%EC%B0%A8%EC%9D%B4%EC%A6%88&category2=%EC%9D%B8%EB%8F%84&category3=&category4='

        # 동물/애완용품
        PET_URL = 'https://contentour.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ec%a0%95%eb%b3%b4/%ed%95%b4%ec%99%b8%ec%a0%84%ec%8b%9c%ed%9a%8c/?mod=list&pageid=1&category5=&category1=%EB%8F%99%EB%AC%BC%2F%EC%95%A0%EC%99%84%EC%9A%A9%ED%92%88&category2=%EC%9D%B8%EB%8F%84&category3=&category4='

        category_urls = [CONTENTOUR_COMPREHENSIVE_EXHIBITION_URL, CONTENTOUR_FOOD_URL, PET_URL]
        
        for category_url in category_urls:
            html_content = self.fetch_page(category_url)
            urls = self.parse_exhibition_urls(html_content)
            self.urls.extend(urls)

    def fetch_exhibition_page(self, url):
        logging.info(f"Fetching exhibition page: {url}")
        response = requests.get(url)
        return response.text

    def parse_exhibition_page(self, html_content):
        logging.info("Parsing exhibition page.")
        soup = BeautifulSoup(html_content, 'html.parser')

        title = soup.find_all('h1')[1].text
        overview1 = soup.find_all('p')[1].text
        overview2 = soup.find_all('p')[2].text
        exhibition = {'title': title, 'overview': overview1 + ' ' + overview2}

        columns = ['시작일', '종료일', '국가', '분야/분류', '참가기업 수', '총 방문자 수', '전시장', '전시회 홈페이지']
        info1 = '\n'.join(soup.find_all('div', class_='kboard-aside')[0].text.replace('\n\n', '').split('\n')[:7])
        info2 = '전시회 홈페이지 ' + soup.find_all('div', class_='kboard-aside')[0].find_all('a')[0]['href']
        informations = info1 + '\n' + info2

        for index in range(len(informations.split('\n'))):
            exhibition[columns[index]] = informations.split('\n')[index].split(columns[index])[-1].strip()

        logging.info(f"Parsed exhibition: {exhibition['title']}")
        return exhibition

    def make_dataset(self):
        logging.info("Creating dataset.")
        contentour_exhibitions = []

        for url in self.urls:
            html_content = self.fetch_exhibition_page(url)
            exhibition = self.parse_exhibition_page(html_content)
            contentour_exhibitions.append(exhibition)

        df = pd.DataFrame(contentour_exhibitions)
        df.to_csv(self.output_path, index=False)
        logging.info(f"Dataset saved to {self.output_path}")

    def run(self):
        logging.info("Starting crawler.")
        self.extract_exhibition_urls()
        self.make_dataset()
        logging.info("Crawler finished.")


# 사용 예시
OUTPUT_PATH = 'contentour_exhibitions.csv'
crawler = ContentourExhibitionCrawler(output_path=OUTPUT_PATH)
crawler.run()
