"""
Bulk scraper to collect 5 years of race data from all Turkish racetracks
Multi-threaded for faster processing
"""
import requests
import json
import time
from datetime import datetime, timedelta
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import gc  # Garbage collector for memory management

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
    "Urfa",  # Fixed: was "Sanliurfa" but enum uses "Urfa"
    "Elazig",
    "Diyarbakir",
    "Antalya"
]

# Verbose logging to see all requests
VERBOSE = False  # Set to True to see all requests in console

# Date range
END_DATE = datetime(2026, 1, 30)  # End date
START_DATE = datetime(2025, 6, 1)  # Starting from June 1, 2025

# Output directory
OUTPUT_DIR = r"E:\data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Failed requests log file
FAILED_REQUESTS_FILE = os.path.join(OUTPUT_DIR, "failed_requests.json")

# Thread-safe counters and lists
lock = threading.Lock()
success_count = 0
error_count = 0
processed_count = 0
retry_count = 0
# REMOVED: failed_requests list to prevent RAM buildup
MAX_WORKERS = 30  # Maximum speed - parallel worker threads
REQUEST_TIMEOUT = 30  # Increased timeout for slow TJK responses
MAX_RETRIES = 2  # Reduced retries for speed
BATCH_SIZE = 500  # Process dates in batches to control memory usage

def scrape_race_day(city, year, month, day, retry_attempt=0):
    """Scrape data for a specific race day with retry logic"""
    global success_count, error_count, processed_count, retry_count
    
    params = {
        'city': city,
        'year': year,
        'month': month,
        'day': day,
        'type': 'fixture'  # Always fetch program (fixture) page for KGS/s20 data
    }
    
    try:
        if VERBOSE and retry_attempt == 0:
            print(f"📡 Fetching: {city} {year}-{month:02d}-{day:02d}", flush=True)
        elif retry_attempt > 0:
            print(f"🔄 Retry {retry_attempt}/{MAX_RETRIES}: {city} {year}-{month:02d}-{day:02d}", flush=True)
        
        response = requests.get(API_URL, params=params, timeout=REQUEST_TIMEOUT)
        
        with lock:
            processed_count += 1
            
        if response.status_code == 200:
            data = response.json()
            # Check if response is a dict with race data (dict keys should be race numbers like "0", "1", etc.)
            if isinstance(data, dict) and data:
                # If it has error keys, it's an error response
                if 'error' in data or 'detail' in data or 'message' in data or 'status_code' in data:
                    with lock:
                        error_count += 1
                    log_failed_request(city, year, month, day, 'API returned error response')
                    return (city, year, month, day, None, False)
                # Otherwise it's valid race data
                else:
                    with lock:
                        success_count += 1
                    if VERBOSE:
                        print(f"✅ SUCCESS: {city} {year}-{month:02d}-{day:02d} - {len(data)} races", flush=True)
                    return (city, year, month, day, data, True)
            else:
                with lock:
                    error_count += 1
                log_failed_request(city, year, month, day, 'Empty or invalid data')
                if VERBOSE:
                    print(f"❌ NO DATA: {city} {year}-{month:02d}-{day:02d}", flush=True)
                return (city, year, month, day, None, False)
        else:
            with lock:
                error_count += 1
            log_failed_request(city, year, month, day, f'HTTP {response.status_code}')
            if VERBOSE:
                print(f"⚠️ ERROR {response.status_code}: {city} {year}-{month:02d}-{day:02d}", flush=True)
            return (city, year, month, day, None, False)
    except Exception as e:
        error_msg = str(e)
        # Retry on timeout errors
        if retry_attempt < MAX_RETRIES and ('timeout' in error_msg.lower() or 'timed out' in error_msg.lower()):
            with lock:
                retry_count += 1
            print(f"⏰ TIMEOUT: {city} {year}-{month:02d}-{day:02d} - Retrying... ({retry_attempt + 1}/{MAX_RETRIES})", flush=True)
            time.sleep(2)  # Wait 2 seconds before retry
            return scrape_race_day(city, year, month, day, retry_attempt + 1)
        else:
            with lock:
                error_count += 1
            log_failed_request(city, year, month, day, f'Exception: {error_msg}')
            if VERBOSE:
                print(f"💥 EXCEPTION: {city} {year}-{month:02d}-{day:02d} - {error_msg}", flush=True)
            return (city, year, month, day, None, False)

