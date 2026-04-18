"""
Retry failed requests from the bulk scraper
Reads failed_requests.json and attempts to scrape those dates again
"""
import requests
import json
import time
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
FAILED_REQUESTS_FILE = os.path.join(OUTPUT_DIR, "failed_requests.json")
NEW_FAILED_FILE = os.path.join(OUTPUT_DIR, "failed_requests_retry.json")

# Thread-safe counters
lock = threading.Lock()
success_count = 0
error_count = 0
processed_count = 0
MAX_WORKERS = 10  # Lower parallelization for retry

# New failed requests
still_failed = []

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
        print(f"🔄 Retrying: {city} {year}-{month:02d}-{day:02d}", flush=True)
        response = requests.get(API_URL, params=params, timeout=15)
        
        with lock:
            processed_count += 1
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data:
                if 'error' in data or 'detail' in data or 'message' in data or 'status_code' in data:
                    with lock:
                        error_count += 1
                        still_failed.append({
                            'city': city, 'year': year, 'month': month, 'day': day,
                            'reason': 'API returned error response'
                        })
                    return (city, year, month, day, None, False)
                else:
                    with lock:
                        success_count += 1
                    print(f"✅ SUCCESS: {city} {year}-{month:02d}-{day:02d} - {len(data)} races", flush=True)
                    return (city, year, month, day, data, True)
            else:
                with lock:
                    error_count += 1
                    still_failed.append({
                        'city': city, 'year': year, 'month': month, 'day': day,
                        'reason': 'Empty or invalid data'
                    })
                return (city, year, month, day, None, False)
        else:
            with lock:
                error_count += 1
                still_failed.append({
                    'city': city, 'year': year, 'month': month, 'day': day,
                    'reason': f'HTTP {response.status_code}'
                })
            return (city, year, month, day, None, False)
    except Exception as e:
        with lock:
            error_count += 1
            still_failed.append({
                'city': city, 'year': year, 'month': month, 'day': day,
                'reason': f'Exception: {str(e)}'
            })
        return (city, year, month, day, None, False)

def save_data(city, year, month, day, data):
    """Save data to JSON file organized by city/year/month"""
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

def main():
    """Main retry function"""
    global success_count, error_count, processed_count
    
    # Check if failed requests file exists
    if not os.path.exists(FAILED_REQUESTS_FILE):
        print(f"❌ Failed requests file not found: {FAILED_REQUESTS_FILE}")
        print("Run bulk_scraper.py first to generate failed requests file.")
        return
    
    # Load failed requests
    with open(FAILED_REQUESTS_FILE, 'r', encoding='utf-8') as f:
        failed_requests = json.load(f)
    
    if not failed_requests:
        print("✅ No failed requests to retry!")
        return
    
    print(f"Found {len(failed_requests)} failed requests to retry")
    print(f"Using {MAX_WORKERS} parallel workers")
    print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}")
    print("-" * 80)
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(
                scrape_race_day, 
                req['city'], 
                req['year'], 
                req['month'], 
                req['day']
            ): req for req in failed_requests
        }
        
        # Process results as they complete
        for future in as_completed(future_to_task):
            city, year, month, day, data, success = future.result()
            
            if success and data:
                save_data(city, year, month, day, data)
    
    elapsed = time.time() - start_time
    
    # Save still failed requests
    if still_failed:
        with open(NEW_FAILED_FILE, 'w', encoding='utf-8') as f:
            json.dump(still_failed, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"RETRY COMPLETED!")
    print(f"Total attempted: {len(failed_requests)}")
    print(f"Now successful: {success_count}")
    print(f"Still failing: {error_count}")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print(f"Data saved to: {os.path.abspath(OUTPUT_DIR)}")
    if still_failed:
        print(f"Still failed requests saved to: {os.path.abspath(NEW_FAILED_FILE)}")
    else:
        print(f"🎉 All failed requests were successfully retried!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
