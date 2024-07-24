from abc import ABC, abstractmethod
from configparser import ConfigParser

import psycopg2

from config import PARAM_FILE_NAME, SECTION
from src.api import HhAPI


class DB(ABC):
    """
    Абстрактный класс для работы с БД PostgreSQL
    """

    @staticmethod
    @abstractmethod
    def get_params(filename: str, section: str) -> dict:
        """
        Абстрактный метод для создания словаря с параметрами из файла database.ini
        :return:
        """
        pass

    def create_database(self):
        """
        Абстрактный метод для создания базы данных и таблиц
        :return:
        """
        pass

    def save_data_to_database(self, data):
        """
        Абстрактный метод сохранение данных
        :param data:
        :return:
        """
        pass


class DBManager(DB):
    """
    Класс для работы с БД PostgreSQL
    """

    def __init__(self, database_name: str):
        self.database_name = database_name
        self.__params = self.get_params(PARAM_FILE_NAME, SECTION)

    @staticmethod
    def get_params(filename: str, section: str) -> dict:
        """ Метод создает словарь с параметрами из файла database.ini для коннекта с БД"""
        # create a parser
        parser = ConfigParser()
        # read config file
        parser.read(filename)
        db = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception(
                'Section {0} is not found in the {1} file.'.format(section, filename))
        return db

    def create_database(self):
        """Создание базы данных и таблиц для сохранения данных о компаниях и вакансиях"""
        conn = psycopg2.connect(dbname='postgres', **self.__params)
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute(f"DROP DATABASE IF EXISTS {self.database_name}")
        cur.execute(f"CREATE DATABASE {self.database_name}")

        cur.close()
        conn.close()

        conn = psycopg2.connect(dbname=self.database_name, **self.__params)

        with conn.cursor() as cur:
            cur.execute("""
                    CREATE TABLE employers (
                        employee_id INT PRIMARY KEY,
                        employee_name VARCHAR NOT NULL,
                        employee_url TEXT
                    )
                """)

        with conn.cursor() as cur:
            cur.execute("""
                    CREATE TABLE vacancies (
                        vacancy_id INT PRIMARY KEY,
                        employee_id INT,
                        vacancy_name VARCHAR NOT NULL,
                        salary_from INT DEFAULT 0,
                        vacancy_url TEXT,
                        FOREIGN KEY(employee_id) REFERENCES employers(employee_id)                       
                    )
                """)

        conn.commit()
        conn.close()

    def save_data_to_database(self, data: HhAPI):
        """Сохранение данных о компаниях и вакансиях в базу данных"""
        conn = psycopg2.connect(dbname=self.database_name, **self.__params)

        with conn.cursor() as cur:
            # Заполняем таблицу с компаниями
            for employee in data.employers:
                cur.execute(
                    """
                    INSERT INTO employers (employee_id, employee_name, employee_url)
                    VALUES (%s, %s, %s)
                    """,
                    (employee['id'], employee['name'], employee['url'])
                )
            # Заполняем таблицу с вакансиями
            for vacancy in data.vacancies:
                salary_from = vacancy.get('salary').get('from', 0) if vacancy.get('salary') else 0
                cur.execute(
                    """
                    INSERT INTO vacancies (vacancy_id, employee_id, vacancy_name, salary_from, vacancy_url)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (vacancy['id'], vacancy['employer']['id'], vacancy['name'],
                     salary_from, vacancy['url'])
                )

        conn.commit()
        conn.close()

    def get_companies_and_vacancies_count(self):
        """
        Метод получает список всех компаний и количество вакансий у каждой компании
        :return:
        """
        conn = psycopg2.connect(dbname=self.database_name, **self.__params)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT employers.employee_id, employers.employee_name, COUNT(*) AS num_vac
                FROM employers
                JOIN vacancies USING (employee_id)
                GROUP BY employee_id
                """
            )
            rows = cur.fetchall()
            for row in rows:
                print(row)

        conn.close()

    def get_all_vacancies(self):
        """
        Метод получает список всех вакансий с указанием названия компании, названия вакансии и зарплаты
        и ссылки на вакансию
        :return:
        """
        conn = psycopg2.connect(dbname=self.database_name, **self.__params)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT vacancies.vacancy_id, employers.employee_name, vacancies.vacancy_name,
                vacancies.salary_from, vacancies.vacancy_url
                FROM employers
                JOIN vacancies USING (employee_id)
                """
            )
            rows = cur.fetchall()
            for row in rows:
                print(row)

        conn.close()

    def get_avg_salary(self):
        """
        Метод получает среднюю зарплату по вакансиям
        :return:
        """
        conn = psycopg2.connect(dbname=self.database_name, **self.__params)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT employers.employee_id, employers.employee_name,
                AVG(vacancies.salary_from) AS avg_salary
                FROM employers INNER JOIN vacancies USING (employee_id)
                WHERE salary_from <> 0
                GROUP BY employee_id
                """
            )
            rows = cur.fetchall()
            for row in rows:
                print(row)

        conn.close()

    def get_vacancies_with_higher_salary(self):
        """
        Метод получает список всех вакансий, у которых зарплата выше
        средней по всем вакансиям
        :return:
        """
        conn = psycopg2.connect(dbname=self.database_name, **self.__params)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT vacancies.vacancy_id, employers.employee_name, vacancies.vacancy_name,
                vacancies.salary_from, vacancies.vacancy_url
                FROM employers
                JOIN vacancies USING (employee_id)
                WHERE vacancies.salary_from > (SELECT AVG(salary_from) FROM vacancies WHERE salary_from <> 0)
                """
            )
            rows = cur.fetchall()
            for row in rows:
                print(row)

        conn.close()

    def get_vacancies_with_keyword(self, input_word: str):
        """
        Метод получает список всех вакансий, в названии которых
        содержатся переданные в метод слова
        :return:
        """
        conn = psycopg2.connect(dbname=self.database_name, **self.__params)

        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT vacancies.vacancy_id, employers.employee_name, vacancies.vacancy_name,
                vacancies.salary_from, vacancies.vacancy_url
                FROM employers
                JOIN vacancies USING (employee_id)
                WHERE vacancies.vacancy_name LIKE '%{input_word}%'
                """
            )
            rows = cur.fetchall()
            for row in rows:
                print(row)

        conn.close()
