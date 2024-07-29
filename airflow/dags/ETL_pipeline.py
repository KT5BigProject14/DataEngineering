import os
import pickle
import logging
import pendulum
from airflow.decorators import dag, task, bash_task
from airflow.operators.bash import BashOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator

# 기본 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dag(
    schedule_interval=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["example"],
)
def ETL_pipeline():

    @task
    def clean_datafiles():
        directories = ['/opt/airflow/dags/crawling_output', '/opt/airflow/dags/csv_to_pickle', '/opt/airflow/dags/pdf_datafiles']
        for directory in directories:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logging.info(f"Deleted file: {file_path}")
                except Exception as e:
                    logging.error(f"Failed to delete {file_path}. Reason: {e}")

    clean_task = clean_datafiles()

    trigger_contentour_exhibition = TriggerDagRunOperator(
        task_id='trigger_contentour_exhibition',
        trigger_dag_id='contentour_exhibition_etl',
        wait_for_completion=True,
    )

    trigger_gep = TriggerDagRunOperator(
        task_id='trigger_gep',
        trigger_dag_id='gep_exhibition_crawler_etl',
        wait_for_completion=True,
    )

    trigger_indian_trade_portal_faq = TriggerDagRunOperator(
        task_id='trigger_indian_trade_portal_faq',
        trigger_dag_id='indian_trade_portal_faq_crawler_etl',
        wait_for_completion=True,
    )

    trigger_indian_trade_portal_latest_news = TriggerDagRunOperator(
        task_id='trigger_indian_trade_portal_latest_news',
        trigger_dag_id='indian_trade_portal_latest_news_etl',
        wait_for_completion=True,
    )

    trigger_fnbnews = TriggerDagRunOperator(
        task_id='trigger_fnbnews',
        trigger_dag_id='fnbnews_crawler_etl',
        wait_for_completion=True,
    )

    # TRANSFORM
    transform_contentour = TriggerDagRunOperator(
        task_id='transform_contentour',
        trigger_dag_id='transform_contentour_exhibition_data',
        wait_for_completion=True,
    )

    transform_fnbnews = TriggerDagRunOperator(
        task_id='transform_fnbnews',
        trigger_dag_id='transform_fnbnews_data',
        wait_for_completion=True,
    )

    transform_gep = TriggerDagRunOperator(
        task_id='transform_gep',
        trigger_dag_id='transform_gep_exhibition_data',
        wait_for_completion=True,
    )

    transform_faq = TriggerDagRunOperator(
        task_id='transform_faq',
        trigger_dag_id='transform_indian_trade_portal_faq_data',
        wait_for_completion=True,
    )

    transform_latest_news = TriggerDagRunOperator(
        task_id='transform_latest_news',
        trigger_dag_id='transform_indian_trade_portal_latest_news_data',
        wait_for_completion=True,
    )

    @task.bash
    def kotra_abroad_strategy() -> str:
        return "python /opt/airflow/dags/website_to_crawl/kotra_abroad_strategy.py"

    @task.bash
    def kotra_fraud_examples() -> str:
        return "python /opt/airflow/dags/website_to_crawl/kotra_fraud_examples.py"

    @task.bash
    def kotra_market_news() -> str:
        return "python /opt/airflow/dags/website_to_crawl/kotra_market_news.py"

    @task.bash
    def transform_data() -> str:
        return "python /opt/airflow/dags/transform_generate_metadata/transformations.py"

    @task.bash
    def load_data() -> str:
        return "scp -i '/opt/airflow/logo_data.pem' -o StrictHostKeyChecking=no /opt/airflow/dags/csv_to_pickle/merged_all_data.pkl ubuntu@54.181.1.215:/home/ubuntu/AIModel/langserve/chatbot/app/database"

    @task
    def final_task():
        logging.info("All ETL processes are completed.")

        # Pickle 파일 병합 작업
        pickle_dir = '/opt/airflow/dags/csv_to_pickle'
        output_file = '/opt/airflow/dags/csv_to_pickle/merged_all_data.pkl'

        # Pickle 파일 로드 함수 정의
        def load_pickle(file_path):
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            return data

        # Pickle 파일 저장 함수 정의
        def save_pickle(data, file_path):
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)

        # 여러 Pickle 파일 병합 함수 정의
        def merge_pickles(pickle_files, output_file):
            merged_data = []
            for file in pickle_files:
                data = load_pickle(file)
                merged_data.extend(data)  # assuming data is a list
            save_pickle(merged_data, output_file)

        # Pickle 파일 목록 가져오기
        pickle_files = [os.path.join(pickle_dir, f) for f in os.listdir(pickle_dir) if f.endswith('.pkl')]

        # Pickle 파일 병합
        merge_pickles(pickle_files, output_file)
        logging.info(f"Pickle files merged into {output_file}")

    clean_task >> [
        trigger_contentour_exhibition >> transform_contentour,
        trigger_gep >> transform_gep,
        trigger_indian_trade_portal_faq >> transform_faq,
        trigger_indian_trade_portal_latest_news >> transform_latest_news,
        trigger_fnbnews >> transform_fnbnews,
        [kotra_abroad_strategy(), kotra_fraud_examples(), kotra_market_news()] >> transform_data(),
    ] >> final_task() >> load_data()


ETL_pipeline()
