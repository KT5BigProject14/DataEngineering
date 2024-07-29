import logging
import re
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
def indian_trade_portal_faq_crawler_etl():
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
    OUTPUT_PATH = '/opt/airflow/dags/crawling_output/indian_trade_portal_faq.csv'
    pattern = r'\?([A-Z])'

    @task
    def fetch_page(url):
        logging.info(f"Fetching data from {url}")
        response = requests.get(url)
        if response.status_code == 200:
            logging.info("Page fetched successfully.")
            return {'url': url, 'content': response.text}
        else:
            logging.error(f"Failed to fetch the page. Status code: {response.status_code}")
            return {'url': url, 'content': None}

    @task
    def parse_page(data):
        url = data['url']
        html_content = data['content']
        logging.info("Parsing the page content.")
        soup = BeautifulSoup(html_content, 'html.parser')
        topic = soup.select_one('#inner-left-side > div > div:nth-child(2) > p > font > strong > span').text
        data = soup.select('#accordion')
        results = []
        if data:
            data = data[0].text.replace('\xa0', '').replace('Question:', '\nQuestion:').replace('“', '').replace('”', '').replace("'", '').replace('Answer: ', '?').replace('Answer:', '?').replace('??', '?').replace('RatesThe', 'Rates?The').replace('cost.The', 'cost?The').replace('exporters.The', 'exporters?The').strip()
            results = re.sub(pattern, lambda match: f"?\n{match.group(1)}" if match.group(1).isupper() else match.group(0), data).split('\n')
            results = [result for result in results if result != '']
            logging.info("Page content parsed successfully.")
        else:
            logging.warning("No data found in the page content.")
        return {'url': url, 'topic': topic, 'results': results}

    @task
    def process_results(data):
        url = data['url']
        topic = data['topic']
        results = data['results']
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
        return {'questions': questions, 'answers': answers, 'topics': topics, 'page_urls': page_urls, 'crawling_dates': crawling_dates}

    @task
    def save_to_csv(all_data, output_path):
        logging.info("Creating dataset.")
        questions = []
        answers = []
        topics = []
        page_urls = []
        crawling_dates = []

        for data in all_data:
            questions.extend(data['questions'])
            answers.extend(data['answers'])
            topics.extend(data['topics'])
            page_urls.extend(data['page_urls'])
            crawling_dates.extend(data['crawling_dates'])

        df = pd.DataFrame({
            'question': questions,
            'answer': answers,
            'topic': topics,
            'url': page_urls,
            'crawling_date': crawling_dates,
        })
        df.to_csv(output_path, index=False)
        logging.info(f"Data saved to CSV at {output_path}")

    fetch_tasks = [fetch_page(url) for url in INDIAN_TRADE_PORTAL_FAQ_URLS]
    parsed_tasks = [parse_page(task) for task in fetch_tasks]
    processed_tasks = [process_results(task) for task in parsed_tasks]
    save_to_csv(processed_tasks, OUTPUT_PATH)


indian_trade_portal_faq_crawler_etl()
