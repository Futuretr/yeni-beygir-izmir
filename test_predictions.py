# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from test_with_idman import load_race_from_program_with_idman
from predict_race import predict_race

gerçek_sonuçlar = {
    1: "ÖZGÜNVERA",
    2: "DİLHUN",
    3: "ERSOYHAN",
    4: "CESURSOY",
    5: "UNSEEN POWER",
    6: "BOLİDE",
    7: "AGE OF DISCOVERY"
}

print("=" * 80)
print("TAHMİN vs GERÇEK SONUÇLAR - MUTLAK DEĞER SISTEMİ (0'a en yakın)")
print("=" * 80)

doğru = 0
for race_num in range(7):
    result = load_race_from_program_with_idman('Antalya', 2026, 1, 30, race_num)
    if result:
        race_horses, race_info = result
        res = predict_race(race_horses, race_info)
        
        tahmin = res['predictions'][0]['horse_name']
        skor = res['predictions'][0]['score']
        gerçek = gerçek_sonuçlar.get(race_num + 1, "?")
        
        durum = "✓ DOĞRU!" if tahmin == gerçek else "✗"
        if tahmin == gerçek:
            doğru += 1
            
        print(f"\nKOŞU #{race_num+1}:")
        print(f"  Tahmin: {tahmin:20s} (Skor: {skor:6.2f})")
        print(f"  Gerçek: {gerçek:20s} {durum}")

print(f"\n{'=' * 80}")
print(f"BAŞARI ORANI: {doğru}/7 = %{(doğru*100/7):.1f}")
print(f"{'=' * 80}")
