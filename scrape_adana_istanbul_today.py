"""
7 Mart 2026 Adana ve İstanbul programlarını çek
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

# Tarih: 07-03-2026
year = 2026
month = 3
day = 7

# Şehirler
cities = ["Adana", "Istanbul"]

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
        'type': 'program'
    }
    
    print(f"📥 {city} programı çekiliyor... ({day:02d}-{month:02d}-{year})")
    
    try:
        response = requests.get(API_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Save to file
            filename = f"{city}_{year}-{month:02d}-{day:02d}_program.json"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ {city} programı kaydedildi: {filepath}")
            return True
        else:
            print(f"❌ {city} için hata (HTTP {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ {city} için hata: {e}")
        return False

if __name__ == "__main__":
    print(f"🏇 {day:02d}-{month:02d}-{year} Adana ve İstanbul programları çekiliyor...\n")
    
    results = {}
    for city in cities:
        results[city] = scrape_city_today(city)
        print()
    
    print("\n" + "="*60)
    print("📊 ÖZET")
    print("="*60)
    for city, success in results.items():
        status = "✅ Başarılı" if success else "❌ Başarısız"
        print(f"{city:15} : {status}")
    print("="*60)
