"""
Eksik İdmanları Çek - Sadece missing_idman_horses.json'daki atlar için
"""
import sys
sys.path.append('c:\\Users\\emir\\Desktop\\HorseRacingAPI-master')

from main.scrappers.idman import IdmanScrapper
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

# Fix console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Input/Output
MISSING_FILE = r"E:\data\missing_idman_horses.json"
OUTPUT_DIR = r"E:\data\idman"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Thread-safe counters
lock = threading.Lock()
success_count = 0
error_count = 0
processed_count = 0
failed_horses = []

MAX_WORKERS = 30  # Paralel worker sayısı
REQUEST_TIMEOUT = 10

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
    """İdman verisini kaydet"""
    # Her 100 atı bir klasöre koy
    folder_num = (horse_id // 100) * 100
    folder_path = os.path.join(OUTPUT_DIR, f"{folder_num:06d}")
    os.makedirs(folder_path, exist_ok=True)
    
    filename = os.path.join(folder_path, f"{horse_id}.json")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    """Ana scraping fonksiyonu"""
    global success_count, error_count, processed_count, failed_horses
    
    # Eksik horse ID'lerini yükle
    print("🔍 Eksik idman listesi yükleniyor...")
    
    if not os.path.exists(MISSING_FILE):
        print(f"❌ Dosya bulunamadı: {MISSING_FILE}")
        print(f"Önce 'python find_missing_idman.py' çalıştırın!")
        return
    
    with open(MISSING_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        horse_ids = data['missing_horse_ids']
    
    total_horses = len(horse_ids)
    
    if total_horses == 0:
        print("✅ Eksik idman yok!")
        return
    
    print(f"=" * 80)
    print(f"EKSİK İDMANLARI ÇEK")
    print(f"=" * 80)
    print(f"Eksik at sayısı: {total_horses:,}")
    print(f"Worker: {MAX_WORKERS}")
    print(f"Çıktı: {OUTPUT_DIR}")
    print("-" * 80)
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_horse = {executor.submit(scrape_horse_idman, horse_id): horse_id 
                          for horse_id in horse_ids}
        
        for future in as_completed(future_to_horse):
            horse_id, data, success, error = future.result()
            
            if success and data:
                save_idman_data(horse_id, data)
                print(f"✓ {horse_id}: {len(data.get('idman_records', []))} idman kaydı", flush=True)
            else:
                print(f"✗ {horse_id}: {error}", flush=True)
            
            # Progress
            if processed_count % 10 == 0:
                elapsed = time.time() - start_time
                progress = (processed_count / total_horses) * 100
                rate = processed_count / elapsed if elapsed > 0 else 0
                eta = (total_horses - processed_count) / rate if rate > 0 else 0
                
                print(f"\n📊 İlerleme: {progress:.1f}% ({processed_count}/{total_horses}) | "
                      f"Başarılı: {success_count} | Hata: {error_count} | "
                      f"Hız: {rate:.1f} at/s | Kalan: {eta:.0f}s\n", flush=True)
    
    # Failed horses'ları kaydet
    if failed_horses:
        failed_file = os.path.join(OUTPUT_DIR, 'failed_missing_horses.json')
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed_horses, f, ensure_ascii=False, indent=2)
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"✅ EKSİK İDMAN ÇEKİMİ TAMAMLANDI!")
    print(f"Başarılı: {success_count}/{total_horses} at")
    print(f"Başarısız: {error_count}/{total_horses} at")
    print(f"Başarı oranı: {success_count/total_horses*100:.1f}%")
    print(f"Toplam süre: {elapsed/60:.1f} dakika")
    print(f"Ortalama hız: {total_horses/elapsed:.1f} at/saniye")
    if failed_horses:
        print(f"Başarısız atlar: {failed_file}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
