from ..api.codeforces_api import CodeforcesAPI
from ..db import Database
import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

class MemberParse:
    def __init__(self):
        self.api = CodeforcesAPI()  # Инициализация API Codeforces
        self.db = Database()  # Инициализация подключения к базе данных
        self.ratings_page_url = 'https://codeforces.com/problemset/status/'
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # Скрывает автоматизацию от сайта
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Отключает "controlled by automation"
        self.chrome_options.add_experimental_option('useAutomationExtension', False)  # Отключает автоматизацию
        self.chrome_options.add_argument('--disable-infobars')  # Убирает инфо-панель "Chrome is being controlled by automated test software"

        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36")

        self.chrome_options.add_argument('--disable-dev-shm-usage')  # Уменьшает использование разделяемой памяти
        self.chrome_options.add_argument('--no-sandbox')  # Для предотвращения сбоев в headless-режиме
        self.chrome_options.add_argument('--window-size=1920x1080')  # Определяет размер окна

        self.chrome_options.add_argument('--disable-gpu')  # Отключить использование GPU

    def create_member(self, cur, conn, dataset: set):
        create_member_query = '''
            INSERT INTO member (handle) 
            VALUES (%s)
            ON CONFLICT (handle) DO NOTHING;
        '''
        try:
            cur.executemany(create_member_query, [(handle,) for handle in dataset])  # Используем executemany для вставки всех пользователей сразу
            conn.commit()
        except Exception as e:
            logging.error(f"Ошибка при добавлении пользователей: {e}")

    def get_problem(self, cur):
        get_problem_query = '''
            SELECT * FROM problem
            ORDER BY problem.contest_id, problem.index
            ;
        '''
        cur.execute(get_problem_query)
        return cur.fetchall()

    def fetch_page(self, contestId, index, page):
        url = f'{self.ratings_page_url}{contestId}/problem/{index}/page/{page}'
        driver = webdriver.Chrome(options=self.chrome_options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        driver.get(url=url)
        driver.implicitly_wait(3)  # Ожидание до 10 секунд перед извлечением
        response = driver.page_source
        driver.quit()

        dataset = set()
        if response:
            soup = BeautifulSoup(response, 'html.parser')
            table = soup.find('table', class_='status-frame-datatable')
            if table:
                rows_tr = table.find_all('tr')
                for row_tr in rows_tr:
                    rows_td = row_tr.find_all('td')
                    for rod_td in rows_td:
                        link = rod_td.find('a')
                        if link and 'href' in link.attrs:
                            href_value = link['href']
                            if '/profile/' in href_value:
                                member_handle = href_value.split('/profile/')[1]
                                if member_handle:
                                    dataset.add(member_handle)
        if not dataset:
            logging.error(f'Ошибка загрузки страницы {url}')

        return dataset

    def process_problem(self, cur, conn, contestId, index, page_count, task_id, pbar):
        for page in range(1, page_count + 1):
            dataset = self.fetch_page(contestId, index, page)
            if dataset:
                self.create_member(cur=cur, conn=conn, dataset=dataset)

            percent_complete = (page / page_count) * 100
            pbar.update(1)  # Обновляем прогресс-бар

    def fetch_members_from_page(self):
        conn = self.db.connect()  # Открываем одно подключение на всю обработку страниц
        try:
            with conn.cursor() as cur:
                problems = self.get_problem(cur=cur)
                
                # Ограничиваем до 10 потоков
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    progress_bars = []  # Список для прогресс-баров
                    
                    for i in range(11, len(problems) + 1):
                        problem = problems[i]
                        contestId, index, solvedCount = problem[1], problem[2], problem[3]
                        page_count = (solvedCount + 49) // 50
                        
                        # Создаём прогресс-бар для каждой задачи
                        pbar = tqdm(total=page_count, desc=f"Задача {index} из контеста {contestId}")
                        progress_bars.append(pbar)
                        
                        # Добавляем задачи в executor
                        futures.append(executor.submit(self.process_problem, cur, conn, contestId, index, page_count, i, pbar))

                    # Обрабатываем результаты
                    for future in as_completed(futures):
                        try:
                            future.result()  # Если возникает ошибка, она будет брошена здесь
                        except Exception as e:
                            logging.error(f"Ошибка в процессе обработки: {e}")
                        
                    # Закрываем все прогресс-бары после завершения
                    for pbar in progress_bars:
                        pbar.close()
                        
        except Exception as e:
            logging.error(f"Ошибка при обработке страниц: {e}")
        finally:
            conn.close()  # Закрываем соединение после всех страниц

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = MemberParse()
    parser.fetch_members_from_page()


