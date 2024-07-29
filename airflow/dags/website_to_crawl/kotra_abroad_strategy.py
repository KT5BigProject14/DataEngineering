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


def tranform_to_df(data, params):
    rows = []
    for i in range(len(data['response']['body']['itemList']['item'])):
        # Assuming r contains the HTML content
        news = data['response']['body']['itemList']['item'][i]

        content = news['bdtCntnt']
        title = news["titl"]
        type = news['fraudType']
        ovro = news['ovrofInfo']
        date = news['othbcDt']

        soup = BeautifulSoup(content, 'html.parser')
        cleaned_text = soup.get_text()

        row = {
            'title': title,
            'type': type,
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

url = "https://apis.data.go.kr/B410001/entryStrategy/entryStrategy"

# 오늘 날짜를 'YYYYMMDD' 형식으로 문자열로 저장
today = datetime.today().strftime('%Y%m%d')

# 오늘 날짜를 datetime 객체로 변환
today_date = datetime.strptime(today, '%Y%m%d')

# start_date를 오늘 날짜 기준으로 7일 전으로 설정
start_date = today_date - timedelta(days=7)

# end_date를 오늘 날짜로 설정
end_date = today_date

# 저장할 디렉토리 생성
save_dir = "/opt/airflow/dags/pdf_datafiles"
os.makedirs(save_dir, exist_ok=True)

while today_date <= end_date:
    params = {
        "serviceKey": API_KEY,
        "type": "json",
        "numOfRows": "100",
        "pageNo": "1",
        "search1": "인도",
        "search2": f"{today_date.strftime('%Y%m%d')}"
    }

    today_date += timedelta(days=1)
    
    response = session.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        items = data.get('response', {}).get('body', {}).get('itemList', {}).get('item', [])

        for item in items:
            realAtfileInfoList = item.get('realAtfileInfoList', {}).get('realAtfileInfo', [])
            for file_info in realAtfileInfoList:
                file_url = file_info['realAtfileUrl']
                file_name = file_info['realAtfileName']
                file_response = session.get(file_url)
                
                if file_response.status_code == 200:
                    file_path = os.path.join(save_dir, file_name)
                    with open(file_path, 'wb') as file:
                        file.write(file_response.content)
                    print(f"Downloaded and saved {file_name} to {file_path}")
                else:
                    print(f"Failed to download {file_name} from {file_url}")
    else:
        print(f"Error: {response.status_code}, Response: {response.text}")
        break
