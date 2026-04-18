"""
Failed Urfa requests retry scraper
"""
import requests
import json
import time
from datetime import datetime
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Fix console encoding for Turkish characters on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# API endpoint
API_URL = "http://127.0.0.1:8000/race_day"

# Output directory
OUTPUT_DIR = r"E:\data"

# Failed requests log file
FAILED_REQUESTS_FILE = os.path.join(OUTPUT_DIR, "urfa_failed_requests.json")
RETRY_FAILED_FILE = os.path.join(OUTPUT_DIR, "urfa_retry_failed_requests.json")

# Thread-safe counters
lock = threading.Lock()
success_count = 0
error_count = 0
processed_count = 0

MAX_WORKERS = 5
REQUEST_TIMEOUT = 30

def scrape_race_day(city, year, month, day):
    """Scrape data for a specific race day"""
    global success_count, error_count, processed_count
    
    params = {
        'city': city,
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
                    return (city, year, month, day, None, False)
                else:
                    with lock:
                        success_count += 1
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

def log_failed_request(city, year, month, day, reason):
    """Log failed request to retry file"""
    failed_entry = {
        'city': city,
        'year': year,
        'month': month,
        'day': day,
        'reason': reason,
        'timestamp': datetime.now().isoformat()
    }
    
    with lock:
        if os.path.exists(RETRY_FAILED_FILE):
            with open(RETRY_FAILED_FILE, 'r', encoding='utf-8') as f:
                try:
                    failed_list = json.load(f)
                except:
                    failed_list = []
        else:
            failed_list = []
        
        failed_list.append(failed_entry)
        
        with open(RETRY_FAILED_FILE, 'w', encoding='utf-8') as f:
            json.dump(failed_list, f, ensure_ascii=False, indent=2)

def main():
    """Main retry function"""
    global success_count, error_count, processed_count
    
    # Load failed requests
    if not os.path.exists(FAILED_REQUESTS_FILE):
        print(f"❌ Failed requests dosyası bulunamadı: {FAILED_REQUESTS_FILE}")
        return
    
    with open(FAILED_REQUESTS_FILE, 'r', encoding='utf-8') as f:
        failed_requests = json.load(f)
    
    if not failed_requests:
        print("✅ Tekrar denenecek başarısız istek yok!")
        return
    
    total_tasks = len(failed_requests)
    
    print(f"🔄 BAŞARISIZ İSTEKLERİ TEKRAR DENEME")
    print(f"Toplam başarısız istek: {total_tasks}")
    print(f"Worker sayısı: {MAX_WORKERS}")
    print(f"Çıktı dizini: {os.path.abspath(OUTPUT_DIR)}")
    print("-" * 80)
    
    start_time = time.time()
    
    # Create tasks from failed requests
    tasks = [(req['city'], req['year'], req['month'], req['day']) for req in failed_requests]
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {executor.submit(scrape_race_day, *task): task for task in tasks}
        
        for future in as_completed(future_to_task):
            city, year, month, day, data, success = future.result()
            
            if success and data:
                save_data(city, year, month, day, data)
            else:
                # Still failed, log it again
                log_failed_request(city, year, month, day, 'Retry failed')
            
            del future, city, year, month, day, data, success
            
            if processed_count % 20 == 0:
                elapsed = time.time() - start_time
                progress = (processed_count / total_tasks) * 100
                print(f"İlerleme: {progress:.1f}% ({processed_count}/{total_tasks})", flush=True)
        
        del future_to_task
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"✅ TEKRAR DENEME TAMAMLANDI!")
    print(f"Başarılı: {success_count}")
    print(f"Hala başarısız: {error_count}")
    print(f"Toplam süre: {elapsed/60:.1f} dakika")
    if error_count > 0:
        print(f"Hala başarısız olanlar: {os.path.abspath(RETRY_FAILED_FILE)}")
    else:
        # Delete original failed file if all succeeded
        if os.path.exists(FAILED_REQUESTS_FILE):
            os.remove(FAILED_REQUESTS_FILE)
            print(f"✅ Tüm başarısız istekler başarıyla yeniden çekildi!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
