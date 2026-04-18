# -*- coding: utf-8 -*-
import sys, io, json
from pathlib import Path
from test_with_idman import load_race_from_program_with_idman
from predict_race import (
    extract_weight, 
    extract_age_years,
    get_horse_last_race_data,
    calculate_adjusted_100m_time,
    time_to_seconds
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

r_h, r_i = load_race_from_program_with_idman('Izmir', 2026, 1, 30, 0)

# Dream Horse'u yükle
dream_file = Path(f"E:\\data\\stats\\dream_horse\\{r_i['category']}\\{r_i['city']}\\İngiliz\\{r_i['track_type']}_{r_i['distance']}m.json")
with open(dream_file, 'r', encoding='utf-8') as f:
    dream = json.load(f)

print("=" * 100)
print("DREAM HORSE DEĞERLERİ:")
print("=" * 100)
print(f"Kilo: {dream.get('horse_weight')} kg")
print(f"Handicap: {dream.get('handicap_weight') or 'YOK'}")
print(f"Derece: {dream.get('time')}")
dream_time = time_to_seconds(dream.get('time'))
if dream_time:
    dream_100m = dream_time / (r_i['distance'] / 100)
    print(f"100m Süresi: {dream_100m:.2f}s")
print(f"Referans: {dream['_metadata']['total_wins_analyzed']} galibiyet")

print("\n" + "=" * 100)
print("ATLAR VE FARKLAR:")
print("=" * 100)

race_date = r_i.get('race_date')

for i, horse in enumerate(r_h[:5], 1):
    print(f"\n{i}. {horse.get('horse_name')}")
    print("-" * 100)
    
    # Kilo
    h_weight = extract_weight(horse.get('horse_weight'))
    d_weight = extract_weight(dream.get('horse_weight'))
    weight_diff = abs(h_weight - d_weight) if h_weight and d_weight else 0
    print(f"  Kilo: {h_weight} kg (Dream: {d_weight} kg) → Fark: {weight_diff:.1f} kg")
    
    # Handicap
    h_hw = extract_weight(horse.get('handicap_weight'))
    d_hw = extract_weight(dream.get('handicap_weight'))
    hw_diff = abs(h_hw - d_hw) if h_hw and d_hw else 0
    print(f"  Handicap: {h_hw or 'YOK'} (Dream: {d_hw or 'YOK'}) → Fark: {hw_diff:.1f}")
    
    # Derece
    last_race = get_horse_last_race_data(horse, race_date)
    if last_race:
        h_100m = calculate_adjusted_100m_time(horse, r_i['city'], r_i['track_type'], r_i['distance'], race_date)
        if h_100m and dream_100m:
            time_diff = abs(h_100m - dream_100m)
            faster = "✓ HIZLI" if h_100m < dream_100m else "✗ YAVAŞ"
            print(f"  100m: {h_100m:.2f}s (Dream: {dream_100m:.2f}s) → Fark: {time_diff:.2f}s {faster}")
        else:
            print(f"  100m: Hesaplanamadı")
    else:
        print(f"  100m: Son yarış bulunamadı")
    
    print(f"  İdman: {'VAR' if horse.get('last_idman') else 'YOK'}")
