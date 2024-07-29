import pickle

import pandas as pd
import pendulum
from airflow.decorators import dag, task
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dag(
    schedule_interval=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["news"],
)
def transform_fnbnews_data():

    @task()
    def process_data():
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False
        )

        # CSV 파일 경로 (Airflow 작업 환경에 맞게 조정)
        csv_file_path = '/opt/airflow/dags/crawling_output/fnbnews.csv'

        # CSV 파일 읽기
        df = pd.read_csv(csv_file_path)

        page_no = 0
        metadata = {}
        documents = []

        for index in range(len(df)):
            page_content = f"author: {df['author'][index]}\n{df['page_content'][index]}"

            contents = text_splitter.create_documents([page_content])
            for content in contents:
                metadata = {'source': 'FnBnews', 'page_no': page_no, 'category': '2. 경제 및 시장 분석', 'url': df['url'][index], 'date': df['article_published_date'][index]}
                document = Document(page_content=content.page_content, metadata=metadata)
                documents.append(document)
                page_no += 1

        # 문서 객체를 pickle 파일로 저장
        pickle_file_path = '/opt/airflow/dags/csv_to_pickle/fnbnews.pkl'
        with open(pickle_file_path, 'wb') as file:
            pickle.dump(documents, file)

    process_data()


transform_fnbnews_data()
