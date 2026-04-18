# -*- coding: utf-8 -*-
import sys, io
from test_with_idman import load_race_from_program_with_idman
from predict_race import predict_race

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

r_h, r_i = load_race_from_program_with_idman('Izmir', 2026, 1, 30, 0)
res = predict_race(r_h, r_i)

print("KOŞU 1 - YENİ SKORLAMA SİSTEMİ:")
print("=" * 70)
for i, p in enumerate(res['predictions'][:8], 1):
    print(f"{i}. {p['horse_name']:20s}: {p['score']:6.2f}/100 (dist: {p['euclidean_distance']:6.2f})")
