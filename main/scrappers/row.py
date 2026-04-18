# -*- coding: utf-8 -*-
# The above line is for turkish characters in comments, unless it is there a encoding error is raised in the server

from main.enums import PageType
from .abstract import BaseRaceDayRowScrapper


class FixtureRowScrapper(BaseRaceDayRowScrapper):
    """
    Ex: <td class="gunluk-GunlukYarisProgrami-AtAdi">
    """
    horse_name_class_name = "AtAdi"
    td_class_base = 'gunluk-GunlukYarisProgrami-'
    page_type = PageType.Fixture

    def get(self):
        fixture = super(FixtureRowScrapper, self).get()
        # No additional processing needed for fixture
        return fixture


class ResultRowScrapper(BaseRaceDayRowScrapper):
    """
    Ex: <td class="gunluk-GunlukYarisProgrami-AtAdi3">
    """
    horse_name_class_name = "AtAdi3"
    td_class_base = 'gunluk-GunlukYarisSonuclari-'
    page_type = PageType.Result

    def get(self):
        result = super(ResultRowScrapper, self).get()

        # Horses name still has the order that horse started the race in the first place.
        # Example "KARAHİNDİBAYA (7)" - clean it
        if "(" in result.horse_name:
            result.horse_name = result.horse_name.split("(")[0].strip()

        return result

