# -*- coding: utf-8 -*-
from test_with_idman import load_race_from_program_with_idman

result = load_race_from_program_with_idman('Izmir', 2026, 1, 30, 1)

if result:
    horses, info = result
    print(f'Toplam at: {len(horses)}')
    print(f'Idman olan: {sum(1 for h in horses if h.get("last_idman"))}')
    print('\nİlk 3 at detay:')
    for i, h in enumerate(horses[:3], 1):
        print(f'\n{i}. {h.get("horse_name")}')
        print(f'   Horse ID: {h.get("horse_id")}')
        print(f'   Last idman: {h.get("last_idman")}')
