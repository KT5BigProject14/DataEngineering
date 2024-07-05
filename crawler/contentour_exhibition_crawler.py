import re
import time

import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_contentour_exhibition_urls():
    # 국가종합전시회
    CONTENTOUR_COMPREHENSIVE_EXHIBITION_URL = 'https://contentour.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ec%a0%95%eb%b3%b4/%ed%95%b4%ec%99%b8%ec%a0%84%ec%8b%9c%ed%9a%8c/?mod=list&pageid=1&category5=&category1=%EA%B5%AD%EA%B0%80%EC%A2%85%ED%95%A9%EC%A0%84%EC%8B%9C%ED%9A%8C&category2=%EC%9D%B8%EB%8F%84&category3=&category4='

    # 식품/음료/호텔
    CONTENTOUR_FOOD_URL = 'https://contentour.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ec%a0%95%eb%b3%b4/%ed%95%b4%ec%99%b8%ec%a0%84%ec%8b%9c%ed%9a%8c/?mod=list&pageid=1&category5=&category1=%EC%8B%9D%ED%92%88%2F%EC%9D%8C%EB%A3%8C%2F%ED%98%B8%ED%85%94%2F%ED%94%84%EB%A0%8C%EC%B0%A8%EC%9D%B4%EC%A6%88&category2=%EC%9D%B8%EB%8F%84&category3=&category4='

    # 동물/애완용품
    PET_URL = 'https://contentour.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ec%a0%95%eb%b3%b4/%ed%95%b4%ec%99%b8%ec%a0%84%ec%8b%9c%ed%9a%8c/?mod=list&pageid=1&category5=&category1=%EB%8F%99%EB%AC%BC%2F%EC%95%A0%EC%99%84%EC%9A%A9%ED%92%88&category2=%EC%9D%B8%EB%8F%84&category3=&category4='

    URLS = [CONTENTOUR_COMPREHENSIVE_EXHIBITION_URL, CONTENTOUR_FOOD_URL, PET_URL]
    urls = []
    for URL in URLS:
        response = requests.get(URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('tbody')
        links = table.find_all('a', href=True)
        for link in links:
            url = 'https://contentour.co.kr' + link['href']
            urls.append(url)
    
    return urls

def make_dataset(urls: list):
    contentour_exhibitions = []
    
    for url in urls:    
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find_all('h1')[1].text
        overview1 = soup.find_all('p')[1].text
        overview2 = soup.find_all('p')[2].text
        exhibition = {'title': title, 'overview': overview1 + ' ' + overview2,}
        
        info1 = '\n'.join(soup.find_all('div', class_='kboard-aside')[0].text.replace('\n\n', '').split('\n')[:7])
        info2 = '전시회 홈페이지 ' + soup.find_all('div', class_='kboard-aside')[0].find_all('a')[0]['href']
        informations = info1 + '\n' + info2
        
        for words in informations.split('\n'):
            words = words.split()
            exhibition[' '.join(words[:-1])] = words[-1]
                    
        contentour_exhibitions.append(exhibition)
        
    df = pd.DataFrame(contentour_exhibitions)
    df.to_csv('contentour_exhibitions.csv', index=False)
    
    
if __name__ == '__main__':
    urls = extract_contentour_exhibition_urls()
    make_dataset(urls)