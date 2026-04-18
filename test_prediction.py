import json
from pathlib import Path
from predict_race import predict_race

def load_race_from_program(city, year, month, day, race_number):
    """Program dosyasından yarış yükle"""
    program_dir = Path("E:\\data\\program")
    
    # Dosya yolu: E:\data\program\{city}\{year}\{month}.json
    month_str = str(month).zfill(2)  # 1 -> "01"
    program_file = program_dir / city / str(year) / f"{month_str}.json"
    
    if not program_file.exists():
        print(f"Program dosyası bulunamadı: {program_file}")
        return None
    
    try:
        with open(program_file, 'r', encoding='utf-8') as f:
            month_data = json.load(f)
        
        # Gün ve yarış numarasına göre bul
        day_key = str(day)
        race_key = str(race_number)
        
        if day_key not in month_data:
            print(f"Bu gün için veri yok: {day}")
            return None
        
        if race_key not in month_data[day_key]:
            print(f"Bu yarış numarası için veri yok: {race_number}")
            return None
        
        race_horses = month_data[day_key][race_key]
        
        if not race_horses or len(race_horses) == 0:
            print("Yarışta at yok")
            return None
        
        # İlk atın bilgilerinden yarış bilgilerini al
        first_horse = race_horses[0]
        
        race_info = {
            'category': first_horse.get('race_category', '').split('/')[0].strip(),
            'city': first_horse.get('city'),
            'track_type': first_horse.get('track_type'),
            'distance': first_horse.get('distance'),
            'age_group': first_horse.get('age_group'),
            'race_date': first_horse.get('race_date'),
            'race_number': race_number
        }
        
        return race_horses, race_info
        
    except Exception as e:
        print(f"Hata: {e}")
        return None

def test_prediction():
    """Test tahmin"""
    print("=" * 80)
    print("AT YARIŞI TAHMİN SİSTEMİ - TEST")
    print("=" * 80)
    
    # Örnek: Istanbul, 2024, 1 (Ocak), 27. gün, 3. yarış
    city = "Istanbul"
    year = 2024
    month = 1
    day = 27
    race_number = 3
    
    print(f"\nYarış: {city}, {day}.{month}.{year}, Koşu #{race_number}")
    print("-" * 80)
    
    result = load_race_from_program(city, year, month, day, race_number)
    
    if not result:
        print("Yarış yüklenemedi!")
        return
    
    race_horses, race_info = result
    
    print(f"\nYarış Bilgileri:")
    print(f"  Kategori: {race_info['category']}")
    print(f"  Şehir: {race_info['city']}")
    print(f"  Pist: {race_info['track_type']}")
    print(f"  Mesafe: {race_info['distance']}m")
    print(f"  Yaş Grubu: {race_info['age_group']}")
    print(f"  Toplam At: {len(race_horses)}")
    
    print("\n" + "=" * 80)
    print("TAHMİN HESAPLANIYOR...")
    print("=" * 80)
    
    # Tahmin yap
    predictions = predict_race(race_horses, race_info)
    
    if 'error' in predictions:
        print(f"\nHATA: {predictions['error']}")
        return
    
    # Sonuçları göster
    dream = predictions['dream_horse']
    print(f"\nDream Horse: {dream['category']}/{dream['city']}/{dream['breed']}/{dream['track_type']}_{dream['distance']}m")
    print(f"Referans: {dream['total_wins_analyzed']} galibiyet analiz edildi")
    
    print("\n" + "=" * 80)
    print("KAZANMA UYUMU SKORLARI (0-100)")
    print("=" * 80)
    
    for i, pred in enumerate(predictions['predictions'], 1):
        print(f"\n{i}. {pred['horse_name']} (#{pred['start_no']})")
        print(f"   Skor: {pred['score']}/100")
        print(f"   - Temel Skor: {pred['base_score']}/100 (Euclidean Distance: {pred['euclidean_distance']})")
        print(f"   - İdman Bonusu: +{pred['idman_bonus']}")
        print(f"   Jokey: {pred['jockey']}")
        print(f"   Antrenör: {pred['trainer']}")
        
        if pred['idman_comparison']:
            print(f"   İdman Karşılaştırması:")
            for dist, comp in pred['idman_comparison'].items():
                status = "✓ HIZLI" if comp['faster'] else "✗ Yavaş"
                print(f"     {dist}: {comp['horse']} vs {comp['dream']} {status} (+{comp['bonus']} puan)")
    
    print("\n" + "=" * 80)
    print(f"ÖNERİ: İlk 3 at en yüksek kazanma uyumuna sahip!")
    print("=" * 80)

if __name__ == "__main__":
    test_prediction()
