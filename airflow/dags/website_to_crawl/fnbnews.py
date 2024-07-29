import time

import pandas as pd
import pendulum
import requests
from airflow.decorators import dag, task
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@dag(
    schedule_interval=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["example"],
)
def fnbnews_crawler_etl():
    FNBNEWS_URL = 'https://www.fnbnews.com/Top-News'
    output_path = '/opt/airflow/dags/crawling_output/fnbnews.csv'

    @task()
    def extract_fnbnews_data():
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920x1080')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=options)

        try:
            driver.get(FNBNEWS_URL)
            time.sleep(3)

            titles = []
            article_published_dates = []
            authors = []
            urls = []

            count = 100
            while count > 0:
                count -= 5
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                tables = soup.find_all('div', id='ContentPlaceHolder1_UpdatePanel1')

                for rows in tables:
                    rows = rows.find_all('a')
                    for row in rows:
                        if 'Top-News' in row['href']:
                            urls.append('https://www.fnbnews.com' + row['href'])

                for news_index in range(5):
                    try:
                        contents = soup.find_all('tr', id=f'ContentPlaceHolder1_lvPosts_Tr1_{news_index}')[0].text.replace('\n\n\n\n', '').strip().split('\n\n')

                        for index, content in enumerate(contents):
                            if index == 0:
                                titles.append(content.replace('\r\n', '')[1:].strip())
                            elif index == 1:
                                article_published_dates.append(content.replace('\r\n', '').strip())
                            elif index == 2:
                                authors.append(content.replace('\r\n', '').strip())

                    except IndexError:
                        continue

                try:
                    wait = WebDriverWait(driver, 10)
                    next_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ContentPlaceHolder1_btnNext"]')))
                    next_button.click()
                    time.sleep(5)
                except TimeoutException:
                    break

            page_contents = []
            for url in urls:
                try:
                    response = requests.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_contents.append(soup.find('span', class_='breadcrumb').text)
                except Exception as e:
                    print(f"Failed to get content from {url}: {e}")
                    page_contents.append("")

            df = pd.DataFrame({
                'title': titles,
                'page_content': page_contents,
                'article_published_date': article_published_dates,
                'author': authors,
                'url': urls,
            })

            df['article_published_date'] = pd.to_datetime(df['article_published_date'])
            df.to_csv(output_path, index=False)

        except WebDriverException as e:
            print(f"WebDriverException: {e}")
            driver.quit()
            raise e
        except Exception as e:
            driver.quit()
            raise e
        finally:
            driver.quit()

        return output_path


fnbnews_crawler_etl()
