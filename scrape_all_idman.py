"""
Tüm atların idman istatistiklerini hızlıca çek
19,774 at için idman verileri
"""
import sys
sys.path.append('c:\\Users\\emir\\Desktop\\HorseRacingAPI-master')

from main.scrappers.idman import IdmanScrapper
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import gc

# Fix console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Input/Output
HORSE_IDS_FILE = r"E:\data\all_horse_ids.json"
OUTPUT_DIR = r"E:\data\idman"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Thread-safe counters
lock = threading.Lock()
success_count = 0
error_count = 0
processed_count = 0
failed_horses = []

MAX_WORKERS = 50  # Maksimum hız için 50 paralel worker
REQUEST_TIMEOUT = 10  # Daha kısa timeout
BATCH_SIZE = 2000  # Daha büyük batch'ler

def scrape_horse_idman(horse_id):
    """Tek bir atın idman bilgilerini çek"""
    global success_count, error_count, processed_count
    
    try:
        data = IdmanScrapper.scrap_by_horse_id(horse_id)
        
        with lock:
            success_count += 1
            processed_count += 1
        
        return (horse_id, data, True, None)
        
    except Exception as e:
        with lock:
            error_count += 1
            processed_count += 1
            failed_horses.append({'horse_id': horse_id, 'error': str(e)})
        
        return (horse_id, None, False, str(e))

def save_idman_data(horse_id, data):
    """İdman verisini kaydet - her at için ayrı dosya"""
    # Her 100 atı bir klasöre koy (0-99, 100-199, vs.)
    folder_num = (horse_id // 100) * 100
    folder_path = os.path.join(OUTPUT_DIR, f"{folder_num:06d}")
    os.makedirs(folder_path, exist_ok=True)
    
    filename = os.path.join(folder_path, f"{horse_id}.json")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    """Ana scraping fonksiyonu"""
    global success_count, error_count, processed_count, failed_horses
    
    # Horse ID'lerini yükle
    print("🔍 Horse ID'leri yükleniyor...")
    with open(HORSE_IDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        horse_ids = data['horse_ids']
    
    total_horses = len(horse_ids)
    
    print(f"🏁 ATLAR İÇİN İDMAN BİLGİLERİNİ ÇEK")
    print(f"Toplam at: {total_horses:,}")
    print(f"Worker: {MAX_WORKERS}")
    print(f"Batch: {BATCH_SIZE}")
    print(f"Çıktı: {OUTPUT_DIR}")
    print("-" * 80)
    
    start_time = time.time()
    
    # Batch'lere böl
    batches = [horse_ids[i:i + BATCH_SIZE] for i in range(0, len(horse_ids), BATCH_SIZE)]
    total_batches = len(batches)
    
    for batch_num, batch in enumerate(batches, 1):
        print(f"\n🔄 Batch {batch_num}/{total_batches} ({len(batch)} at)")
        batch_start = time.time()
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_horse = {executor.submit(scrape_horse_idman, horse_id): horse_id 
                              for horse_id in batch}
            
            for future in as_completed(future_to_horse):
                horse_id, data, success, error = future.result()
                
                if success and data:
                    save_idman_data(horse_id, data)
                
                # Progress
                if processed_count % 100 == 0:
                    elapsed = time.time() - start_time
                    progress = (processed_count / total_horses) * 100
                    rate = processed_count / elapsed if elapsed > 0 else 0
                    eta = (total_horses - processed_count) / rate if rate > 0 else 0
                    
                    print(f"İlerleme: {progress:.1f}% ({processed_count:,}/{total_horses:,}) | "
                          f"Başarılı: {success_count:,} | Hata: {error_count:,} | "
                          f"Hız: {rate:.1f} at/s | Kalan: {eta/60:.1f} dk", flush=True)
                
                del future, horse_id, data, success, error
            
            del future_to_horse
        
        batch_elapsed = time.time() - batch_start
        print(f"✅ Batch {batch_num} tamamlandı ({batch_elapsed:.1f}s)")
        gc.collect()
    
    # Failed horses'ları kaydet
    if failed_horses:
        failed_file = os.path.join(OUTPUT_DIR, 'failed_horses.json')
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed_horses, f, ensure_ascii=False, indent=2)
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"✅ TÜM İDMAN VERİLERİ ÇEKİLDİ!")
    print(f"Başarılı: {success_count:,} at")
    print(f"Başarısız: {error_count:,} at")
    print(f"Toplam süre: {elapsed/60:.1f} dakika")
    print(f"Ortalama hız: {total_horses/elapsed:.1f} at/saniye")
    print(f"Veri dizini: {os.path.abspath(OUTPUT_DIR)}")
    if failed_horses:
        print(f"Başarısız atlar: {OUTPUT_DIR}\\failed_horses.json")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
