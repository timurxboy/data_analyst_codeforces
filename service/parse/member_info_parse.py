from ..api.codeforces_api import CodeforcesAPI
from ..db import Database
import time
import logging
import requests
from bs4 import BeautifulSoup

class MemberInfoParse:
    def __init__(self):
        self.api = CodeforcesAPI()  # Инициализация API Codeforces
        self.db = Database()  # Инициализация подключения к базе данных
        
    def create_member_info(self, cur, member_info: dict):
        create_member_info_query = '''
            INSERT INTO member_info (
                first_name, last_name, country, city, organization, rating, max_rating, 
                rank, max_rank, friend_of_count, title_photo, avatar, contribution, 
                last_online_time_seconds, registration_time_seconds, handle
            ) 
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (handle) DO NOTHING;
        '''
        try:
            cur.execute(create_member_info_query, (
                member_info.get('firstName', None),
                member_info.get('lastName', None),
                member_info.get('country', None),
                member_info.get('city', None),
                member_info.get('organization', None),
                member_info.get('rating', None),
                member_info.get('maxRating', None),
                member_info.get('rank', None),
                member_info.get('maxRank', None),
                member_info.get('friendOfCount', 0),
                member_info.get('titlePhoto', None),
                member_info.get('avatar', None),
                member_info.get('contribution', 0),
                member_info.get('lastOnlineTimeSeconds', 0),
                member_info.get('registrationTimeSeconds', 0),
                member_info.get('handle')
            ))
        except Exception as e:
            logging.error(f"Ошибка при добавлении пользователя {member_info.get('handle')}: {e}")

    def get_member_handler(self, cur):
        get_member_handler_query = '''
            SELECT * FROM member
            ORDER BY id;
        '''
        cur.execute(get_member_handler_query)
        # print(cur.fetchall())
        return cur.fetchall()

    def fetch_members_info(self):
        conn = self.db.connect()  # Открываем одно подключение на всю обработку страниц
        
        try:
            with conn.cursor() as cur:
                members = self.get_member_handler(cur=cur)
                for member in members:
                    # print(member[1])
                    if member[1].lower() == 'timurxboy':
                        print(member)
                    
            # user_info = self.api.get_user_info(user_handle)[0]
            # if user_info:
            #     logging.info(f'Обрабатывается пользователь: {user_info["handle"]}')
            #     self.create_user(cur, user_info)
            #     conn.commit()  # Коммитим после каждой страницы
            #     logging.info(f'Страница {page} завершена!')
            #     time.sleep(1)



        # try:
        #     with conn.cursor() as cur:
        #         for page in range(3): #837
        #             logging.info(f'Обрабатываем страницу: {self.ratings_page_url}{page}')
        #             response = requests.get(f'{self.ratings_page_url}{page}', headers=self.ratings_page_headers)
        #             if response.status_code == 200:
        #                 soup = BeautifulSoup(response.text, 'html.parser')
        #                 rating_div = soup.find('div', class_='datatable ratingsDatatable')
        #                 if rating_div:
        #                     table = rating_div.find('table')
        #                     if table:
        #                         rows = table.find_all('tr')
        #                         for row in rows:
        #                             cells = row.find_all('td', style='text-align:left;padding-left:1em;')
        #                             if not cells:
        #                                 continue                                      
        #                             for cell in cells:
        #                                 link = cell.find('a')
        #                                 if link and 'href' in link.attrs:
        #                                     href_value = link['href']
        #                                     if '/profile/' in href_value:
        #                                         member_handle = href_value.split('/profile/')[1]
        #                                         if member_handle:
        #                                             self.create_member(cur, member_handle)

        #             conn.commit()  # Коммитим после каждой страницы
        #             logging.info(f'Страница {page} завершена!')
        #             time.sleep(1)

        except Exception as e:
            logging.error(f"Ошибка при обработке страниц: {e}")
        finally:
            conn.close()  # Закрываем соединение после всех страниц


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = MemberInfoParse()
    parser.fetch_members_info()

