import json
from pathlib import Path

city = "Izmir"
year = "2026"
target_date = "2026-01-29"
race_dir = Path(f"E:/data/race_jsons/{city}/{year}")

print(f"Dizin: {race_dir}")
print(f"Exists: {race_dir.exists()}")

race_files = []

for race_file in race_dir.glob("*.json"):
    try:
        with open(race_file, encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                race_data = data[0]
            else:
                race_data = data
            
            print(f"\nDosya: {race_file.name}")
            print(f"  race_date: {race_data.get('race_date')}")
            print(f"  race_number: {race_data.get('race_number')}")
            
            # Tarihe göre filtrele
            if target_date:
                if race_data.get('race_date') == target_date:
                    race_files.append((race_file, race_data.get('race_number', 0)))
                    print(f"  [OK] Eslesti!")
    except Exception as e:
        print(f"  [ERROR] Hata: {e}")

print(f"\n{'='*80}")
print(f"Toplam {len(race_files)} yarış bulundu")
race_files.sort(key=lambda x: x[1])
for fname, rnum in race_files:
    print(f"Yarış {rnum}: {fname.name}")
