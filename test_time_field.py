"""
TJK sonuç sayfasında YARIŞ SÜRESİ (derece) var mı kontrol et
"""
import sys
sys.path.append('c:\\Users\\emir\\Desktop\\HorseRacingAPI-master')

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
import django
django.setup()

from datetime import datetime
from main.scrappers.page import ResultScrapper
from main.enums import City

# Test: Son bir günü çek ve HTML'e bak
scrapper = ResultScrapper.scrap_by_date(City.Istanbul, datetime(2026, 1, 30))

# HTML'i kaydet
with open('test_result_html.html', 'w', encoding='utf-8') as f:
    f.write(str(scrapper.soup))

print("✅ HTML kaydedildi: test_result_html.html")
print("🔍 Şimdi dosyada 'derece', 'süre', 'time', '1.' ara")

# İlk yarışın sonuçlarını serialize et
result = scrapper.serialize()
if result:
    print(f"\n📊 {len(result)} yarış bulundu")
    if len(result) > 0:
        first_race = list(result.values())[0]
        if len(first_race) > 0:
            first_horse = first_race[0]
            print("\n🏇 İLK ATIN VERİLERİ:")
            for key, value in first_horse.items():
                print(f"  {key:20s} = {value}")
