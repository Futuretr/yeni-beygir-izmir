"""
Result (Sonuç) sayfalarını şehir şehir hızlıca çek - 30 worker
Kullanım: python result_scraper_city.py Istanbul
"""
import requests
import json
import time
from datetime import datetime, timedelta
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import gc

# Fix console encoding for Turkish characters on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# API endpoint
API_URL = "http://127.0.0.1:8000/race_day"

# All available cities
AVAILABLE_CITIES = [
    "Istanbul",
    "Ankara", 
    "Izmir",
    "Adana",
    "Bursa",
    "Kocaeli",
    "Urfa",
    "Elazig",
    "Diyarbakir",
    "Antalya"
]

# Date range
END_DATE = datetime(2026, 1, 30)
START_DATE = datetime(2021, 1, 1)

# Output directory - sonuclar klasörü
OUTPUT_DIR = r"E:\data\sonuclar"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Thread-safe counters
lock = threading.Lock()
success_count = 0
error_count = 0
processed_count = 0

MAX_WORKERS = 15
REQUEST_TIMEOUT = 30

def scrape_race_day(city, year, month, day):
    """Scrape RESULT data for a specific race day"""
    global success_count, error_count, processed_count
    
    params = {
        'city': city,
        'year': year,
        'month': month,
        'day': day,
        'type': 'result'  # RESULT sayfası
    }
    
    try:
        response = requests.get(API_URL, params=params, timeout=REQUEST_TIMEOUT)
        
        with lock:
            processed_count += 1
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data:
                if 'error' in data or 'detail' in data or 'message' in data or 'status_code' in data:
                    with lock:
                        error_count += 1
                    return (city, year, month, day, None, False)
                else:
                    with lock:
                        success_count += 1
                    if success_count % 100 == 0:
                        print(f"✅ {city} {year}-{month:02d}-{day:02d}: {len(data)} koşu", flush=True)
                    return (city, year, month, day, data, True)
            else:
                with lock:
                    error_count += 1
                return (city, year, month, day, None, False)
        else:
            with lock:
                error_count += 1
            return (city, year, month, day, None, False)
    except Exception as e:
        with lock:
            error_count += 1
        return (city, year, month, day, None, False)

def save_data(city, year, month, day, data):
    """Save data to JSON file"""
    city_dir = os.path.join(OUTPUT_DIR, city)
    year_dir = os.path.join(city_dir, str(year))
    os.makedirs(year_dir, exist_ok=True)
    
    filename = os.path.join(year_dir, f"{month:02d}.json")
    
    with lock:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = {}
        
        existing_data[f"{day:02d}"] = data
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

def main(city):
    """Main scraping function for one city"""
    global success_count, error_count, processed_count
    
    # Generate all dates
    all_dates = []
    current_date = START_DATE
    while current_date <= END_DATE:
        all_dates.append(current_date)
        current_date += timedelta(days=1)
    
    total_tasks = len(all_dates)
    
    print(f"🏁 {city.upper()} SONUÇ SAYFALARINI ÇEK")
    print(f"Tarih aralığı: {START_DATE.date()} → {END_DATE.date()}")
    print(f"Toplam gün: {total_tasks}")
    print(f"Worker: {MAX_WORKERS}")
    print(f"Çıktı: {OUTPUT_DIR}\\{city}")
    print("-" * 80)
    
    start_time = time.time()
    
    # Create tasks for this city
    tasks = [(city, date.year, date.month, date.day) for date in all_dates]
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {executor.submit(scrape_race_day, *task): task for task in tasks}
        
        for future in as_completed(future_to_task):
            c, year, month, day, data, success = future.result()
            
            if success and data:
                save_data(c, year, month, day, data)
            
            del future, c, year, month, day, data, success
            
            if processed_count % 100 == 0:
                elapsed = time.time() - start_time
                progress = (processed_count / total_tasks) * 100
                rate = processed_count / elapsed if elapsed > 0 else 0
                eta = (total_tasks - processed_count) / rate if rate > 0 else 0
                print(f"İlerleme: {progress:.1f}% ({processed_count}/{total_tasks}) | "
                      f"Hız: {rate:.1f} req/s | Kalan: {eta/60:.1f} dk", flush=True)
        
        del future_to_task
    
    elapsed = time.time() - start_time
    gc.collect()
    
    print(f"\n{'='*80}")
    print(f"✅ {city.upper()} SONUÇ SAYFALARI TAMAMLANDI!")
    print(f"Başarılı: {success_count}")
    print(f"Başarısız/Boş: {error_count}")
    print(f"Toplam süre: {elapsed/60:.1f} dakika")
    print(f"Ortalama hız: {total_tasks/elapsed:.1f} istek/saniye")
    print(f"Veri dizini: {os.path.abspath(os.path.join(OUTPUT_DIR, city))}")
    print(f"{'='*80}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n❌ Şehir adı belirtmelisiniz!")
        print("\n📋 Kullanılabilir şehirler:")
        for i, city in enumerate(AVAILABLE_CITIES, 1):
            print(f"  {i}. {city}")
        print("\n💡 Kullanım: python result_scraper_city.py Istanbul")
        print("💡 Örnek: python result_scraper_city.py Ankara")
        sys.exit(1)
    
    city_name = sys.argv[1]
    
    # Check if city is valid
    if city_name not in AVAILABLE_CITIES:
        print(f"\n❌ Geçersiz şehir: {city_name}")
        print("\n📋 Kullanılabilir şehirler:")
        for i, city in enumerate(AVAILABLE_CITIES, 1):
            print(f"  {i}. {city}")
        sys.exit(1)
    
    main(city_name)
