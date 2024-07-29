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
def indian_trade_portal_latest_news_etl():

    @task(multiple_outputs=True)
    def extract(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr', class_='rowHover')
        
        descriptions = [row.find('a').text for row in rows]
        urls = [row.find('a')['href'] for row in rows]
        dates = [row.find_all('td')[2].text for row in rows]
        return {'description': descriptions, 'url': urls, 'article_upload_date': dates}

    @task(multiple_outputs=True)
    def transform(extracted_data):
        transformed_data = {
            'description': extracted_data['description'],
            'url': extracted_data['url'],
            'article_upload_date': [pd.to_datetime(date).strftime('%Y-%m-%d') for date in extracted_data['article_upload_date']]
        }
        return transformed_data

    @task()
    def load(data, output_path):
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)

    url = 'https://www.indiantradeportal.in/news.jsp?lang=0'
    output_path = '/opt/airflow/dags/crawling_output/indian_trade_portal_latest_news.csv'

    extracted_data = extract(url)
    transformed_data = transform(extracted_data)
    load(transformed_data, output_path)  # >> process_faq_data()


indian_trade_portal_latest_news_etl()
