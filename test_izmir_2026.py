"""
30 Ocak 2026 İzmir yarışı tahmin testi
Güncel veri ile sistemin performansını test eder
"""
from test_with_idman import load_race_from_program_with_idman
from predict_race import predict_race

def test_izmir_2026():
    """İzmir 30.01.2026 yarışını test et"""
    print("=" * 80)
    print("30 OCAK 2026 İZMİR YARIŞI - TAHMİN TESTİ")
    print("=" * 80)
    
    city = "Izmir"
    year = 2026
    month = 1
    day = 30
    
    # Koşu 1: Maiden/Satış - 8 at
    race_number = 0
    
    print(f"\nYarış: {city}, {day}.{month}.{year}, Koşu #{race_number + 1}")
    print("-" * 80)
    
    result = load_race_from_program_with_idman(city, year, month, day, race_number)
    
    if not result:
        print("Yarış yüklenemedi!")
        return
    
    race_horses, race_info = result
    
    print(f"\nYarış Bilgileri:")
    print(f"  Kategori: {race_info['category']}")
    print(f"  Şehir: {race_info['city']}")
    print(f"  Pist: {race_info['track_type']}")
    print(f"  Mesafe: {race_info['distance']}m")
    print(f"  Yaş Grubu: {race_info.get('age_group', 'N/A')}")
    print(f"  Toplam At: {len(race_horses)}")
    
    # İdman istatistiği
    idman_count = sum(1 for h in race_horses if h.get('last_idman'))
    print(f"  İdman Verisi Olan At: {idman_count}/{len(race_horses)}")
    
    print("\n" + "=" * 80)
    print("TAHMİN HESAPLANIYOR...")
    print("=" * 80)
    
    # Tahmin yap
    results = predict_race(race_horses, race_info)
    
    if 'error' in results:
        print(f"\nHata: {results['error']}")
        return
    
    dream = results['dream_horse']
    print(f"\nDream Horse: {dream['category']}/{dream['city']}/{dream['breed']}/{dream['track_type']}_{dream['distance']}m")
    print(f"Referans: {dream['total_wins_analyzed']} galibiyet analiz edildi")
    
    print("\n" + "=" * 80)
    print("KAZANMA UYUMU SKORLARI (0-100)")
    print("=" * 80)
    
    for i, pred in enumerate(results['predictions'][:10], 1):  # İlk 10 atı göster
        print(f"\n{i}. {pred['horse_name']} (#{pred['start_no']})")
        print(f"   >> SKOR: {pred['score']}/100 <<")
        print(f"   - Temel Skor: {pred['base_score']}/100")
        print(f"   - İdman Bonusu: +{pred['idman_bonus']}")
        print(f"   - Euclidean Distance: {pred['euclidean_distance']}")
        print(f"   Jokey: {pred['jockey']}")
        print(f"   Antrenör: {pred['trainer']}")
        
        if pred['idman_comparison']:
            print(f"   İdman Karşılaştırması:")
            for dist, comp in pred['idman_comparison'].items():
                if comp['faster']:
                    print(f"     >> {dist}: {comp['horse']} < {comp['dream']} (HIZLI! +{comp['bonus']} puan)")
                else:
                    print(f"     x {dist}: {comp['horse']} > {comp['dream']} (Yavaş)")
        else:
            print(f"   İdman: YOK")
    
    print("\n" + "=" * 80)
    print(f">> ÖNERİ: {results['predictions'][0]['horse_name']} en yüksek kazanma uyumuna sahip!")
    print("=" * 80)

if __name__ == "__main__":
    test_izmir_2026()
