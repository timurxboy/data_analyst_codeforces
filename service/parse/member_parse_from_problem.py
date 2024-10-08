# from ..api.codeforces_api import CodeforcesAPI
# from ..db import Database
# import time
# import logging
# import requests
# from bs4 import BeautifulSoup

# class MemberParse:
#     def __init__(self):
#         self.api = CodeforcesAPI()  # Инициализация API Codeforces
#         self.db = Database()  # Инициализация подключения к базе данных
#         self.ratings_page_url = 'https://codeforces.com/problemset/status/'
#         self.ratings_page_headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#         }

#     def create_member(self, cur, conn, dataset: set):
#         create_member_query = '''
#             INSERT INTO member (
#                 handle
#             ) 
#             VALUES (
#                 %s
#             )
#             ON CONFLICT (handle) DO NOTHING;
#         '''
#         try:
#             for handle in dataset:
#                 cur.execute(create_member_query, (handle,))
#             conn.commit()
#         except Exception as e:
#             logging.error(f"Ошибка при добавлении пользователя {handle}: {e}")

#     def get_problem(self, cur):
#             get_problem_query = '''
#                 SELECT * FROM problem
#                 ORDER BY id;
#             '''
#             cur.execute(get_problem_query)
#             # print(cur.fetchall())
#             return cur.fetchall()

#     def fetch_members_from_page(self):
#         conn = self.db.connect()  # Открываем одно подключение на всю обработку страниц


#         try:
#             with conn.cursor() as cur:
#                 problems = self.get_problem(cur=cur)
#                 for problemStatistic in problems:
#                     id = problemStatistic[0]
#                     contestId = problemStatistic[1]
#                     index = problemStatistic[2]
#                     solvedCount = problemStatistic[3]

#                     if solvedCount % 50 ==0:
#                         page_count = solvedCount // 50
#                     else:
#                         page_count = solvedCount // 50 + 1 

#                     for page in range(1, page_count+1):
#                         dataset = set()
#                         # logging.info(f'Обрабатываем страницу: {self.ratings_page_url}{contestId}/problem/{index}/page/{page}')
#                         response = requests.get(f'{self.ratings_page_url}{contestId}/problem/{index}/page/{page}', headers=self.ratings_page_headers)
#                         if response.status_code == 200:
#                             soup = BeautifulSoup(response.text, 'html.parser')
#                             table = soup.find('table', class_='status-frame-datatable')
#                             if table:
#                                 rows_tr = table.find_all('tr')
#                                 for row_tr in rows_tr:
#                                     rows_td = row_tr.find_all('td')
#                                     for rod_td in rows_td:
#                                         link = rod_td.find('a')
#                                         if link and 'href' in link.attrs:
#                                             href_value = link['href']
#                                             if '/profile/' in href_value:
#                                                 member_handle = href_value.split('/profile/')[1]
#                                                 if member_handle:
#                                                     dataset.add(member_handle)

#                             self.create_member(cur=cur, conn=conn, dataset=dataset)
#                             # logging.info(f'Страница {page} завершена!')
#                             time.sleep(1)
#                         else:
#                             logging.error(f'Страница {self.ratings_page_url}{contestId}/problem/{index}/page/{page} вывел ошибку - {response.status_code} \nID: {id}')
#                             break
#                     logging.info(f'Контест {contestId}, Index {index} завершена!')
                
#         except Exception as e:
#             logging.error(f"Ошибка при обработке страниц: {e}")
#         finally:
#             conn.close()  # Закрываем соединение после всех страниц



# if __name__ == '__main__':
#     logging.basicConfig(level=logging.INFO)
#     parser = MemberParse()
#     parser.fetch_members_from_page()


from ..api.codeforces_api import CodeforcesAPI
from ..db import Database
import time
import logging
import requests
from bs4 import BeautifulSoup
import sys

class MemberParse:
    def __init__(self):
        self.api = CodeforcesAPI()  # Инициализация API Codeforces
        self.db = Database()  # Инициализация подключения к базе данных
        self.ratings_page_url = 'https://codeforces.com/problemset/status/'
        self.ratings_page_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

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
            ORDER BY problem.contest_id;
        '''
        cur.execute(get_problem_query)
        return cur.fetchall()

    def fetch_page(self, contestId, index, page):
        url = f'{self.ratings_page_url}{contestId}/problem/{index}/page/{page}'
        response = requests.get(url, headers=self.ratings_page_headers)
        dataset = set()
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
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
        else:
            logging.error(f'Ошибка загрузки страницы {url}: {response.status_code}')
        return dataset

    def fetch_members_from_page(self):
        conn = self.db.connect()  # Открываем одно подключение на всю обработку страниц
        try:
            with conn.cursor() as cur:
                problems = self.get_problem(cur=cur)
                for problem in problems:
                for i in range (4, len(problems)+1):
                    problem = problems[i]
                    contestId, index, solvedCount = problem[1], problem[2], problem[3]
                    page_count = (solvedCount + 49) // 50  # Округляем вверх
                    logging.info(f'Контест {contestId}, задача {index} начался.')

                    for page in range(1, page_count + 1):
                        dataset = self.fetch_page(contestId, index, page)
                        if dataset:
                            self.create_member(cur=cur, conn=conn, dataset=dataset)

                        # Вычисляем и выводим процент завершения в одну строку
                        percent_complete = (page / page_count) * 100
                        print(f'Задача {index} из контеста {contestId}: {percent_complete:.2f}% завершено', end='\r', flush=True)
                        
                        time.sleep(1)  # Задержка для уменьшения нагрузки на сервер
                    
                    logging.info(f'Контест {contestId}, задача {index} завершена.')
                    print()  # Печатаем пустую строку для завершения обновления прогресса
        except Exception as e:
            logging.error(f"Ошибка при обработке страниц: {e}")
        finally:
            conn.close()  # Закрываем соединение после всех страниц

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = MemberParse()
    parser.fetch_members_from_page()


