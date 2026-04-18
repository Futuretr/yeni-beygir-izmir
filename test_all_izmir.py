# -*- coding: utf-8 -*-
"""
30 Ocak 2026 İzmir - TÜM KOŞULAR Tahmin Testi
"""
import sys
import io
from test_with_idman import load_race_from_program_with_idman
from predict_race import predict_race

# UTF-8 encoding için
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_all_races_izmir():
    """İzmir 30.01.2026 - Tüm koşuları test et"""
    
    city = "Izmir"
    year = 2026
    month = 1
    day = 30
    
    print("=" * 100)
    print("30 OCAK 2026 İZMİR - TÜM KOŞULAR TAHMİN TESTİ")
    print("=" * 100)
    
    # 0-7 arası 8 koşu var
    for race_number in range(8):
        print(f"\n{'#' * 100}")
        print(f"KOŞU #{race_number + 1} (JSON index: {race_number})")
        print(f"{'#' * 100}\n")
        
        result = load_race_from_program_with_idman(city, year, month, day, race_number)
        
        if not result:
            print(f"❌ Koşu {race_number + 1} yüklenemedi!\n")
            continue
        
        race_horses, race_info = result
        
        print(f"📋 YARIŞ BİLGİLERİ:")
        print(f"   Kategori: {race_info['category']}")
        print(f"   Şehir: {race_info['city']}")
        print(f"   Pist: {race_info['track_type']}")
        print(f"   Mesafe: {race_info['distance']}m")
        print(f"   Yaş Grubu: {race_info.get('age_group', 'N/A')}")
        print(f"   Toplam At: {len(race_horses)}")
        
        idman_count = sum(1 for h in race_horses if h.get('last_idman'))
        print(f"   İdman Verisi: {idman_count}/{len(race_horses)} at")
        
        # Tahmin yap
        results = predict_race(race_horses, race_info)
        
        if 'error' in results:
            print(f"\n❌ HATA: {results['error']}\n")
            continue
        
        dream = results['dream_horse']
        print(f"\n🎯 Dream Horse: {dream['category']}/{dream['city']}/{dream['breed']}/{dream['track_type']}_{dream['distance']}m")
        print(f"   Referans: {dream['total_wins_analyzed']} galibiyet")
        
        print(f"\n{'─' * 100}")
        print("TAHMİN SONUÇLARI (İLK 5 AT)")
        print(f"{'─' * 100}")
        
        for i, pred in enumerate(results['predictions'][:5], 1):
            print(f"\n{i}. {pred['horse_name']} (#{pred['start_no']})")
            print(f"   ⭐ SKOR: {pred['score']:.2f}/100")
            print(f"   • Temel: {pred['base_score']:.2f} | İdman Bonus: +{pred['idman_bonus']:.2f} | Distance: {pred['euclidean_distance']:.2f}")
            print(f"   • Jokey: {pred['jockey']} | Antrenör: {pred['trainer']}")
            
            if pred['idman_comparison']:
                has_bonus = any(comp['faster'] for comp in pred['idman_comparison'].values())
                if has_bonus:
                    print(f"   ✓ İdman: ", end="")
                    bonuses = [f"{dist}(+{comp['bonus']:.1f})" for dist, comp in pred['idman_comparison'].items() if comp['faster']]
                    print(", ".join(bonuses))
        
        print(f"\n{'═' * 100}")
        print(f"🏆 ÖNERİ: {results['predictions'][0]['horse_name']} - {results['predictions'][0]['score']:.2f}/100")
        print(f"{'═' * 100}\n")

if __name__ == "__main__":
    test_all_races_izmir()
