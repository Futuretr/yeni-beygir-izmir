"""
08-03-2026 Adana ve İzmir programlarını çek
"""
import requests
import json
from datetime import datetime
import os
import sys

# Fix console encoding for Turkish characters on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# API endpoint
API_URL = "http://127.0.0.1:8000/race_day"

# Tarih
year = 2026
month = 3
day = 8

# Şehirler (sırayla)
cities = ["Adana", "Izmir"]

# Output directory
OUTPUT_DIR = r"E:\data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def scrape_city_program(city):
    """Şehrin programını çek"""
    params = {
        'city': city,
        'year': year,
        'month': month,
        'day': day,
        'type': 'fixture'  # Program sayfası
    }
    
    print(f"\n📡 {city} için program çekiliyor: {year}-{month:02d}-{day:02d}")
    
    try:
        response = requests.get(API_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict) and data:
                # Hata kontrolü
                if 'error' in data or 'detail' in data or 'message' in data or 'status_code' in data:
                    print(f"❌ {city}: API hata döndü - {data}")
                    return None
                else:
                    # Başarılı
                    race_count = len(data)
                    print(f"✅ {city}: {race_count} koşu bulundu!")
                    
                    # Dosyaya kaydet
                    city_dir = os.path.join(OUTPUT_DIR, city)
                    os.makedirs(city_dir, exist_ok=True)
                    
                    filename = os.path.join(city_dir, f"{year}-{month:02d}-{day:02d}.json")
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    print(f"💾 Kaydedildi: {filename}")
                    
                    # Kısa özet
                    print(f"\n📋 {city} Koşu Özeti:")
                    for race_num, race_data in data.items():
                        if isinstance(race_data, dict):
                            race_info = race_data.get('race', {})
                            horse_count = len(race_data.get('horses', []))
                            distance = race_info.get('distance', '?')
                            ground = race_info.get('ground', '?')
                            race_time = race_info.get('time', '?')
                            print(f"  Koşu {race_num}: {horse_count} at, {distance}m, {ground}, Saat: {race_time}")
                        elif isinstance(race_data, list):
                            print(f"  Koşu {race_num}: {len(race_data)} at")
                    
                    return data
            else:
                print(f"⚠️ {city}: Veri yok (muhtemelen bugün yarış yok)")
                return None
        else:
            print(f"❌ {city}: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Hata detayı: {error_data}")
            except:
                print(f"   Hata içeriği: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ {city}: Hata - {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=" * 80)
    print(f"🏇 ADANA VE İZMİR PROGRAMLARI ({year}-{month:02d}-{day:02d})")
    print("=" * 80)
    
    results = {}
    
    # Sırayla çek
    for city in cities:
        data = scrape_city_program(city)
        if data:
            results[city] = data
    
    print("\n" + "=" * 80)
    print("📊 ÖZET")
    print("=" * 80)
    
    if results:
        for city, data in results.items():
            print(f"✅ {city}: {len(data)} koşu başarıyla çekildi")
    else:
        print("⚠️ Hiçbir şehirden veri çekilemedi")
    
    print("\n✨ Tamamlandı!")
