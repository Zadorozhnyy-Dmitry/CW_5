from config import ID_EMPLOYERS_LIST, DATA_BASE_NAME
from src.api import HhAPI
from src.dbmanager import DBManager


def main():
    # инициализируем обращению к API HH.ru
    hh = HhAPI()
    # Задаем список id компаний
    hh.employers_id_list = ID_EMPLOYERS_LIST
    # Загружаем данные по вакансиям
    hh.load_vacancies()
    # инициализируем управление БД
    db_manager = DBManager(DATA_BASE_NAME)
    # создаем базу данных с таблицами
    db_manager.create_database()
    # заполняем таблицу данными
    db_manager.save_data_to_database(hh)
    # Интерфейс работы с юзером

    dict_functions: dict = {
        '1': db_manager.get_companies_and_vacancies_count,
        '2': db_manager.get_all_vacancies,
        '3': db_manager.get_avg_salary,
        '4': db_manager.get_vacancies_with_higher_salary,
    }

    user_choice: str = ''
    while user_choice != 'exit':
        user_choice = input(
            """
            Введите цифру от 1 до 4 или ключевое слово для поиска
            Для выхода из программы наберите 'exit'
            1 - получить список всех компаний и количество вакансий у каждой компании
            2 - получить список всех вакансий
            3 - получить среднюю зарплату по вакансиям
            4 - получить список вакансий, у которых зарплата выше средней
            '***' - получить список всех вакансий, с указанным словом
            """
        ).lower()

        if dict_functions.get(user_choice):
            dict_functions[user_choice]()
        else:
            db_manager.get_vacancies_with_keyword(user_choice)


if __name__ == '__main__':
    main()
