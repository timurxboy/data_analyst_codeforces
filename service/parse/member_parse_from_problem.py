from ..api.codeforces_api import CodeforcesAPI
from ..db import Database
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor, as_completed

import logging
from logging.handlers import RotatingFileHandler

class MemberParse:
    def __init__(self):
        self.api = CodeforcesAPI()  # Инициализация API Codeforces
        self.db = Database()  # Инициализация подключения к базе данных
        self.ratings_page_url = 'https://codeforces.com/problemset/status/'
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        self.chrome_options.add_argument('--disable-infobars')
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36")

        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--window-size=1920x1080')
        self.chrome_options.add_argument('--disable-gpu')

        # Настраиваем два логгера
        self.setup_logging()

    def setup_logging(self):
        # Логгер для терминала
        self.console_logger = logging.getLogger("console_logger")
        self.console_logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        self.console_logger.addHandler(console_handler)

        # Логгер для файла
        self.file_logger = logging.getLogger("file_logger")
        self.file_logger.setLevel(logging.DEBUG)
        file_handler = RotatingFileHandler('logging_member_parse_from_problem.log', maxBytes=10**6, backupCount=3)  # Лог-файл с ротацией
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.file_logger.addHandler(file_handler)

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
            self.file_logger.error(f"Ошибка при добавлении пользователей: {e}")

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
        driver.implicitly_wait(5)
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
        
        # Логгируем детали запроса в файл
        if not dataset:
            self.file_logger.error(f'Ошибка загрузки страницы {url}')
        else:
            self.file_logger.info(f'Успешно загружена страница {url} с {len(dataset)} пользователями')

        return dataset

    def process_problem(self, cur, conn, contestId, index, page_count, task_id):
        for page in range(1, page_count + 1):
            dataset = self.fetch_page(contestId, index, page)
            if dataset:
                self.create_member(cur=cur, conn=conn, dataset=dataset)

        # Сообщаем о завершении задачи в консоли
        self.console_logger.info(f'Задача {index} из контеста {contestId} завершена')

    def fetch_members_from_page(self):
        conn = self.db.connect()
        try:
            with conn.cursor() as cur:
                problems = self.get_problem(cur=cur)
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    
                    for i in range(11, len(problems) + 1):
                        problem = problems[i]
                        contestId, index, solvedCount = problem[1], problem[2], problem[3]
                        page_count = (solvedCount + 49) // 50
                        
                        futures.append(executor.submit(self.process_problem, cur, conn, contestId, index, page_count, i))

                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            self.file_logger.error(f"Ошибка в процессе обработки: {e}")
                        
        except Exception as e:
            self.file_logger.error(f"Ошибка при обработке страниц: {e}")
        finally:
            conn.close()

if __name__ == '__main__':
    parser = MemberParse()
    parser.fetch_members_from_page()
