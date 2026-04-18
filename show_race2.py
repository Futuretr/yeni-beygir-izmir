# -*- coding: utf-8 -*-
import sys, io
from test_with_idman import load_race_from_program_with_idman
from predict_race import predict_race

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Koşu 2 (index 1)
r_h, r_i = load_race_from_program_with_idman('Izmir', 2026, 1, 30, 1)
res = predict_race(r_h, r_i)

print("=" * 100)
print("30 OCAK 2026 İZMİR - KOŞU #2 (ŞARTLI 4)")
print("=" * 100)

print(f"\nYarış Bilgileri:")
print(f"  Kategori: {r_i['category']}")
print(f"  Pist: {r_i['track_type']} {r_i['distance']}m")
print(f"  Yaş Grubu: {r_i.get('age_group')}")
print(f"  Toplam At: {len(r_h)}")

idman_count = sum(1 for h in r_h if h.get('last_idman'))
print(f"  İdman Verisi: {idman_count}/{len(r_h)} at")

dream = res['dream_horse']
print(f"\nDream Horse: {dream['total_wins_analyzed']} galibiyet analizi")

print("\n" + "=" * 100)
print("TAHMİN SONUÇLARI:")
print("=" * 100)

for i, p in enumerate(res['predictions'], 1):
    print(f"\n{i}. {p['horse_name']:25s} (#{p['start_no']})")
    print(f"   ⭐ SKOR: {p['score']:6.2f}/100  (Distance: {p['euclidean_distance']:6.2f})")
    print(f"   • Temel: {p['base_score']:.2f} | İdman Bonus: +{p['idman_bonus']:.2f}")
    print(f"   • Jokey: {p['jockey']:20s} | Antrenör: {p['trainer']}")
    print(f"   • Yaş: {p['details']['age']:10s} | Kilo: {p['details']['weight']:6s} | Handicap: {p['details']['handicap_weight'] or 'YOK'}")
    
    if p['idman_comparison']:
        bonuses = []
        for dist, comp in p['idman_comparison'].items():
            if comp['faster']:
                bonuses.append(f"{dist}(+{comp['bonus']:.1f})")
        if bonuses:
            print(f"   ✓ İdman Hızlı: {', '.join(bonuses)}")

print("\n" + "=" * 100)
print(f"🏆 ÖNERİ: {res['predictions'][0]['horse_name']} - {res['predictions'][0]['score']:.2f}/100")
print("=" * 100)
