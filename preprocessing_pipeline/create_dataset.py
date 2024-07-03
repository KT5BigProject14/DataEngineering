from glob import glob
from tqdm import tqdm
import pandas as pd
from langchain_community.document_loaders import PyPDFLoader


def get_total_pdfs(base_path):
    """
    주어진 기본 경로에서 모든 PDF 파일 경로를 가져옵니다.
    
    Parameters:
    base_path (str): PDF 파일들이 저장된 기본 경로
    
    Returns:
    list: PDF 파일 경로 리스트
    """
    total_pdfs = []
    folders = glob(base_path + '/**')

    for folder in folders:
        total_pdfs += glob(folder + '/**')
        
    total_pdfs = [pdf.replace('\\', '/') for pdf in total_pdfs if 'Forms' not in pdf]
    return total_pdfs
    
def extract_pdf_data(pdf_path, data_name: str):
    """
    주어진 PDF 파일 경로 리스트에서 데이터를 추출하여 CSV 파일로 저장합니다.
    
    Parameters:
    pdf_paths (list): PDF 파일 경로 리스트
    data_name (str): 저장할 CSV 파일 이름
    
    Returns:
    None
    """
    source = []
    category = []
    page_content = []
    page_no = []
    
    for pdf_path in tqdm(pdf_path):
        loader = PyPDFLoader(pdf_path, extract_images=False)
        pages = loader.load()

        for index in range(len(pages)):
            # 추출된 텍스트 후처리
            text = pages[index].page_content.strip()
            try:
                # 텍스트가 깨지는 경우를 대비한 예외 처리
                text = text.encode('utf-8').decode('utf-8')
            except UnicodeDecodeError:
                pass
            
            source.append(pdf_path.split(']')[-1].split('.pdf')[0])
            category.append(pdf_path.split('/')[2])
            page_content.append(pages[index].page_content.strip())
            page_no.append(index)
            
    df = pd.DataFrame({'source': source, 'category': category, 'page_content': page_content, 'page_no': page_no})
    df.to_csv(data_name, index=False)


if __name__ == "__main__":
    base_path = 'data/PDF_with_contents'        # PDF 파일들이 저장된 기본 경로
    total_pdfs = get_total_pdfs(base_path)      # 모든 PDF 파일 경로를 가져옴
    extract_pdf_data(total_pdfs, 'data.csv')   # PDF 데이터 추출 및 CSV 파일로 저장