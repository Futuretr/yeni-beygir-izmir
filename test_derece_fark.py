"""
Derece ve Fark çekme testi
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

# 10 Ocak 2026 İstanbul sonuçlarını çek
print("🔍 10 Ocak 2026 İstanbul sonuçları çekiliyor...")
scrapper = ResultScrapper.scrap_by_date(City.Istanbul, datetime(2026, 1, 10))
result = scrapper.serialize()

if result:
    # İlk yarışın ilk 3 atını göster
    first_race_key = list(result.keys())[0]
    first_race = result[first_race_key]
    
    print(f"\n✅ {len(result)} yarış bulundu\n")
    print("📊 İLK YARIŞIN İLK 3 ATI:")
    print("=" * 100)
    
    for i, horse in enumerate(first_race[:3], 1):
        print(f"\n{i}. {horse['horse_name']}")
        print(f"   Derece (time): {horse.get('time', 'YOK!')}")
        print(f"   Fark:          {horse.get('fark', 'YOK!')}")
        print(f"   Ganyan:        {horse.get('ganyan', '-')}")
        print(f"   AGF:           {horse.get('agf', '-')}")
else:
    print("❌ Sonuç bulunamadı")
