"""
Tek bir günün tüm verisini çeker ve dosyaya kaydeder
"""
import requests
import json

# 29 Ocak 2026 Antalya
API_URL = "http://127.0.0.1:8000/race_day"

params = {
    'city': 'Antalya',
    'year': 2026,
    'month': 1,
    'day': 29
}

print(f"Fetching: {params['city']} {params['year']}-{params['month']:02d}-{params['day']:02d}")

try:
    response = requests.get(API_URL, params=params, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        
        # Save to file
        filename = f"sample_data_{params['city']}_{params['year']}-{params['month']:02d}-{params['day']:02d}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Data saved to: {filename}")
        print(f"\nTotal races: {len(data)}")
        total_horses = sum(len(race) for race in data.values())
        print(f"Total horses: {total_horses}")
        
        # Print full data to console
        print("\n" + "="*80)
        print("FULL DATA:")
        print("="*80)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
    else:
        print(f"ERROR: Status {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"ERROR: {str(e)}")
