"""
SADECE TIME VE FARK ÇEK - Minimal Scraper
Horse_id, race_id, time, fark - hepsi bu kadar!
"""
import sys
sys.path.append('c:\\Users\\emir\\Desktop\\HorseRacingAPI-master')

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
import django
django.setup()

import json
from datetime import datetime, timedelta
from main.scrappers.page import ResultScrapper
from main.enums import City
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# HANGİ ŞEHİR? (Komut satırından al)
if len(sys.argv) < 2:
    print("KULLANIM: python scrape_time_fark_only.py <sehir_adi>")
    print("\nMevcut şehirler:")
    print("  Istanbul, Ankara, Izmir, Bursa, Adana, Antalya, Kocaeli, Elazig, Urfa, Diyarbakir")
    sys.exit(1)

CITY_NAME = sys.argv[1]

# Şehir enum
CITY_MAP = {
    'Istanbul': City.Istanbul,
    'Ankara': City.Ankara,
    'Izmir': City.Izmir,
    'Bursa': City.Bursa,
    'Adana': City.Adana,
    'Antalya': City.Antalya,
    'Kocaeli': City.Kocaeli,
    'Elazig': City.Elazig,
    'Urfa': City.Urfa,
    'Diyarbakir': City.Diyarbakir
}

if CITY_NAME not in CITY_MAP:
    print(f"❌ Hatalı şehir: {CITY_NAME}")
    print(f"Mevcut şehirler: {', '.join(CITY_MAP.keys())}")
    sys.exit(1)

CITY_ENUM = CITY_MAP[CITY_NAME]

# Tarih aralığı
START_DATE = datetime(2021, 1, 1)
END_DATE = datetime(2026, 1, 30)

# Output dosyası (şehir bazında - E:\data\time klasörüne)
OUTPUT_FILE = rf"E:\data\time\time_fark_{CITY_NAME}.json"

print("=" * 80)
print(f"⚡ {CITY_NAME} - TIME VE FARK ÇEKME")
print("=" * 80)
print(f"📅 Tarih: {START_DATE.date()} - {END_DATE.date()}")
print(f"🏙️  Şehir: {CITY_NAME}")
print(f"💾 Output: {OUTPUT_FILE}")
print()

def scrape_minimal(date_obj):
    """Sadece horse_id, race_id, time, fark çek"""
    try:
        scrapper = ResultScrapper.scrap_by_date(CITY_ENUM, date_obj)
        result = scrapper.serialize()
        
        if not result or len(result) == 0:
            return None
        
        # Minimal veri - sadece ihtiyacımız olanlar
        minimal_data = []
        for race_id, horses in result.items():
            for horse in horses:
                minimal_data.append({
                    'race_id': horse['race_id'],
                    'horse_id': horse['horse_id'],
                    'time': horse.get('time', ''),
                    'fark': horse.get('fark', '')
                })
        
        return {
            'date': date_obj.strftime('%Y-%m-%d'),
            'count': len(minimal_data),
            'data': minimal_data
        }
        
    except Exception as e:
        return None

# Tüm tarihleri oluştur
tasks = []
current_date = START_DATE
while current_date <= END_DATE:
    tasks.append(current_date)
    current_date += timedelta(days=1)

print(f"📦 Toplam {len(tasks):,} tarih")
print(f"🔄 Paralel çekme başlıyor (100 worker)...\n")

# Sonuçları topla
all_data = []
success = 0
empty = 0
failed = 0
start_time = time.time()

# Paralel çekme - 100 WORKER
with ThreadPoolExecutor(max_workers=100) as executor:
    # Submit all tasks
    futures = {executor.submit(scrape_minimal, date): date for date in tasks}
    
    # Process as completed
    for i, future in enumerate(as_completed(futures), 1):
        date = futures[future]
        
        try:
            result = future.result()
            
            if result:
                all_data.extend(result['data'])
                success += 1
                
                if i % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (len(tasks) - i) / rate if rate > 0 else 0
                    print(f"✅ {i:,}/{len(tasks):,} | Kayıt: {len(all_data):,} | "
                          f"Hız: {rate:.1f} tarih/s | ETA: {eta/60:.1f}dk")
            else:
                empty += 1
                
        except Exception as e:
            failed += 1

# Kaydet
print(f"\n💾 {len(all_data):,} kayıt JSON'a yazılıyor...")
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

elapsed = time.time() - start_time
print("\n" + "=" * 80)
print("✅ ÇEKME TAMAMLANDI")
print("=" * 80)
print(f"Süre: {elapsed/60:.1f} dakika")
print(f"Başarılı: {success:,}")
print(f"Boş: {empty:,}")
print(f"Hatalı: {failed:,}")
print(f"Toplam kayıt: {len(all_data):,}")
print(f"Hız: {len(tasks)/elapsed:.1f} tarih/s")
print(f"Dosya: {OUTPUT_FILE}")
