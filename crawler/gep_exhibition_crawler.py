import re
import time

import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_gep_exhibition_urls():
    GEP_EXHIBITION_URL = 'https://www.gep.or.kr/gept/ovrss/exbi/exbiInfo/allExbiList.do#'

    # WebDriver 초기화 (Chrome 사용 예시)
    driver = webdriver.Chrome()

    # 페이지 로드
    driver.get(GEP_EXHIBITION_URL)
    time.sleep(3)

    # '산업분야 더보기' 버튼 클릭
    wait = WebDriverWait(driver, 10)
    more_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="searchForm"]/div/div[2]/div[1]/div[3]/div/div/div/div[2]/button')))
    more_button.click()

    # 모든 창 핸들을 가져옴
    all_windows = driver.window_handles
    main_window = driver.current_window_handle

    # 새로 열린 창으로 전환
    for window in all_windows:
        if window != main_window:
            driver.switch_to.window(window)
            break

    # '동물&애완용품' 버튼 클릭
    animal_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="rowid1"]/div[2]/label')))
    animal_button.click()

    # '농수산' 버튼 클릭
    farm_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="rowid8"]/div[1]/label')))
    farm_button.click()

    # '식품&음료' 버튼 클릭
    food_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="rowid2"]/div[3]/label')))
    food_button.click()

    # '확인' 버튼 클릭
    confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="frm"]/div/div/div/div[2]/div[2]/a[1]')))
    confirm_button.click()

    # 원래 창으로 돌아오기 전 대기
    time.sleep(3)  # 확인 버튼 클릭 후 창이 닫히는 시간을 확보

    # 작업 완료 후 원래 창으로 돌아오기
    driver.switch_to.window(main_window)

    # '국가분야 더보기' 버튼 클릭
    wait = WebDriverWait(driver, 10)
    more_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="searchForm"]/div/div[2]/div[1]/div[4]/div/div/div/div/div[3]/button')))
    more_button.click()

    # 모든 창 핸들을 가져옴
    all_windows = driver.window_handles
    main_window = driver.current_window_handle

    # 새로 열린 창으로 전환
    for window in all_windows:
        if window != main_window:
            driver.switch_to.window(window)
            break

    # '인도' 버튼 클릭
    india_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="rowid46"]/div[3]/label')))
    india_button.click()

    # '확인' 버튼 클릭
    confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="frm"]/div/div/div/div[2]/div[2]/a[1]')))
    confirm_button.click()

    # 원래 창으로 돌아오기 전 대기
    time.sleep(3)  # 확인 버튼 클릭 후 창이 닫히는 시간을 확보

    # 작업 완료 후 원래 창으로 돌아오기
    driver.switch_to.window(main_window)

    search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="searchForm"]/div/div[2]/div[2]/a[2]')))
    search_button.click()

    time.sleep(3)

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    links = soup.find('ul', class_='list-search-card row').find_all('a')

    urls = []
    # 'onclick' 속성에서 fnDetail 값을 추출
    for link in links:
        onclick_value = link.get('onclick', '')
        match = re.search(r'fnDetail\("([^"]+)"\)', onclick_value)
        if match:
            detail_value = match.group(1)
            url = 'https://www.gep.or.kr/gept/ovrss/exbi/exbiInfo/exbiDetailMain.do?ovrssExbiCd='
            urls.append(url + detail_value)
            
    driver.quit()
    return urls

def make_dataset(urls: list):
    gep_exhibitions = []
    informations = ['주최기관', '담당자', '전화', '팩스', '이메일', '홈페이지']

    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = ' | '.join(soup.find_all('div', class_='text-info')[0].text.strip().split('\n')[:2])
        overview = soup.find_all('div', class_='ph-wrap')[0].text.replace('\n', '').strip()
        exhibition = {'title': title, 'overview': overview,}
        
        info1 = soup.find_all('div', class_='dotline-items')[0].text.replace('\n\n', '').split('\n')
        info1 = '\n'.join([word.replace('개최규모', '개최규모\n-\n') if word == '개최규모산업분야' else word for word in info1]).split('\n')
        for index in range(1, len(info1), 2):
            exhibition[info1[index - 1]] = info1[index]
                
        info2 = soup.find_all('div', class_='dotline-items')[1].text.replace('\n\n', '').strip().split('\n')
        if '주최기관' in info2:
            for index in range(1, len(info2), 2):
                exhibition[info2[index - 1]] = info2[index]
        else:
            for index in range(len(informations)):
                exhibition[informations[index]] = '-'
        
        gep_exhibitions.append(exhibition)
        
    df = pd.DataFrame(gep_exhibitions)
    df.to_csv('gep_exhibitions.csv', index=False)
    
    
if __name__ == '__main__':
    urls = extract_gep_exhibition_urls()
    make_dataset(urls)