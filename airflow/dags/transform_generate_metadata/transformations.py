import glob
import os
import pickle
from datetime import datetime

import pandas as pd
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 디렉토리 경로 설정 (여기에 CSV 파일들이 위치한 디렉토리 경로를 입력하세요)
directory_path = '/opt/airflow/dags/pdf_datafiles'

# 모든 CSV 파일 경로를 리스트로 가져오기
csv_files = glob.glob(f"{directory_path}/*.csv")

# 다양한 인코딩을 시도하여 파일을 읽는 함수
def read_csv_with_encoding(file_path):
    encodings = ['utf-8', 'cp949']
    for encoding in encodings:
        try:
            return pd.read_csv(file_path, encoding=encoding, index_col = False)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode the file: {file_path}")

# 파일을 읽어서 DataFrame 리스트에 저장
dfs = [read_csv_with_encoding(file) for file in csv_files]


documents = []
output_date=datetime.now().strftime("%Y-%m-%d")

def split_text_into_sections(text):
    text_splitter = RecursiveCharacterTextSplitter(
        separators=[
            "\n\n",
            "\n",
            " ",
            ".",
            ",",
            "\u200b",  # Zero-width space
            "\uff0c",  # Fullwidth comma
            "\u3001",  # Ideographic comma
            "\uff0e",  # Fullwidth full stop
            "\u3002",  # Ideographic full stop
            "",
        ],
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(text)
    return chunks

category = ''

for idx, df in enumerate(dfs):
    for index, row in df.iterrows():
        # Extract relevant fields
        source = csv_files[idx]
        category = '2. 경제 및 시장 분석'
        url = 'https://www.kotra.or.kr/kp/index.do'
        date = row.get('date', output_date) if pd.notna(row.get('date')) else output_date

        # Combine other fields into page_content
        columns_to_include = [col for col in df.columns if col not in ['url', 'date']]
        page_content = "\n".join([f"{col}: {row.get(col, '')}" for col in columns_to_include])
        
        chunks = split_text_into_sections(page_content)

        for page_no, chunk in enumerate(chunks):
            # Create Document object
            document = Document(
                page_content=chunk,
                metadata={
                    'source': source,
                    'url': url,
                    'date': date,
                    'category': category,
                    'page_no': page_no
                }
            )
            documents.append(document)

save_dir = "/opt/airflow/dags/csv_to_pickle"
os.makedirs(save_dir, exist_ok=True)

with open('/opt/airflow/dags/csv_to_pickle/documents.pkl', 'wb') as file:
    pickle.dump(documents, file)
