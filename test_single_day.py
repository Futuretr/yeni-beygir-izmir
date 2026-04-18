"""
Test script - Tek bir günü çekip kontrol eder
"""
import requests
import json

# Test: 30 Ocak 2026 Antalya (bugün - program sayfası, KGS/s20 olmalı)
API_URL = "http://127.0.0.1:8000/race_day"

params = {
    'city': 'Antalya',
    'year': 2026,
    'month': 1,
    'day': 30
}

print("Testing API with:")
print(f"  URL: {API_URL}")
print(f"  City: {params['city']}")
print(f"  Date: {params['year']}-{params['month']:02d}-{params['day']:02d}")
print("-" * 80)

try:
    response = requests.get(API_URL, params=params, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n✓ SUCCESS! Got data for {len(data)} races")
        print("-" * 80)
        
        # Show sample data from first race
        if data and '0' in data:
            first_race = data['0']
            if first_race and len(first_race) > 0:
                first_horse = first_race[0]
                print("\nSample data (first horse):")
                print(json.dumps(first_horse, indent=2, ensure_ascii=False))
                
                # Check important fields
                print("\n" + "=" * 80)
                print("FIELD CHECK:")
                print("=" * 80)
                fields_to_check = [
                    'race_number', 'race_category', 'age_group', 'distance', 'track_type',
                    'horse_name', 'horse_equipment', 'jockey_name', 'trainer_name', 
                    'owner_name', 'kgs', 's20', 'agf', 'finish_position'
                ]
                
                for field in fields_to_check:
                    value = first_horse.get(field, 'MISSING')
                    status = "✓" if value and value != "" else "✗"
                    print(f"{status} {field:20s}: {value}")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        total_horses = sum(len(race) for race in data.values())
        print(f"Total races: {len(data)}")
        print(f"Total horses: {total_horses}")
        print("\nData structure looks good! ✓")
        
    else:
        print(f"\n✗ ERROR: Status code {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"\n✗ EXCEPTION: {str(e)}")
