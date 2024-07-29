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
    tags=["exhibition"],
)
def transform_contentour_exhibition_data():

    @task()
    def process_data():
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False
        )

        # CSV 파일 경로 (Airflow 작업 환경에 맞게 조정)
        csv_file_path = '/opt/airflow/dags/crawling_output/contentour_exhibitions.csv'

        # CSV 파일 읽기
        df = pd.read_csv(csv_file_path)

        page_no = 0
        metadata = {}
        documents = []

        for index in range(len(df)):
            page_content = f"전시회명: {df['title'][index]}\n개요: {df['overview'][index]}\n시작일: {df['시작일'][index]}\n종료일: {df['종료일'][index]}\n국가: {df['국가'][index]}\n분야/분류: {df['분야/분류'][index]}\n참가기업 수: {df['참가기업 수'][index]}\n총 방문자 수: {df['총 방문자 수'][index]}\n전시장: {df['전시장'][index]}\n전시회 홈페이지: {df['전시회 홈페이지'][index]}"
            contents = text_splitter.create_documents([page_content])
            for content in contents:
                metadata = {'source': 'contentour_exhibition', 'page_no': page_no, 'category': '4. 컨퍼런스 및 박람회, 전시회', 'url': df['url'][index], 'date': df['crawling_date'][index]}
                document = Document(page_content=content.page_content, metadata=metadata)
                documents.append(document)
                page_no += 1

        # 문서 객체를 pickle 파일로 저장
        pickle_file_path = '/opt/airflow/dags/csv_to_pickle/contentour_exhibitions.pkl'  # 실제 저장 경로로 수정
        with open(pickle_file_path, 'wb') as file:
            pickle.dump(documents, file)

    process_data()


transform_contentour_exhibition_data()
