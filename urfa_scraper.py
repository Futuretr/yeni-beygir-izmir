"""
Şanlıurfa (Urfa) için özel scraper - Haziran 2025'ten bugüne
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

# Only Urfa
CITY = "Urfa"

# Date range
END_DATE = datetime(2026, 1, 30)
START_DATE = datetime(2021, 1, 1)

# Output directory
OUTPUT_DIR = r"E:\data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Failed requests log file
FAILED_REQUESTS_FILE = os.path.join(OUTPUT_DIR, "urfa_failed_requests.json")

# Thread-safe counters
lock = threading.Lock()
success_count = 0
error_count = 0
processed_count = 0

MAX_WORKERS = 10
REQUEST_TIMEOUT = 30
MAX_RETRIES = 2

def scrape_race_day(year, month, day, retry_attempt=0):
    """Scrape data for a specific race day"""
    global success_count, error_count, processed_count
    
    params = {
        'city': CITY,
        'year': year,
        'month': month,
        'day': day,
        'type': 'fixture'
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
                    log_failed_request(year, month, day, 'API error response')
                    return (year, month, day, None, False)
                else:
                    with lock:
                        success_count += 1
                    print(f"✅ {CITY} {year}-{month:02d}-{day:02d}: {len(data)} koşu", flush=True)
                    return (year, month, day, data, True)
            else:
                with lock:
                    error_count += 1
                log_failed_request(year, month, day, 'Veri yok')
                return (year, month, day, None, False)
        else:
            with lock:
                error_count += 1
            log_failed_request(year, month, day, f'HTTP {response.status_code}')
            return (year, month, day, None, False)
    except Exception as e:
        error_msg = str(e)
        if retry_attempt < MAX_RETRIES and 'timeout' in error_msg.lower():
            print(f"⏰ TIMEOUT: {year}-{month:02d}-{day:02d} - Tekrar deneniyor...", flush=True)
            time.sleep(2)
            return scrape_race_day(year, month, day, retry_attempt + 1)
        else:
            with lock:
                error_count += 1
            log_failed_request(year, month, day, f'Hata: {error_msg}')
            return (year, month, day, None, False)

def save_data(year, month, day, data):
    """Save data to JSON file"""
    city_dir = os.path.join(OUTPUT_DIR, CITY)
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

def log_failed_request(year, month, day, reason):
    """Log failed request to file"""
    failed_entry = {
        'city': CITY,
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
    """Main scraping function"""
    global success_count, error_count, processed_count
    
    # Generate all dates
    all_dates = []
    current_date = START_DATE
    while current_date <= END_DATE:
        all_dates.append(current_date)
        current_date += timedelta(days=1)
    
    total_tasks = len(all_dates)
    
    print(f"🐎 ŞANLIURFA (URFA) VERİ ÇEKİCİ")
    print(f"Tarih aralığı: {START_DATE.date()} → {END_DATE.date()}")
    print(f"Toplam gün: {total_tasks}")
    print(f"Worker sayısı: {MAX_WORKERS}")
    print(f"Çıktı dizini: {os.path.abspath(OUTPUT_DIR)}")
    print("-" * 80)
    
    start_time = time.time()
    
    # Create tasks
    tasks = [(date.year, date.month, date.day) for date in all_dates]
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {executor.submit(scrape_race_day, *task): task for task in tasks}
        
        for future in as_completed(future_to_task):
            year, month, day, data, success = future.result()
            
            if success and data:
                save_data(year, month, day, data)
            
            del future, year, month, day, data, success
            
            if processed_count % 50 == 0:
                elapsed = time.time() - start_time
                progress = (processed_count / total_tasks) * 100
                rate = processed_count / elapsed if elapsed > 0 else 0
                eta = (total_tasks - processed_count) / rate if rate > 0 else 0
                print(f"İlerleme: {progress:.1f}% ({processed_count}/{total_tasks}) | "
                      f"Hız: {rate:.1f} istek/sn | Kalan: {eta/60:.1f} dk", flush=True)
        
        del future_to_task
    
    gc.collect()
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"✅ ŞANLIURFA VERİ ÇEKİMİ TAMAMLANDI!")
    print(f"Başarılı: {success_count}")
    print(f"Hata/Boş: {error_count}")
    print(f"Toplam süre: {elapsed/60:.1f} dakika")
    print(f"Ortalama hız: {total_tasks/elapsed:.1f} istek/saniye")
    print(f"Veri dizini: {os.path.abspath(os.path.join(OUTPUT_DIR, CITY))}")
    if os.path.exists(FAILED_REQUESTS_FILE):
        print(f"Başarısız istekler: {os.path.abspath(FAILED_REQUESTS_FILE)}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
