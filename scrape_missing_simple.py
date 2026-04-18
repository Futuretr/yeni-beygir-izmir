"""
Eksik sonuçları TEK TEK çek - robust version
Her tarihi tek tek çeker, hata olsa bile devam eder
"""
import sys
sys.path.append('c:\\Users\\emir\\Desktop\\HorseRacingAPI-master')

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
import django
django.setup()

import json
from datetime import datetime
from main.scrappers.page import ResultScrapper
from main.enums import City
import time

# Fix console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Eksik tarihleri yükle
with open(r"E:\data\eksik_sonuclar.json", 'r', encoding='utf-8') as f:
    eksik_detay = json.load(f)

# Tüm eksik tarihleri listeye çevir
tum_gorevler = []
for city, dates in eksik_detay.items():
    for date_info in dates:
        date_str = date_info['date']
        race_count = date_info['race_count']
        tum_gorevler.append({
            'city': city,
            'date': date_str,
            'race_count': race_count
        })

print("=" * 80)
print(f"📊 Toplam {len(tum_gorevler)} tarih çekilecek")
print("=" * 80)

def save_data(city, year, month, day, data):
    """Veriyi kaydet"""
    output_dir = r"E:\data\sonuclar"
    city_dir = os.path.join(output_dir, city)
    year_dir = os.path.join(city_dir, str(year))
    os.makedirs(year_dir, exist_ok=True)
    
    filename = os.path.join(year_dir, f"{month:02d}.json")
    
    # Eğer dosya varsa, içeriği yükle
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except:
                existing_data = {}
    else:
        existing_data = {}
    
    # Günü ekle
    date_key = f"{year}-{month:02d}-{day:02d}"
    existing_data[date_key] = data
    
    # Kaydet
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

basarili = 0
basarisiz = 0
bos = 0
start_time = time.time()

for i, task in enumerate(tum_gorevler, 1):
    city = task['city']
    date_str = task['date']
    race_count = task['race_count']
    
    try:
        # Tarih objesine çevir
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # City enum'a çevir
        city_enum = City[city]
        
        # ResultScrapper ile çek
        scrapper = ResultScrapper.scrap_by_date(city_enum, date_obj)
        result = scrapper.serialize()
        
        if result and len(result) > 0:
            # Toplam kayıt sayısını hesapla
            total_records = sum(len(race_data) for race_data in result.values())
            
            # Kaydet
            save_data(city, date_obj.year, date_obj.month, date_obj.day, result)
            
            basarili += 1
            
            if total_records != race_count:
                print(f"{i}/{len(tum_gorevler)} ⚠️  {city} {date_str}: {total_records}/{race_count} yarış", flush=True)
            elif i % 10 == 0:
                print(f"{i}/{len(tum_gorevler)} ✅ {city} {date_str}: {total_records} yarış", flush=True)
        else:
            bos += 1
            print(f"{i}/{len(tum_gorevler)} ⚫ {city} {date_str}: Boş", flush=True)
            
    except Exception as e:
        basarisiz += 1
        print(f"{i}/{len(tum_gorevler)} ❌ {city} {date_str}: {str(e)[:80]}", flush=True)
    
    # Her 50 tanesinde özet
    if i % 50 == 0:
        elapsed = time.time() - start_time
        rate = i / elapsed if elapsed > 0 else 0
        print(f"\n📊 {i}/{len(tum_gorevler)} - ✅ {basarili} | ⚫ {bos} | ❌ {basarisiz} | Hız: {rate:.1f} tarih/s\n", flush=True)
    
    # Rate limiting
    time.sleep(0.5)

# Final rapor
elapsed = time.time() - start_time
print("\n" + "=" * 80)
print("✅ ÇEKME TAMAMLANDI")
print("=" * 80)
print(f"Süre: {elapsed/60:.1f} dakika")
print(f"Başarılı: {basarili}")
print(f"Boş: {bos}")
print(f"Başarısız: {basarisiz}")
print(f"Hız: {(basarili + basarisiz + bos) / elapsed:.2f} tarih/s")
print("\nŞimdi master_sonuclar.parquet dosyasını yeniden oluştur!")
