"""
ULTRA HIZLI - Sadece regex ile time ve fark çek
BeautifulSoup'u atla, direkt regex
"""
import sys
sys.path.append('c:\\Users\\emir\\Desktop\\HorseRacingAPI-master')

import os
import json
import re
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Fix console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Komut satırından şehir al
if len(sys.argv) < 2:
    print("KULLANIM: python scrape_time_fark_fast.py <sehir_adi>")
    print("\nMevcut şehirler:")
    print("  Istanbul, Ankara, Izmir, Bursa, Adana, Antalya, Kocaeli, Elazig, Urfa")
    sys.exit(1)

CITY_NAME = sys.argv[1]

# Şehir ID'leri
CITY_IDS = {
    'Istanbul': 3,
    'Ankara': 2,
    'Izmir': 6,
    'Bursa': 7,
    'Adana': 1,
    'Antalya': 4,
    'Kocaeli': 9,
    'Elazig': 5,
    'Urfa': 8
}

if CITY_NAME not in CITY_IDS:
    print(f"❌ Hatalı şehir: {CITY_NAME}")
    sys.exit(1)

CITY_ID = CITY_IDS[CITY_NAME]

# Tarih aralığı
START_DATE = datetime(2021, 1, 1)
END_DATE = datetime(2026, 1, 30)

# Output
OUTPUT_FILE = rf"E:\data\time\time_fark_{CITY_NAME}.json"

print("=" * 80)
print(f"⚡ {CITY_NAME} - ULTRA HIZLI TIME VE FARK ÇEKME (REGEX)")
print("=" * 80)
print(f"📅 Tarih: {START_DATE.date()} - {END_DATE.date()}")
print(f"💾 Output: {OUTPUT_FILE}")
print()

def scrape_fast(date_obj):
    """Regex ile ultra hızlı çekme"""
    try:
        # URL
        date_str = date_obj.strftime('%d/%m/%Y').replace('/', '%2F')
        url = f"https://www.tjk.org/TR/YarisSever/Info/Sehir/GunlukYarisSonuclari?SehirId={CITY_ID}&QueryParameter_Tarih={date_str}&SehirAdi={CITY_NAME}"
        
        # Request
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        
        html = response.text
        
        # Her yarış div'ini bul
        race_divs = re.findall(
            r'<div[^>]+id="(\d{6})"[^>]*>.*?(?=<div[^>]+id="\d{6}"|$)',
            html,
            re.DOTALL
        )
        
        if not race_divs:
            return None
        
        results = []
        
        # Her yarış için
        for race_id in re.findall(r'<div[^>]+id="(\d{6})"', html):
            # O yarışın HTML'ini bul
            race_section = re.search(
                rf'<div[^>]+id="{race_id}"[^>]*>(.*?)(?=<div[^>]+id="\d{{6}}"|$)',
                html,
                re.DOTALL
            )
            
            if not race_section:
                continue
            
            race_html = race_section.group(1)
            
            # Bu yarıştaki tüm atları çek
            horses = re.findall(
                r'QueryParameter_AtId=(\d+).*?' +
                r'GunlukYarisSonuclari-Derece[^>]*>\s*\n*([^\n<]*?)\s*\n*\s*</td>.*?' +
                r'GunlukYarisSonuclari-Fark[^>]*>\s*\n*([^\n<]*?)\s*\n*\s*</td>',
                race_html,
                re.DOTALL
            )
            
            for horse_id, time_val, fark_val in horses:
                results.append({
                    'race_id': int(race_id),
                    'horse_id': int(horse_id),
                    'time': time_val.strip(),
                    'fark': fark_val.strip()
                })
        
        return results if results else None
        
    except Exception as e:
        return None

# Tarihleri oluştur
dates = []
current = START_DATE
while current <= END_DATE:
    dates.append(current)
    current += timedelta(days=1)

print(f"📦 {len(dates):,} tarih")
print(f"🔄 50 worker ile başlıyor...\n")

all_data = []
success = 0
empty = 0
failed = 0
start_time = time.time()

with ThreadPoolExecutor(max_workers=50) as executor:
    futures = {executor.submit(scrape_fast, date): date for date in dates}
    
    for i, future in enumerate(as_completed(futures), 1):
        try:
            result = future.result()
            
            if result:
                all_data.extend(result)
                success += 1
            else:
                empty += 1
                
            if i % 50 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(dates) - i) / rate if rate > 0 else 0
                print(f"✅ {i:,}/{len(dates):,} | Kayıt: {len(all_data):,} | "
                      f"Hız: {rate:.1f} tarih/s | ETA: {eta:.0f}s")
        except:
            failed += 1

# Kaydet
print(f"\n💾 {len(all_data):,} kayıt kaydediliyor...")
os.makedirs(r'E:\data\time', exist_ok=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

elapsed = time.time() - start_time
print("\n" + "=" * 80)
print("✅ TAMAMLANDI")
print("=" * 80)
print(f"Süre: {elapsed:.0f}s ({elapsed/60:.1f}dk)")
print(f"Başarılı: {success:,}")
print(f"Boş: {empty:,}")
print(f"Kayıt: {len(all_data):,}")
print(f"Hız: {len(dates)/elapsed:.1f} tarih/s")
