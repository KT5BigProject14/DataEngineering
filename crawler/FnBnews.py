import time
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class FnBNewsCrawler:
    def __init__(self, url, output_path, max_count=100):
        self.url = url
        self.output_path = output_path
        self.max_count = max_count
        self.driver = None
        self.titles = []
        self.page_contents = []
        self.article_published_dates = []
        self.authors = []
        self.urls = []

    def start_driver(self):
        logging.info("Starting WebDriver.")
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.url)
        time.sleep(3)
        logging.info("WebDriver started and navigated to the URL.")

    def scrape_page(self):
        logging.info("Scraping page.")
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        tables = soup.find_all('div', id='ContentPlaceHolder1_UpdatePanel1')

        for rows in tables:
            rows = rows.find_all('a')
            for row in rows:
                if 'Top-News' in row['href']:
                    self.urls.append('https://www.fnbnews.com' + row['href'])

        for news_index in range(5):
            contents = soup.find_all('tr', id=f'ContentPlaceHolder1_lvPosts_Tr1_{news_index}')[0].text.replace('\n\n\n\n', '').strip().split('\n\n')

            for index, content in enumerate(contents):
                if index == 0:
                    self.titles.append(content.replace('\r\n', '')[1:].strip())
                elif index == 1:
                    self.article_published_dates.append(content.replace('\r\n', '').strip())
                elif index == 2:
                    self.authors.append(content.replace('\r\n', '').strip())
                else:
                    pass
        logging.info("Page scraping completed.")
  
    def click_next(self):
        logging.info("Clicking next button.")
        wait = WebDriverWait(self.driver, 10)
        next_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ContentPlaceHolder1_btnNext"]')))
        next_button.click()
        time.sleep(5)
        logging.info("Navigated to next page.")

    def fetch_page_contents(self):
        logging.info("Fetching page contents.")
        for url in self.urls:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            self.page_contents.append(soup.find('span', class_='breadcrumb').text)
        logging.info("Fetched all page contents.")

    def save_to_csv(self):
        logging.info("Saving data to CSV.")
        df = pd.DataFrame(
            {
                'title': self.titles,
                'page_content': self.page_contents,
                'article_published_date': self.article_published_dates,
                'author': self.authors,
                'url': self.urls,
            }
        )

        df['article_published_date'] = pd.to_datetime(df['article_published_date'])
        df.to_csv(self.output_path, index=False)
        logging.info("Data saved to CSV at %s.", self.output_path)

    def run(self):
        self.start_driver()
        count = self.max_count

        while count > 0:
            self.scrape_page()
            count -= 5
            if count > 0:
                self.click_next()

        self.fetch_page_contents()
        self.save_to_csv()
        self.driver.quit()
        logging.info("Crawler run completed.")


# 사용 예시
FNBNEWS_URL = 'https://www.fnbnews.com/Top-News'
OUTPUT_PATH = 'india_FnBnews.csv'

crawler = FnBNewsCrawler(url=FNBNEWS_URL, output_path=OUTPUT_PATH)
crawler.run()
