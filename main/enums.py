from enum import Enum
import importlib


class PageType(Enum):
    """
    Cities and their are respected ids determined by TJK.org for their query parameters
    """
    Fixture = 'F'
    Result = 'R'
    Horse = 'H'

    @property
    def scrapper(self):
        scrapper_module = importlib.import_module("scrappers.page")
        return getattr(scrapper_module, '{0}Scrapper'.format(self.name))

    @property
    def model(self):
        model_module = importlib.import_module("scrappers.models")
        return getattr(model_module, self.name)


class City(Enum):
    """
    Cities and their are respected ids determined by TJK.org for their query parameters
    Updated for 2026 TJK.org structure
    """
    Adana = 1
    Izmir = 2
    Istanbul = 3
    Bursa = 4
    Ankara = 5
    Urfa = 6
    Elazig = 7
    Diyarbakir = 8
    Kocaeli = 9
    Antalya = 10  # 12. Yarış Günü


class ManagerType(Enum):
    """
    The class of the columns in the each race table
    """
    Jockey = 'JokeAdi'
    Owner = 'SahipAdi'
    Trainer = 'AntronorAdi'