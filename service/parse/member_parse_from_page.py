from ..api.codeforces_api import CodeforcesAPI
from ..db import Database
import time
import logging
import requests
from bs4 import BeautifulSoup

class MemberParse:
    def __init__(self):
        self.api = CodeforcesAPI()  # Инициализация API Codeforces
        self.db = Database()  # Инициализация подключения к базе данных
        self.ratings_page_url = 'https://codeforces.com/ratings/page/'
        self.ratings_page_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def create_member(self, cur, conn, dataset: set):
        create_member_query = '''
            INSERT INTO member (
                handle
            ) 
            VALUES (
                %s
            )
            ON CONFLICT (handle) DO NOTHING;
        '''
        try:
            for handle in dataset:
                cur.execute(create_member_query, (handle,))
            conn.commit()
        except Exception as e:
            logging.error(f"Ошибка при добавлении пользователя {handle}: {e}")

    def fetch_members_from_page(self):
        conn = self.db.connect()  # Открываем одно подключение на всю обработку страниц

        try:
            with conn.cursor() as cur:
                for page in range(711, 837):  # Обработаем первые 2 страницы
                    dataset = set()
                    logging.info(f'Обрабатываем страницу: {self.ratings_page_url}{page}')
                    response = requests.get(f'{self.ratings_page_url}{page}', headers=self.ratings_page_headers)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        rating_div = soup.find('div', class_='datatable ratingsDatatable')
                        if rating_div:
                            table = rating_div.find('table')
                            if table:
                                rows = table.find_all('tr')
                                for row in rows:
                                    cells = row.find_all('td', style='text-align:left;padding-left:1em;')
                                    if not cells:
                                        continue                                      
                                    for cell in cells:
                                        link = cell.find('a')
                                        if link and 'href' in link.attrs:
                                            href_value = link['href']
                                            if '/profile/' in href_value:
                                                member_handle = href_value.split('/profile/')[1]
                                                if member_handle:
                                                    dataset.add(member_handle)
            
                        self.create_member(cur=cur, conn=conn, dataset=dataset)
                        logging.info(f'Страница {page} завершена!')
                        time.sleep(1)
                    else:
                        logging.error(f'Страница {page} вывел ошибку - {response.status_code}')
                        break
        except Exception as e:
            logging.error(f"Ошибка при обработке страниц: {e}")
        finally:
            conn.close()  # Закрываем соединение после всех страниц



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = MemberParse()
    parser.fetch_members_from_page()
