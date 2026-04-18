"""
Antalya ve Adana'nın bugünkü (03-03-2026) verilerini çek
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
month = 3
day = 3

cities = ["Antalya", "Adana"]

# Output directory
OUTPUT_DIR = r"E:\data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def scrape_city_data(city, data_type):
    """Şehrin verilerini çek (fixture veya result)"""
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
                if 'error' in data or 'detail' in data or 'message' in data:
                    print(f"❌ API Hatası: {data}")
                    return False
                
                # Veri var mı kontrolü - API şu formatta dönüyor: {"0": [...], "1": [...]}
                # Ya da {"races": [...]}
                has_data = False
                if 'races' in data and len(data['races']) > 0:
                    has_data = True
                elif any(key.isdigit() for key in data.keys()):
                    has_data = True
                    # Yarış sayısını hesapla
                    race_count = sum(1 for key in data.keys() if key.isdigit())
                    print(f"✅ {race_count} yarış verisi bulundu")
                
                if has_data:
                    # Kaydet
                    folder = "program" if data_type == "fixture" else "sonuclar"
                    city_dir = os.path.join(OUTPUT_DIR, folder, city, str(year))
                    os.makedirs(city_dir, exist_ok=True)
                    
                    filename = os.path.join(city_dir, f"{month:02d}.json")
                    
                    # Eğer dosya varsa, mevcut veriyi yükle
                    existing_data = {}
                    if os.path.exists(filename):
                        try:
                            with open(filename, 'r', encoding='utf-8') as f:
                                existing_data = json.load(f)
                        except:
                            existing_data = {}
                    
                    # Yeni veriyi ekle (gün anahtarı ile)
                    existing_data[str(day)] = data
                    
                    # Kaydet
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(existing_data, f, ensure_ascii=False, indent=2)
                    
                    # Yarış sayısını bul
                    race_count = 0
                    if 'races' in data:
                        race_count = len(data['races'])
                    else:
                        race_count = sum(1 for key in data.keys() if key.isdigit())
                    
                    print(f"✅ {city} {type_name} kaydedildi: {race_count} yarış")
                    print(f"📁 Dosya: {filename}")
                    return True
                else:
                    print(f"⚠️  {city} için {type_name} verisi yok")
                    return False
            else:
                print(f"⚠️  Boş veya geçersiz veri: {data}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout!")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request hatası: {e}")
        return False
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print(f"🏇 Antalya ve Adana Veri Çekme - {year}-{month:02d}-{day:02d}")
    print("=" * 60)
    
    results = {}
    
    for city in cities:
        print(f"\n{'='*60}")
        print(f"🏙️  {city.upper()}")
        print(f"{'='*60}")
        
        # Program verilerini çek
        fixture_success = scrape_city_data(city, 'fixture')
        
        # Sonuç verilerini çek
        result_success = scrape_city_data(city, 'result')
        
        results[city] = {
            'fixture': fixture_success,
            'result': result_success
        }
    
    print("\n" + "=" * 60)
    print("📊 ÖZET:")
    print("=" * 60)
    for city in cities:
        print(f"\n{city}:")
        print(f"   Program: {'✅ Başarılı' if results[city]['fixture'] else '❌ Başarısız'}")
        print(f"   Sonuç: {'✅ Başarılı' if results[city]['result'] else '❌ Başarısız'}")
    print("=" * 60)
