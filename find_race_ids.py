import json
from pathlib import Path

files = list(Path(r'E:\data\race_jsons\Izmir\2026').glob('*.json'))
races = []

for f in files:
    try:
        data = json.load(open(f, 'r', encoding='utf-8'))
        if isinstance(data, list):
            race = data[0]
        else:
            race = data
        
        if race.get('race_date') == '2026-01-29':
            races.append((f.stem, race.get('race_number', 0), race.get('race_category', 'N/A')))
    except:
        pass

races.sort(key=lambda x: x[1])

for rid, rnum, cat in races[:8]:
    print(f"ID: {rid:10} - Race #{rnum} - {cat}")
