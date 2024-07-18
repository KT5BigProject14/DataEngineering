import re
import time
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GepExhibitionCrawler:
    def __init__(self, output_path):
        self.output_path = output_path
        self.urls = []
        self.base_url = 'https://www.gep.or.kr/gept/ovrss/exbi/exbiInfo/exbiDetailMain.do?ovrssExbiCd='
        self.driver = None

    def start_driver(self):
        logging.info("Starting WebDriver.")
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        self.driver = webdriver.Chrome(options=options)

    def stop_driver(self):
        if self.driver:
            logging.info("Stopping WebDriver.")
            self.driver.quit()

    def fetch_page(self, url):
        logging.info(f"Fetching page: {url}")
        self.driver.get(url)
        time.sleep(3)

    def parse_page(self):
        logging.info("Parsing main page.")
        wait = WebDriverWait(self.driver, 10)

        # '산업분야 더보기' 버튼 클릭
        more_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="searchForm"]/div/div[2]/div[1]/div[3]/div/div/div/div[2]/button')))
        more_button.click()
        logging.info("'산업분야 더보기' 버튼 클릭.")

        # 새로 열린 창으로 전환
        self.switch_to_new_window()

        # '동물&애완용품', '농수산', '식품&음료' 버튼 클릭
        self.click_buttons(['//*[@id="rowid1"]/div[2]/label', '//*[@id="rowid8"]/div[1]/label', '//*[@id="rowid2"]/div[3]/label'])
        logging.info("'동물&애완용품', '농수산', '식품&음료' 버튼 클릭.")

        # '확인' 버튼 클릭
        confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="frm"]/div/div/div/div[2]/div[2]/a[1]')))
        confirm_button.click()
        logging.info("'확인' 버튼 클릭.")

        time.sleep(3)  # 확인 버튼 클릭 후 창이 닫히는 시간을 확보
        self.driver.switch_to.window(self.driver.window_handles[0])  # 원래 창으로 돌아오기

        # '국가분야 더보기' 버튼 클릭
        more_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="searchForm"]/div/div[2]/div[1]/div[4]/div/div/div/div/div[3]/button')))
        more_button.click()
        logging.info("'국가분야 더보기' 버튼 클릭.")

        # 새로 열린 창으로 전환
        self.switch_to_new_window()

        # '인도' 버튼 클릭
        india_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="rowid46"]/div[3]/label')))
        india_button.click()
        logging.info("'인도' 버튼 클릭.")

        # '확인' 버튼 클릭
        confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="frm"]/div/div/div/div[2]/div[2]/a[1]')))
        confirm_button.click()
        logging.info("'확인' 버튼 클릭.")

        time.sleep(3)  # 확인 버튼 클릭 후 창이 닫히는 시간을 확보
        self.driver.switch_to.window(self.driver.window_handles[0])  # 원래 창으로 돌아오기

        # 검색 버튼 클릭
        search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="searchForm"]/div/div[2]/div[2]/a[2]')))
        search_button.click()
        logging.info("검색 버튼 클릭.")

        time.sleep(3)

        # 전시회 URL 추출
        self.urls = self.extract_urls_from_page()
        logging.info(f"Extracted {len(self.urls)} URLs from the main page.")

    def switch_to_new_window(self):
        logging.info("Switching to new window.")
        all_windows = self.driver.window_handles
        main_window = self.driver.current_window_handle

        for window in all_windows:
            if window != main_window:
                self.driver.switch_to.window(window)
                break

    def click_buttons(self, xpaths):
        wait = WebDriverWait(self.driver, 10)
        for xpath in xpaths:
            button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            button.click()

    def extract_urls_from_page(self):
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        links = soup.find('ul', class_='list-search-card row').find_all('a')

        urls = []
        for link in links:
            onclick_value = link.get('onclick', '')
            match = re.search(r'fnDetail\("([^"]+)"\)', onclick_value)
            if match:
                detail_value = match.group(1)
                urls.append(self.base_url + detail_value)
        return urls

    def fetch_exhibition_page(self, url):
        logging.info(f"Fetching exhibition page: {url}")
        response = requests.get(url)
        return response.text

    def parse_exhibition_page(self, html_content):
        logging.info("Parsing exhibition page.")
        soup = BeautifulSoup(html_content, 'html.parser')
        informations = ['주최기관', '담당자', '전화', '팩스', '이메일', '홈페이지']

        title = ' | '.join(soup.find_all('div', class_='text-info')[0].text.strip().split('\n')[:2])
        overview = soup.find_all('div', class_='ph-wrap')[0].text.replace('\n', '').strip()
        exhibition = {'title': title, 'overview': overview}

        info1 = soup.find_all('div', class_='dotline-items')[0].text.replace('\n\n', '').split('\n')
        info1 = '\n'.join([word.replace('개최규모', '개최규모\n-\n') if word == '개최규모산업분야' else word for word in info1]).split('\n')
        for index in range(1, len(info1), 2):
            exhibition[info1[index - 1]] = info1[index]

        info2 = soup.find_all('div', class_='dotline-items')[1].text.replace('\n\n', '').strip().split('\n')
        if '주최기관' in info2:
            for index in range(1, len(info2), 2):
                exhibition[info2[index - 1]] = info2[index]
        else:
            for index in range(len(informations)):
                exhibition[informations[index]] = '-'

        return exhibition

    def make_dataset(self):
        logging.info("Creating dataset.")
        gep_exhibitions = []

        for url in self.urls:
            html_content = self.fetch_exhibition_page(url)
            exhibition = self.parse_exhibition_page(html_content)
            gep_exhibitions.append(exhibition)
            logging.info(f"Added exhibition: {exhibition['title']}")

        df = pd.DataFrame(gep_exhibitions)
        df.to_csv(self.output_path, index=False)
        logging.info(f"Dataset saved to {self.output_path}")

    def run(self):
        logging.info("Starting crawler.")
        self.start_driver()
        self.fetch_page('https://www.gep.or.kr/gept/ovrss/exbi/exbiInfo/allExbiList.do#')
        self.parse_page()
        self.make_dataset()
        self.stop_driver()
        logging.info("Crawler finished.")


# 사용 예시
OUTPUT_PATH = 'gep_exhibitions.csv'
crawler = GepExhibitionCrawler(output_path=OUTPUT_PATH)
crawler.run()
