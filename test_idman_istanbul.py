# -*- coding: utf-8 -*-
from test_with_idman import load_race_from_program_with_idman

# İstanbul 2024 - İdman olması muhtemel
result = load_race_from_program_with_idman('Istanbul', 2024, 1, 27, 0)

if result:
    horses, info = result
    print(f'Yarış: Istanbul 27.01.2024 - Koşu #1')
    print(f'Toplam at: {len(horses)}')
    print(f'Idman olan: {sum(1 for h in horses if h.get("last_idman"))}')
    print('\nİlk 5 at detay:')
    for i, h in enumerate(horses[:5], 1):
        print(f'\n{i}. {h.get("horse_name")}')
        print(f'   Horse ID: {h.get("horse_id")}')
        idman = h.get("last_idman")
        if idman:
            print(f'   ✓ İdman var!')
            print(f'     Tarih: {idman.get("İ. Tarihi") or idman.get("Ä°. Tarihi")}')
            print(f'     600m: {idman.get("600m")}')
            print(f'     1000m: {idman.get("1000m")}')
        else:
            print(f'   ✗ İdman yok')
else:
    print("Yarış bulunamadı!")
