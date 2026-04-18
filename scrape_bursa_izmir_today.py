"""
06-03-2026 Bursa ve İzmir programlarını çek
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

# Tarih: 06-03-2026 (Bugün)
year = 2026
month = 3
day = 6

# Şehirler
cities = ["Bursa", "Izmir"]

# Output directory
OUTPUT_DIR = r"E:\data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def scrape_city_today(city):
    """Programı çek"""
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
                    return False
                
                # Veriyi kaydet
                filename = f"{OUTPUT_DIR}\\{city}_{year}-{month:02d}-{day:02d}_program.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Özet bilgi
                race_count = len(data.get('races', []))
                print(f"✅ {city} verisi başarıyla kaydedildi!")
                print(f"   📄 Dosya: {filename}")
                print(f"   🏇 Koşu Sayısı: {race_count}")
                
                return True
            else:
                print(f"❌ {city}: Geçersiz veri formatı veya boş veri")
                return False
                
        else:
            print(f"❌ {city}: HTTP {response.status_code} - {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️ {city}: Zaman aşımı (30 saniye)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {city}: Bağlantı hatası - Server çalışıyor mu?")
        return False
    except Exception as e:
        print(f"❌ {city}: Beklenmeyen hata - {type(e).__name__}: {e}")
        return False

def main():
    print("=" * 60)
    print(f"🏇 TJK Program Çekici - {day:02d}.{month:02d}.{year}")
    print("=" * 60)
    
    results = {}
    for city in cities:
        results[city] = scrape_city_today(city)
    
    # Özet
    print("\n" + "=" * 60)
    print("📊 ÖZET")
    print("=" * 60)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for city, success in results.items():
        status = "✅ Başarılı" if success else "❌ Başarısız"
        print(f"{city:15s}: {status}")
    
    print(f"\nToplam: {success_count}/{total_count} başarılı")
    print("=" * 60)

if __name__ == "__main__":
    main()
