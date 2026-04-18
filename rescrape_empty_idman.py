"""
Boş İdmanları Yeniden Çek - Düzeltilmiş scraper ile
"""
import sys
sys.path.append('c:\\Users\\emir\\Desktop\\HorseRacingAPI-master')

from main.scrappers.idman import IdmanScrapper
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Input/Output
EMPTY_FILE = r"E:\data\empty_idman_horses.json"
OUTPUT_DIR = r"E:\data\idman"

# Thread-safe counters
lock = threading.Lock()
success_count = 0
error_count = 0
processed_count = 0
idman_found_count = 0
failed_horses = []

MAX_WORKERS = 30

def scrape_horse_idman(horse_id):
    """Tek bir atın idman bilgilerini çek"""
    global success_count, error_count, processed_count, idman_found_count
    
    try:
        data = IdmanScrapper.scrap_by_horse_id(horse_id)
        
        idman_count = len(data.get('idman_records', []))
        
        with lock:
            success_count += 1
            processed_count += 1
            if idman_count > 0:
                idman_found_count += 1
        
        return (horse_id, data, True, None, idman_count)
        
    except Exception as e:
        with lock:
            error_count += 1
            processed_count += 1
            failed_horses.append({'horse_id': horse_id, 'error': str(e)})
        
        return (horse_id, None, False, str(e), 0)

def save_idman_data(horse_id, data):
    """İdman verisini kaydet"""
    folder_num = (horse_id // 100) * 100
    folder_path = os.path.join(OUTPUT_DIR, f"{folder_num:06d}")
    os.makedirs(folder_path, exist_ok=True)
    
    filename = os.path.join(folder_path, f"{horse_id}.json")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    """Ana scraping fonksiyonu"""
    global success_count, error_count, processed_count, idman_found_count, failed_horses
    
    # Boş idman listesini yükle
    print("🔍 Boş idman listesi yükleniyor...")
    
    if not os.path.exists(EMPTY_FILE):
        print(f"❌ Dosya bulunamadı: {EMPTY_FILE}")
        print(f"Önce 'python find_empty_idman.py' çalıştırın!")
        return
    
    with open(EMPTY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        horse_ids = [item['horse_id'] for item in data['empty_horses']]
    
    total_horses = len(horse_ids)
    
    if total_horses == 0:
        print("✅ Boş idman yok!")
        return
    
    print(f"=" * 80)
    print(f"BOŞ İDMANLARI YENİDEN ÇEK (DÜZELTİLMİŞ SCRAPER)")
    print(f"=" * 80)
    print(f"Boş idman sayısı: {total_horses:,}")
    print(f"Worker: {MAX_WORKERS}")
    print(f"Çıktı: {OUTPUT_DIR}")
    print("-" * 80)
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_horse = {executor.submit(scrape_horse_idman, horse_id): horse_id 
                          for horse_id in horse_ids}
        
        for future in as_completed(future_to_horse):
            horse_id, data, success, error, idman_count = future.result()
            
            if success and data:
                save_idman_data(horse_id, data)
                if idman_count > 0:
                    print(f"✓ {horse_id}: {idman_count} idman bulundu!", flush=True)
            else:
                print(f"✗ {horse_id}: {error}", flush=True)
            
            # Progress
            if processed_count % 100 == 0:
                elapsed = time.time() - start_time
                progress = (processed_count / total_horses) * 100
                rate = processed_count / elapsed if elapsed > 0 else 0
                eta = (total_horses - processed_count) / rate if rate > 0 else 0
                
                print(f"\n📊 {progress:.1f}% | Başarılı: {success_count} | İdman bulunan: {idman_found_count} | "
                      f"Hata: {error_count} | Hız: {rate:.1f}/s | Kalan: {eta:.0f}s\n", flush=True)
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"✅ BOŞ İDMAN YENİDEN ÇEKİMİ TAMAMLANDI!")
    print(f"Toplam: {total_horses:,} at")
    print(f"Başarılı: {success_count:,}")
    print(f"İdman BULUNAN: {idman_found_count:,} ({idman_found_count/total_horses*100:.1f}%)")
    print(f"Hala boş: {success_count - idman_found_count:,}")
    print(f"Hata: {error_count:,}")
    print(f"Süre: {elapsed/60:.1f} dakika")
    if failed_horses:
        print(f"Başarısız atlar: {OUTPUT_DIR}\\failed_rescrape.json")
        with open(os.path.join(OUTPUT_DIR, 'failed_rescrape.json'), 'w', encoding='utf-8') as f:
            json.dump(failed_horses, f, ensure_ascii=False, indent=2)
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
