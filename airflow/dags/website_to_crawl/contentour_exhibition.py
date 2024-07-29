from datetime import datetime

import pandas as pd
import pendulum
import requests
from airflow.decorators import dag, task
from bs4 import BeautifulSoup


@dag(
    schedule_interval=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["example"],
)
def contentour_exhibition_etl():

    @task()
    def extract_contentour_exhibition_urls():
        CONTENTOUR_COMPREHENSIVE_EXHIBITION_URL = 'https://contentour.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ec%a0%95%eb%b3%b4/%ed%95%b4%ec%99%b8%ec%a0%84%ec%8b%9c%ed%9a%8c/?mod=list&pageid=1&category5=&category1=%EA%B5%AD%EA%B0%80%EC%A2%85%ED%95%A9%EC%A0%84%EC%8B%9C%ED%9A%8C&category2=%EC%9D%B8%EB%8F%84&category3=&category4='
        CONTENTOUR_FOOD_URL = 'https://contentour.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ec%a0%95%eb%b3%b4/%ed%95%b4%ec%99%b8%ec%a0%84%ec%8b%9c%ed%9a%8c/?mod=list&pageid=1&category5=&category1=%EC%8B%9D%ED%92%88%2F%EC%9D%8C%EB%A3%8C%2F%ED%98%B8%ED%85%94%2F%ED%94%84%EB%A0%8C%EC%B0%A8%EC%9D%B4%EC%A6%88&category2=%EC%9D%B8%EB%8F%84&category3=&category4='
        PET_URL = 'https://contentour.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ec%a0%95%eb%b3%b4/%ed%95%b4%ec%99%b8%ec%a0%84%ec%8b%9c%ed%9a%8c/?mod=list&pageid=1&category5=&category1=%EB%8F%99%EB%AC%BC%2F%EC%95%A0%EC%99%84%EC%9A%A9%ED%92%88&category2=%EC%9D%B8%EB%8F%84&category3=&category4='

        URLS = [CONTENTOUR_COMPREHENSIVE_EXHIBITION_URL, CONTENTOUR_FOOD_URL, PET_URL]
        urls = []
        for URL in URLS:
            response = requests.get(URL)
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('tbody')
            links = table.find_all('a', href=True)
            for link in links:
                url = 'https://contentour.co.kr' + link['href']
                urls.append(url)
        return urls

    @task()
    def transform_contentour_exhibition_data(urls: list):
        contentour_exhibitions = []

        for url in urls:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            title = soup.find_all('h1')[1].text
            overview1 = soup.find_all('p')[1].text
            overview2 = soup.find_all('p')[2].text
            exhibition = {'title': title, 'overview': overview1 + ' ' + overview2}
            exhibition['url'] = url
            exhibition['crawling_date'] = datetime.today().strftime('%Y-%m-%d')

            columns = ['시작일', '종료일', '국가', '분야/분류', '참가기업 수', '총 방문자 수', '전시장', '전시회 홈페이지']
            info1 = '\n'.join(soup.find_all('div', class_='kboard-aside')[0].text.replace('\n\n', '').split('\n')[:7])
            info2 = '전시회 홈페이지 ' + soup.find_all('div', class_='kboard-aside')[0].find_all('a')[0]['href']
            informations = info1 + '\n' + info2

            for index in range(len(informations.split('\n'))):
                exhibition[columns[index]] = informations.split('\n')[index].split(columns[index])[-1].strip()

            contentour_exhibitions.append(exhibition)
        return contentour_exhibitions

    @task()
    def load_contentour_exhibition_data(data, output_path):
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)

    output_path = '/opt/airflow/dags/crawling_output/contentour_exhibitions.csv'
    urls = extract_contentour_exhibition_urls()
    contentour_exhibitions = transform_contentour_exhibition_data(urls)
    load_contentour_exhibition_data(contentour_exhibitions, output_path)


contentour_exhibition_etl()
