"""
İzmir'in bugünkü (27-02-2026) verilerini çek
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

# Bugünün tarihi
year = 2026
month = 2
day = 27

city = "Izmir"

# Output directory
OUTPUT_DIR = r"E:\data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def scrape_izmir_data(data_type):
    """İzmir'in verilerini çek (fixture veya result)"""
    params = {
        'city': city,
        'year': year,
        'month': month,
        'day': day,
        'type': data_type
    }
    
    type_name = "Program" if data_type == "fixture" else "Sonuç"
    print(f"\n📡 {city} için {type_name} çekiliyor: {year}-{month:02d}-{day:02d}")
    
    try:
        response = requests.get(API_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Debug: API'den gelen veriyi göster
            print(f"🔍 API Yanıtı: {json.dumps(data, ensure_ascii=False)[:500]}...")
            
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
                    
                    # Data type'a göre dosya adı
                    if data_type == "fixture":
                        filename = os.path.join(city_dir, f"{year}-{month:02d}-{day:02d}.json")
                    else:
                        filename = os.path.join(city_dir, f"{year}-{month:02d}-{day:02d}_results.json")
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    print(f"💾 Kaydedildi: {filename}")
                    
                    # Kısa özet
                    print(f"\n📋 {city} Koşu Özeti ({type_name}):")
                    for race_num, race_data in data.items():
                        if isinstance(race_data, dict):
                            race_info = race_data.get('race', {})
                            horse_count = len(race_data.get('horses', []))
                            distance = race_info.get('distance', '?')
                            ground = race_info.get('ground', '?')
                            print(f"  Koşu {race_num}: {horse_count} at, {distance}m, {ground}")
                        elif isinstance(race_data, list):
                            print(f"  Koşu {race_num}: {len(race_data)} at")
                    
                    return data
            else:
                print(f"⚠️ {city}: Veri yok (muhtemelen bu tarihte yarış yok)")
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
    print(f"🏇 İZMİR VERİ ÇEKME ({year}-{month:02d}-{day:02d})")
    print("=" * 80)
    
    # Önce program (fixture)
    fixture_data = scrape_izmir_data("fixture")
    
    # Sonra sonuç (result) - varsa
    result_data = scrape_izmir_data("result")
    
    print("\n" + "=" * 80)
    print("📊 ÖZET")
    print("=" * 80)
    
    if fixture_data:
        print(f"✅ Program çekildi: {len(fixture_data)} koşu")
    else:
        print("❌ Program çekilemedi")
    
    if result_data:
        print(f"✅ Sonuç çekildi: {len(result_data)} koşu")
    else:
        print("⚠️ Sonuç bulunamadı (henüz koşulmamış olabilir)")
    
    print("=" * 80)
