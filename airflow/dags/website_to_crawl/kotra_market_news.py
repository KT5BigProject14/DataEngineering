import os
import ssl
from datetime import datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter

load_dotenv()
API_KEY = os.getenv('API_KEY')


today = datetime.today().strftime('%Y%m%d')


save_dir = "/opt/airflow/pdf_datafiles"
os.makedirs(save_dir, exist_ok=True)


def tranform_to_df(data, params):
    rows = []
    for i in range(len(data['response']['body']['itemList']['item'])):
        # Assuming r contains the HTML content
        news = data['response']['body']['itemList']['item'][i]

        content = news['newsBdt']
        title = news["newsTitl"]
        url = news["kotraNewsUrl"]
        summary = news['cntntSumar']
        ovro = news['ovrofInfo']
        date = news['othbcDt']

        soup = BeautifulSoup(content, 'html.parser')
        cleaned_text = soup.get_text()

        row = {
            'title': title,
            'url': url,
            'summary': summary,
            'ovro': ovro,
            'date': date,
            'content': cleaned_text
        }

        rows.append(row)

    df = pd.DataFrame(rows)
    return df


class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.set_ciphers('DEFAULT:!DH')
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)


session = requests.Session()
session.mount('https://', SSLAdapter())

url = "https://apis.data.go.kr/B410001/kotra_overseasMarketNews/ovseaMrktNews/ovseaMrktNews"

today = datetime.today().strftime('%Y%m%d')
today_date = datetime.strptime(today, '%Y%m%d')
start_date = (today_date - timedelta(days=7)).strftime('%Y%m%d')

count = 0
while (True):
    count += 1
    params = {
        "serviceKey": API_KEY,
        "type": "json",
        "numOfRows": "100",
        "pageNo": f"{count}",
        "search1": "인도",
        "search4": start_date,
        "search7": today
    }

    response = session.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        df = tranform_to_df(data, params)

        df.to_csv(f"/opt/airflow/dags/pdf_datafiles/kotra_abroad_news_{count}th.csv")
        if len(df) < 50:
            break
        print(f"{count}th trial saved")
    else:
        print(f"Error: {response.status_code}, Response: {response.text}")
        break
