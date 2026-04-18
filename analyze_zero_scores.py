# -*- coding: utf-8 -*-
"""
Neden çoğu atın skoru 0 - Analiz
"""
import sys
import io
from test_with_idman import load_race_from_program_with_idman
from predict_race import (
    get_horse_last_race_data, 
    calculate_adjusted_100m_time,
    extract_weight,
    time_to_seconds
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_zero_scores():
    """Neden skor 0 çıkıyor - analiz"""
    
    city = "Izmir"
    year = 2026
    month = 1
    day = 30
    race_number = 0  # İlk koşu
    
    result = load_race_from_program_with_idman(city, year, month, day, race_number)
    race_horses, race_info = result
    
    print("=" * 100)
    print("NEDEN SKOR 0? - DETAYLI ANALİZ")
    print("=" * 100)
    print(f"\nYarış: {race_info['category']} - {race_info['distance']}m")
    print(f"Dream Horse: E:\\data\\stats\\dream_horse\\{race_info['category']}\\{race_info['city']}\\...")
    
    race_date = race_info.get('race_date')
    
    for horse in race_horses[:5]:
        print(f"\n{'='*100}")
        print(f"AT: {horse.get('horse_name')} (#{horse.get('start_no')})")
        print(f"{'='*100}")
        
        horse_id = horse.get('horse_id')
        horse_weight = extract_weight(horse.get('horse_weight'))
        horse_hw = extract_weight(horse.get('handicap_weight'))
        
        print(f"\n[PROGRAM VERİLERİ]")
        print(f"  Horse ID: {horse_id}")
        print(f"  Kilo: {horse_weight} kg")
        print(f"  Handicap: {horse_hw or 'YOK'}")
        
        # Son yarış verisi
        last_race = get_horse_last_race_data(horse, race_date)
        
        if last_race:
            print(f"\n[SON YARIŞ - {last_race.get('race_date')[:10]}]")
            print(f"  Şehir: {last_race.get('city')}")
            print(f"  Pist: {last_race.get('track_type')}")
            print(f"  Mesafe: {last_race.get('distance')}m")
            print(f"  Derece: {last_race.get('time')}")
            print(f"  Sıra: {last_race.get('finish_position')}")
            
            # 100m hesabı
            adjusted_100m = calculate_adjusted_100m_time(
                horse, 
                race_info['city'], 
                race_info['track_type'],
                race_info['distance'],
                race_date
            )
            
            if adjusted_100m:
                print(f"  Adjusted 100m: {adjusted_100m:.2f}s")
            else:
                print(f"  Adjusted 100m: HESAPLANAMADI!")
        else:
            print(f"\n[SON YARIŞ]")
            print(f"  BULUNAMADI! (Horses klasöründe {horse_id} yok veya önceki yarış yok)")
        
        print(f"\n[EUCLIDEAN DISTANCE BİLEŞENLERİ]")
        
        # Weight diff
        if horse_weight:
            print(f"  Kilo farkı karesinin kökü var")
        
        # Handicap diff
        if horse_hw:
            print(f"  Handicap farkı karesinin kökü var")
        
        # Derece diff
        if last_race:
            adjusted_100m = calculate_adjusted_100m_time(
                horse, 
                race_info['city'], 
                race_info['track_type'],
                race_info['distance'],
                race_date
            )
            
            if adjusted_100m:
                print(f"  Derece farkı: VAR (100m={adjusted_100m:.2f}s) × 10 çarpan = ÇOK YÜKSEK ETKİ!")
            else:
                print(f"  Derece farkı: HESAPLANAMADI")
        else:
            print(f"  Derece farkı: YOK (son yarış bulunamadı)")
        
        print(f"\n[SORUN]")
        if not last_race:
            print(f"  ❌ Son yarış bulunamadığı için distance varsayılan 10.0")
            print(f"  ❌ Base score = 100 - (10.0 × 10) = 0")
        elif adjusted_100m:
            print(f"  ❌ Derece farkı çok yüksekse distance > 10 olur")
            print(f"  ❌ Base score = 100 - (distance × 10) = negatif → 0")
        else:
            print(f"  ❌ 100m hesaplanamadı, distance yüksek çıkabilir")

if __name__ == "__main__":
    analyze_zero_scores()
