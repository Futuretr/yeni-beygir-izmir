"""
Eksik sonuçları nokta atışı olarak çek
Sadece eksik tarihleri çeker, gereksiz istekler yapmaz
Django servisine bağımlı değil, direkt scraper kullanır
"""
import sys
sys.path.append('c:\\Users\\emir\\Desktop\\HorseRacingAPI-master')

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
import django
django.setup()

import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from main.scrappers.page import ResultScrapper
from main.enums import City
import time
import threading

# Thread-safe counter
lock = threading.Lock()
basarili = 0
basarisiz = 0
bos = 0

print("=" * 80)
print("🎯 EKSİK SONUÇLARI NOKTA ATIŞI ÇEK")
print("=" * 80)

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

print(f"\n📊 Toplam {len(tum_gorevler)} tarih çekilecek")
print(f"Toplam ~{sum(g['race_count'] for g in tum_gorevler)} yarış bekleniyor")

# Şehir bazında özet
city_counts = {}
for gorev in tum_gorevler:
    city = gorev['city']
    city_counts[city] = city_counts.get(city, 0) + 1

print("\nŞehir bazında:")
for city, count in sorted(city_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {city}: {count} gün")

input("\nDevam etmek için Enter'a bas...")

# Scraping fonksiyonu
def scrape_result(task):
    """Tek bir tarihin sonucunu çek"""
    global basarili, basarisiz, bos
    
    city = task['city']
    date_str = task['date']
    race_count = task['race_count']
    
    try:
        # Tarih objesine çevir
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # City enum'a çevir
        try:
            city_enum = City[city]
        except KeyError:
            with lock:
                basarisiz += 1
            return {
                'status': 'error',
                'city': city,
                'date': date_str,
                'expected': race_count,
                'error': f'Bilinmeyen şehir: {city}'
            }
        
        # ResultScrapper ile çek
        scrapper = ResultScrapper.scrap_by_date(city_enum, date_obj)
        result = scrapper.serialize()
        
        if result and len(result) > 0:
            # Toplam kayıt sayısını hesapla
            total_records = sum(len(race_data) for race_data in result.values())
            
            # Kaydet
            save_data(city, date_obj.year, date_obj.month, date_obj.day, result)
            
            with lock:
                basarili += 1
            
            return {
                'status': 'success',
                'city': city,
                'date': date_str,
                'expected': race_count,
                'actual': total_records
            }
        else:
            with lock:
                bos += 1
            return {
                'status': 'empty',
                'city': city,
                'date': date_str,
                'expected': race_count,
                'actual': 0,
                'message': 'Veri bulunamadı'
            }
            
    except Exception as e:
        with lock:
            basarisiz += 1
        return {
            'status': 'error',
            'city': city,
            'date': date_str,
            'expected': race_count,
            'error': str(e)
        }

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
    
    # Günü ekle - key formatı: "YYYY-MM-DD"
    date_key = f"{year}-{month:02d}-{day:02d}"
    existing_data[date_key] = data
    
    # Kaydet
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

# Paralel çekme
MAX_WORKERS = 15  # Daha az worker - stabilite için
BATCH_SIZE = 50  # Daha küçük batch - daha sık feedback

print("\n" + "=" * 80)
print(f"🚀 Çekme başlıyor... ({MAX_WORKERS} worker, {BATCH_SIZE} batch)")
print("=" * 80)

basarili = 0
basarisiz = 0
bos = 0
start_time = time.time()

for batch_start in range(0, len(tum_gorevler), BATCH_SIZE):
    batch_end = min(batch_start + BATCH_SIZE, len(tum_gorevler))
    batch = tum_gorevler[batch_start:batch_end]
    
    print(f"\n📦 Batch {batch_start//BATCH_SIZE + 1}/{(len(tum_gorevler)-1)//BATCH_SIZE + 1} " 
          f"({batch_start+1}-{batch_end}/{len(tum_gorevler)})")
    
    batch_basarili = 0
    batch_basarisiz = 0
    batch_bos = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(scrape_result, task): task for task in batch}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                
                if result['status'] == 'success':
                    batch_basarili += 1
                    if result['actual'] != result['expected']:
                        print(f"  ⚠️  {result['city']} {result['date']}: {result['actual']}/{result['expected']} yarış")
                elif result['status'] == 'empty':
                    batch_bos += 1
                    print(f"  ⚫ {result['city']} {result['date']}: Boş")
                else:
                    batch_basarisiz += 1
                    print(f"  ❌ {result['city']} {result['date']}: {result.get('error', 'Bilinmeyen hata')[:50]}")
            except Exception as e:
                batch_basarisiz += 1
                print(f"  ❌ Future hatası: {str(e)[:50]}")
    
    # Batch özeti
    elapsed = time.time() - start_time
    rate = (basarili + basarisiz + bos) / elapsed if elapsed > 0 else 0
    print(f"\n  Batch: ✅ {batch_basarili} | ⚫ {batch_bos} | ❌ {batch_basarisiz}")
    print(f"  Toplam: ✅ {basarili} | ⚫ {bos} | ❌ {basarisiz} | Hız: {rate:.1f} tarih/s")
    
    # Rate limiting - TJK sitesine saygılı olalım
    time.sleep(2)

# Final rapor
elapsed = time.time() - start_time
print("\n" + "=" * 80)
print("✅ ÇEKME TAMAMLANDI")
print("=" * 80)
print(f"Süre: {elapsed/60:.1f} dakika")
print(f"Başarılı: {basarili}")
print(f"Boş: {bos}")
print(f"Başarısız: {basarisiz}")
print(f"Hız: {(basarili + basarisiz + bos) / elapsed:.1f} tarih/s")
print("\nŞimdi master_sonuclar.parquet dosyasını yeniden oluşturmalısın!")
