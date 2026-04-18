"""
Result (Sonuç) sayfalarını hızlıca çek - 30 worker
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

# Turkish cities
CITIES = [
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

# Failed requests log file
FAILED_REQUESTS_FILE = os.path.join(OUTPUT_DIR, "failed_requests.json")

# Thread-safe counters
lock = threading.Lock()
success_count = 0
error_count = 0
processed_count = 0

MAX_WORKERS = 30
REQUEST_TIMEOUT = 30
BATCH_SIZE = 1000  # Process in batches

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
                    log_failed_request(city, year, month, day, 'API error')
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
                log_failed_request(city, year, month, day, 'No data')
                return (city, year, month, day, None, False)
        else:
            with lock:
                error_count += 1
            log_failed_request(city, year, month, day, f'HTTP {response.status_code}')
            return (city, year, month, day, None, False)
    except Exception as e:
        with lock:
            error_count += 1
        log_failed_request(city, year, month, day, str(e))
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

def log_failed_request(city, year, month, day, reason):
    """Log failed request"""
    failed_entry = {
        'city': city,
        'year': year,
        'month': month,
        'day': day,
        'reason': reason,
        'timestamp': datetime.now().isoformat()
    }
    
    with lock:
        if os.path.exists(FAILED_REQUESTS_FILE):
            with open(FAILED_REQUESTS_FILE, 'r', encoding='utf-8') as f:
                try:
                    failed_list = json.load(f)
                except:
                    failed_list = []
        else:
            failed_list = []
        
        failed_list.append(failed_entry)
        
        with open(FAILED_REQUESTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(failed_list, f, ensure_ascii=False, indent=2)

def main():
    """Main scraping function with batch processing"""
    global success_count, error_count, processed_count
    
    # Generate all dates
    all_dates = []
    current_date = START_DATE
    while current_date <= END_DATE:
        all_dates.append(current_date)
        current_date += timedelta(days=1)
    
    total_dates = len(all_dates)
    total_tasks = total_dates * len(CITIES)
    
    print(f"🏁 SONUÇ SAYFALARINI HIZLICA ÇEK")
    print(f"Tarih aralığı: {START_DATE.date()} → {END_DATE.date()}")
    print(f"Toplam gün: {total_dates} | Şehir: {len(CITIES)}")
    print(f"Toplam istek: {total_tasks}")
    print(f"Worker: {MAX_WORKERS} | Batch: {BATCH_SIZE}")
    print(f"Çıktı: {OUTPUT_DIR}")
    print("-" * 80)
    
    start_time = time.time()
    
    # Process in batches
    for batch_start in range(0, total_dates, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_dates)
        batch_dates = all_dates[batch_start:batch_end]
        
        batch_tasks = []
        for date in batch_dates:
            for city in CITIES:
                batch_tasks.append((city, date.year, date.month, date.day))
        
        batch_num = (batch_start // BATCH_SIZE) + 1
        total_batches = (total_dates + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\n🔄 Batch {batch_num}/{total_batches} ({len(batch_tasks)} task)...", flush=True)
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_task = {executor.submit(scrape_race_day, *task): task for task in batch_tasks}
            
            for future in as_completed(future_to_task):
                city, year, month, day, data, success = future.result()
                
                if success and data:
                    save_data(city, year, month, day, data)
                
                del future, city, year, month, day, data, success
                
                if processed_count % 500 == 0:
                    elapsed = time.time() - start_time
                    progress = (processed_count / total_tasks) * 100
                    rate = processed_count / elapsed if elapsed > 0 else 0
                    eta = (total_tasks - processed_count) / rate if rate > 0 else 0
                    print(f"İlerleme: {progress:.1f}% ({processed_count}/{total_tasks}) | "
                          f"Hız: {rate:.1f} req/s | Kalan: {eta/60:.1f} dk", flush=True)
            
            del future_to_task
        
        del batch_tasks, batch_dates
        gc.collect()
        print(f"✅ Batch {batch_num} tamamlandı", flush=True)
    
    elapsed = time.time() - start_time
    gc.collect()
    
    print(f"\n{'='*80}")
    print(f"✅ SONUÇ SAYFALARI ÇEKİMİ TAMAMLANDI!")
    print(f"Başarılı: {success_count}")
    print(f"Başarısız/Boş: {error_count}")
    print(f"Toplam süre: {elapsed/60:.1f} dakika")
    print(f"Ortalama hız: {total_tasks/elapsed:.1f} istek/saniye")
    print(f"Veri dizini: {os.path.abspath(OUTPUT_DIR)}")
    if os.path.exists(FAILED_REQUESTS_FILE):
        print(f"Başarısız: {os.path.abspath(FAILED_REQUESTS_FILE)}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