def save_data(city, year, month, day, data):
    """Save data to JSON file organized by city/year/month"""
    city_dir = os.path.join(OUTPUT_DIR, city)
    year_dir = os.path.join(city_dir, str(year))
    os.makedirs(year_dir, exist_ok=True)
    
    filename = os.path.join(year_dir, f"{month:02d}.json")
    
    # Thread-safe file writing
    with lock:
        # Load existing data if file exists
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = {}
        
        # Update with new data
        existing_data[f"{day:02d}"] = data
        
        # Save back to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

def log_failed_request(city, year, month, day, reason):
    """Directly append failed request to file instead of keeping in memory"""
    failed_entry = {
        'city': city,
        'year': year,
        'month': month,
        'day': day,
        'reason': reason,
        'timestamp': datetime.now().isoformat()
    }
    
    with lock:
        # Append to file directly
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
    
    # Clear from memory immediately
    del failed_entry, failed_list

def main():
    """Main scraping function with multi-threading and batch processing"""
    global success_count, error_count, processed_count
    
    # Generate all dates (not tasks - we'll create tasks per batch)
    all_dates = []
    current_date = START_DATE
    while current_date <= END_DATE:
        all_dates.append(current_date)
        current_date += timedelta(days=1)
    
    total_dates = len(all_dates)
    total_tasks = total_dates * len(CITIES)
    
    print(f"Starting bulk scrape for {len(CITIES)} cities from {START_DATE.date()} to {END_DATE.date()}")
    print(f"Total dates: {total_dates} | Total requests: {total_tasks}")
    print(f"Using {MAX_WORKERS} parallel workers | Batch size: {BATCH_SIZE} dates")
    print(f"Request timeout: {REQUEST_TIMEOUT}s | Max retries: {MAX_RETRIES}")
    print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}")
    print("-" * 80)
    
    start_time = time.time()
    
    # Process dates in batches to control memory usage
    for batch_start in range(0, total_dates, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_dates)
        batch_dates = all_dates[batch_start:batch_end]
        
        # Create tasks for this batch only
        batch_tasks = []
        for date in batch_dates:
            for city in CITIES:
                batch_tasks.append((city, date.year, date.month, date.day))
        
        batch_num = (batch_start // BATCH_SIZE) + 1
        total_batches = (total_dates + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\n🔄 Processing batch {batch_num}/{total_batches} ({len(batch_tasks)} tasks)...", flush=True)
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks for this batch
            future_to_task = {executor.submit(scrape_race_day, *task): task for task in batch_tasks}
            
            # Process results as they complete
            for future in as_completed(future_to_task):
                city, year, month, day, data, success = future.result()
                
                if success and data:
                    save_data(city, year, month, day, data)
                    num_races = len(data)
                    if not VERBOSE:
                        # Only print every 100th successful scrape to reduce console spam & RAM
                        if success_count % 100 == 0:
                            print(f"✓ {city} {year}-{month:02d}-{day:02d}: {num_races} races", flush=True)
                
                # Free memory from completed future and result immediately
                del future, city, year, month, day, data, success
                
                # Progress update every 100 requests
                if processed_count % 100 == 0:
                    elapsed = time.time() - start_time
                    progress = (processed_count / total_tasks) * 100
                    rate = processed_count / elapsed if elapsed > 0 else 0
                    eta = (total_tasks - processed_count) / rate if rate > 0 else 0
                    print(f"Progress: {progress:.1f}% ({processed_count}/{total_tasks}) | "
                          f"Rate: {rate:.1f} req/s | ETA: {eta/60:.1f} min", flush=True)
            
            # Clear batch data
            del future_to_task
        
        # Force garbage collection after each batch
        del batch_tasks, batch_dates
        gc.collect()
        
        print(f"✅ Batch {batch_num}/{total_batches} completed. Memory freed.", flush=True)
    
    elapsed = time.time() - start_time
    
    # Final garbage collection
    gc.collect()
    
    print(f"\n{'='*80}")
    print(f"BULK SCRAPING COMPLETED!")
    print(f"Total successful: {success_count}")
    print(f"Total retries: {retry_count}")
    print(f"Total empty/errors: {error_count}")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print(f"Average rate: {total_tasks/elapsed:.1f} requests/second")
    print(f"Data saved to: {os.path.abspath(OUTPUT_DIR)}")
    if os.path.exists(FAILED_REQUESTS_FILE):
        print(f"Failed requests file: {os.path.abspath(FAILED_REQUESTS_FILE)}")
        print(f"You can retry failed requests later")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
