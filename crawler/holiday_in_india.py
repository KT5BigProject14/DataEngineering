import re
import time
from datetime import datetime
import calendar
import requests
import pandas as pd
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class IndiaHolidayCrawler:
    def __init__(self, output_path):
        self.output_path = output_path
        self.current_year = datetime.now().year
        self.months = []
        self.days = []
        self.holidays = []
        self.urls = []
        self.descriptions = []
        self.dates = []

    def get_days_in_month(self, year):
        logging.info(f"Getting days in each month for year {year}")
        days_in_month = {}
        for month in range(1, 13):
            days_in_month[month] = calendar.monthrange(year, month)[1]
        return days_in_month

    def fetch_page(self, url):
        logging.info(f"Fetching page: {url}")
        response = requests.get(url)
        return response.content

    def parse_holidays(self, contents, month, days_in_month):
        logging.info(f"Parsing holidays for month: {month}")
        soup = BeautifulSoup(contents, 'html.parser')

        for day in range(1, days_in_month + 1):
            day_str = str(day).zfill(2)
            holiday_element = soup.find('td', id=f'calendar-{self.current_year}-{month}-{day_str}-0')
            if holiday_element:
                holiday = holiday_element.text.replace('\n  \n\xa0\n\n\n\n\n\n\xa0\n\n ', ' & ').strip()
                if holiday:
                    self.holidays.append(f'[holiday] {self.current_year}-{month}-{day_str} : {holiday}')
                    self.urls.append(f'https://www.india.gov.in/calendar?date={self.current_year}-{month}')
                    self.dates.append(datetime.today().strftime('%Y-%m-%d'))

                    description = soup.select_one('#block-system-main > div > div.view-header > p:nth-child(3)').text.replace('( \xa0\xa0\xa0 )', '').replace('. C', '.\nC').strip()
                    specific_calendar_url = soup.select_one('#block-system-main > div > div.view-header > p:nth-child(3) > a')['href']
                    self.descriptions.append(f'{description}\n{specific_calendar_url}')

    def save_to_csv(self):
        logging.info("Creating dataset.")
        df = pd.DataFrame({
            'holiday': self.holidays,
            'url': self.urls,
            'description': self.descriptions,
            'date': self.dates,
        })
        df.to_csv(self.output_path, index=False)
        logging.info(f"Dataset saved to {self.output_path}")

    def run(self):
        logging.info("Starting crawler.")
        days_in_current_year = self.get_days_in_month(self.current_year)

        for month, days in days_in_current_year.items():
            month_str = str(month).zfill(2)
            url = f'https://www.india.gov.in/calendar?date={self.current_year}-{month_str}'
            contents = self.fetch_page(url)
            self.parse_holidays(contents, month_str, days)

        self.save_to_csv()
        logging.info("Crawler finished.")


# 사용 예시
OUTPUT_PATH = 'india_holiday.csv'
crawler = IndiaHolidayCrawler(output_path=OUTPUT_PATH)
crawler.run()
