from abc import ABC, abstractmethod
from json import JSONDecodeError

import requests

from requests import Response

from config import HH_URL, ID_EMPLOYERS_LIST
from src.exceptions import HhAPIException


class API(ABC):
    """
    Абстрактный класс для взаимодействия с интерфейсом API
    """

    @abstractmethod
    def _get_response(self) -> Response:
        """
        Абстрактный метод получает объект Response с помощью метода get из библиотеки request
        :return:
        """
        pass

    @staticmethod
    @abstractmethod
    def _check_status(response: Response) -> bool:
        """
        Абстрактный метод проверяет статус запроса метода get из библиотеки request
        :return:
        """
        pass

    @abstractmethod
    def get_response_data(self) -> dict:
        """
        Абстрактный метод преобразует Response в json
        :return:
        """
        pass


class HhAPI(API):
    """
    Класс для работы с API HeadHunter
    """

    def __init__(self):
        self.__url: str = HH_URL
        self.__params: dict = {
            'page': 0,
            'per_page': 100,
            'area': 113,
        }
        self.__employers_id_list: list[str] | None = None
        self.vacancies: list = []
        self.employers: list = []

    @property
    def employers_id_list(self) -> list[str]:
        """
        доступ к атрибуту со списками компаний
        :return:
        """
        return self.__employers_id_list

    @employers_id_list.setter
    def employers_id_list(self, id_list: list[str]) -> None:
        """
        Сеттер для атрибута employers_id_list
        :param id_list:
        :return:
        """
        if id_list:
            self.__employers_id_list = id_list

    def _get_response(self) -> Response:
        """
        Метод получает объект Response со списком вакансий с ресурса hh
        :return:
        """
        if self.__employers_id_list is None:
            raise HhAPIException('Поисковый запрос не задан')

        self.__params['employer_id'] = self.employers_id_list
        return requests.get(self.__url, params=self.__params)

    @staticmethod
    def _check_status(response: Response) -> bool:
        """
        Метод проверяет статус запроса request
        :param response:
        :return: если код 200 возвращает True
        """
        return response.status_code == 200

    def get_response_data(self) -> dict:
        """
        Метод работает с Response:
        если статус соединения с сервером 200
        - проверяет полученный response и преобразует его в json
        :return:
        """
        response = self._get_response()
        is_connect = self._check_status(response)
        if not is_connect:
            raise HhAPIException('Ошибка соединения с сервером hh')
        try:
            return response.json()
        except JSONDecodeError:
            raise HhAPIException('Ошибка получения данных, получен не json объект')

    def load_vacancies(self) -> None:
        """
        Метод обрабатывает все страницы запроса по вакансиям и передает список вакансий в атрибут класса
        так же передает список компаний в атрибут класса
        :return:
        """
        numbers_pages: int = self.get_response_data()['pages']
        for i in range(numbers_pages):
            self.__params['page'] = i
            vacancies: list[dict] = self.get_response_data()['items']
            self.vacancies.extend(vacancies)
            for vacancy in vacancies:
                employee: dict = vacancy['employer']
                if employee not in self.employers:
                    self.employers.append(employee)
