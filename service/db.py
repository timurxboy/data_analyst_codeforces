import psycopg2
from psycopg2 import sql


class Database:
    def __init__(self):
        self.dbname = "codeforces"
        self.user = "postgres"
        self.password = "2RGFDjoBgr9etrjlRU3NR1xLX9CCKw8i7jKA2Rhc"
        self.host = "localhost"
        self.port = "5432"

    def connect(self):
        """Создает и возвращает подключение к базе данных."""
        return psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )

    def create_tables(self):
        """Создает необходимые таблицы в базе данных."""
        conn = self.connect()
        cur = conn.cursor()

        create_member_table = '''
        CREATE TABLE IF NOT EXISTS member (
            id SERIAL PRIMARY KEY,
            handle VARCHAR(50) UNIQUE NOT NULL
        );
        '''

        # SQL для создания таблицы user_info
        create_member_info_table = '''
        CREATE TABLE IF NOT EXISTS member_info (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            country VARCHAR(50),
            city VARCHAR(50),
            organization VARCHAR(255),
            rating INTEGER,
            max_rating INTEGER,
            rank VARCHAR(50),
            max_rank VARCHAR(50),
            friend_of_count INTEGER,
            title_photo VARCHAR(255),
            avatar VARCHAR(255),
            contribution INTEGER,
            last_online_time_seconds INTEGER,
            registration_time_seconds INTEGER,
            handle VARCHAR(50) UNIQUE NOT NULL
        );
        '''

        create_contest_table = '''
        CREATE TABLE IF NOT EXISTS contest (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(50),
            phase VARCHAR(50),
            frozen BOOLEAN,
            duration_seconds INTEGER,
            start_time TIMESTAMP, 
            end_time TIMESTAMP,  
            relative_time_seconds INTEGER 
        );
        '''

        create_problem_table = '''
        CREATE TABLE IF NOT EXISTS problem (
            id SERIAL PRIMARY KEY,
            contest_id INTEGER,
            index VARCHAR(50),
            solved_count INTEGER
        );
        '''

        # delete_problem_table = '''
        # DROP TABLE problem;
        # '''

        # Выполнение запросов на создание таблиц
        try:
            cur.execute(create_member_table)
            cur.execute(create_member_info_table)
            cur.execute(create_contest_table)
            cur.execute(create_problem_table)
            # cur.execute(delete_problem_table)

            # Сохранение изменений в базе данных
            conn.commit()
            print("Таблицы созданы успешно.")

        except Exception as e:
            print(f"Ошибка при создании таблиц: {e}")
            conn.rollback()

        finally:
            # Закрытие соединения
            cur.close()
            conn.close()


if __name__ == "__main__":
    # Создание экземпляра класса Database и вызов метода create_tables
    db = Database()
    db.create_tables()

