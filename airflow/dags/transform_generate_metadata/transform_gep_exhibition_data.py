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
def transform_gep_exhibition_data():

    @task()
    def process_data():
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False
        )

        # CSV 파일 경로 (Airflow 작업 환경에 맞게 조정)
        csv_file_path = '/opt/airflow/dags/crawling_output/gep_exhibitions.csv'

        # CSV 파일 읽기
        df = pd.read_csv(csv_file_path)

        page_no = 0
        metadata = {}
        documents = []

        for index in range(len(df)):
            page_content = f"전시회명: {df['title'][index]}\n개요: {df['overview'][index]}\n개최기간: {df['개최기간'][index]}\n개최국가: {df['개최국가'][index]}\n개최장소: {df['개최장소'][index]}\n개최규모: {df['개최규모'][index]}\n산업분야: {df['산업분야'][index]}\n전시품목: {df['전시품목'][index]}\n주최기관: {df['주최기관'][index]}\n담당자: {df['담당자'][index]}\n전화: {df['전화'][index]}\n팩스: {df['팩스'][index]}\n이메일: {df['이메일'][index]}\n홈페이지: {df['홈페이지'][index]}\n담당자전화: {df['담당자전화'][index]}\n팩스이메일: {df['팩스이메일'][index]}"
            contents = text_splitter.create_documents([page_content])
            for content in contents:
                metadata = {'source': 'gep_exhibition', 'page_no': page_no, 'category': '4. 컨퍼런스 및 박람회, 전시회', 'url': df['url'][index], 'date': df['crawling_date'][index]}
                document = Document(page_content=content.page_content, metadata=metadata)
                documents.append(document)
                page_no += 1

        # 문서 객체를 pickle 파일로 저장
        pickle_file_path = '/opt/airflow/dags/csv_to_pickle/gep_exhibitions.pkl'
        with open(pickle_file_path, 'wb') as file:
            pickle.dump(documents, file)

    process_data()


transform_gep_exhibition_data()
