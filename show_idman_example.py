# -*- coding: utf-8 -*-
"""
İdman bonuslu örnek göster - Istanbul 2024
"""
import sys
import io
from test_with_idman import load_race_from_program_with_idman
from predict_race import predict_race

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# İdman verisi olan bir yarış
result = load_race_from_program_with_idman("Istanbul", 2024, 1, 27, 0)

if not result:
    print("Yarış bulunamadı!")
else:
    race_horses, race_info = result
    res = predict_race(race_horses, race_info)
    
    print("=" * 100)
    print("İDMAN BONUSLU TAHMİN ÖRNEĞİ")
    print("=" * 100)
    print(f"📍 {race_info['city']} - {race_info['race_date']}")
    print(f"🏁 {race_info['category']} - {race_info['track_type']} {race_info['distance']}m")
    
    idman_count = sum(1 for h in race_horses if h.get('last_idman'))
    print(f"✓ İdman: {idman_count}/{len(race_horses)} at ({idman_count*100//len(race_horses)}%)")
    
    print("\n" + "─" * 100)
    print("TOP 5 TAHMİN:")
    print("─" * 100)
    
    for i, p in enumerate(res['predictions'][:5], 1):
        print(f"\n{i}. {p['horse_name']} (#{p['start_no']})")
        print(f"   🎯 SKOR: {p['score']:.2f}/100")
        print(f"      Base: {p['base_score']:.2f} + İdman: +{p['idman_bonus']:.2f}")
        print(f"      Distance: {p['euclidean_distance']:.2f}")
        
        if p['idman_comparison']:
            fast_idmans = []
            for dist, comp in p['idman_comparison'].items():
                if comp['faster']:
                    fast_idmans.append(f"{dist}m (+{comp['bonus']:.1f})")
            if fast_idmans:
                print(f"      ⚡ İdman hızlı: {', '.join(fast_idmans)}")
