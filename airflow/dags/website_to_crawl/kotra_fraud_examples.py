import os
import ssl
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter

# 환경 변수 로드
load_dotenv()
API_KEY = os.getenv('API_KEY')


# 오늘 날짜를 'YYYYMMDD' 형식으로 문자열로 저장
today = datetime.today().strftime('%Y%m%d')

# 저장할 디렉토리 생성
save_dir = "/opt/airflow/dags/pdf_datafiles"
os.makedirs(save_dir, exist_ok=True)


# JSON 데이터를 DataFrame으로 변환하는 함수 정의
def tranform_to_df(data, params):
    rows = []
    for i in range(len(data['response']['body']['itemList']['item'])):
        news = data['response']['body']['itemList']['item'][i]

        content = news['bdtCntnt']
        title = news["titl"]
        fraud_type = news['fraudType']
        ovro = news['ovrofInfo']
        date = news['othbcDt']

        soup = BeautifulSoup(content, 'html.parser')
        cleaned_text = soup.get_text()

        row = {
            'title': title,
            'type': fraud_type,
            'ovro': ovro,
            'date': date,
            'content': cleaned_text
        }

        rows.append(row)

    df = pd.DataFrame(rows)
    return df


# SSL 설정 클래스 정의
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.set_ciphers('DEFAULT:!DH')
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)


# 세션 생성
session = requests.Session()
session.mount('https://', SSLAdapter())

# API URL 설정
url = "http://apis.data.go.kr/B410001/cmmrcFraudCase/cmmrcFraudCase"

count = 0
while True:
    count += 1
    params = {
        "serviceKey": API_KEY,
        "type": "json",
        "numOfRows": "100",
        "pageNo": f"{count}",
        "search1": "인도",
        "search4": "20210711",
        "search7": "20240711"
    }

    response = session.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        df = tranform_to_df(data, params)

        df.to_csv(f"/opt/airflow/dags/pdf_datafiles/Fraud_trade_{count}th.csv", index=False)
        if len(df) < 50:
            break
        print(f"{count}th trial saved")
    else:
        print(f"Error: {response.status_code}, Response: {response.text}")
        break
