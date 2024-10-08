from ..api.codeforces_api import CodeforcesAPI
from ..db import Database
import psycopg2
from datetime import datetime

class ContestParse:
    def __init__(self):
        self.api = CodeforcesAPI()
        self.db = Database()

    def create_contests(self):
        contests = self.api.get_contest_list()
        conn = self.db.connect()
        create_contest_query = '''
            INSERT INTO contest (id, name, type, phase, frozen, duration_seconds, start_time, end_time, relative_time_seconds)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;  -- Игнорировать дубликаты
        '''
        
        try:
            with conn: 
                with conn.cursor() as cur:
                    for contest in contests:
                        start_time = datetime.fromtimestamp(contest['startTimeSeconds']) 
                        end_time = datetime.fromtimestamp(contest['startTimeSeconds'] + contest['durationSeconds'])
                        
                        cur.execute(create_contest_query, (
                            contest['id'],
                            contest['name'],
                            contest['type'],
                            contest['phase'],
                            contest['frozen'],
                            contest['durationSeconds'],
                            start_time, 
                            end_time,  
                            contest['relativeTimeSeconds']
                        ))
                    conn.commit() 

        except psycopg2.Error as e:
            print(f"Произошла ошибка базы данных: {e}")

        except Exception as e:
            print(f"Произошла ошибка: {e}")
        
        finally:
            conn.close()

if __name__ == '__main__':
    parser = ContestParse()
    parser.create_contests() 
