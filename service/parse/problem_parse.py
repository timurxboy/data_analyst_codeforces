from ..api.codeforces_api import CodeforcesAPI
from ..db import Database
import psycopg2
from datetime import datetime

class ProblemsParse:
    def __init__(self):
        self.api = CodeforcesAPI()
        self.db = Database()

    def create_problems(self):
        problems = self.api.get_problemset_problems()['problemStatistics']
        conn = self.db.connect()
        create_contest_query = '''
            INSERT INTO problem (contest_id, index, solved_count)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING;  -- Игнорировать дубликаты
        '''
        
        try:
            with conn: 
                with conn.cursor() as cur:
                    for problem in problems:
                        print(problem)
                        cur.execute(create_contest_query, (
                            int(problem['contestId']),
                            problem['index'],
                            problem['solvedCount'],
                        ))
                    conn.commit() 

        except psycopg2.Error as e:
            print(f"Произошла ошибка базы данных: {e}")

        except Exception as e:
            print(f"Произошла ошибка: {e}")
        
        finally:
            conn.close()

if __name__ == '__main__':
    parser = ProblemsParse()
    parser.create_problems() 
