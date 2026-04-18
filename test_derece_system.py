"""
Yeni derece bazlı tahmin sistemini test eder
"""
import json
from predict_race import (
    get_horse_last_race_data, 
    calculate_adjusted_100m_time,
    calculate_kadapt,
    time_to_seconds
)
from test_with_idman import load_race_from_program_with_idman

def test_derece_calculation():
    """Derece hesaplamalarını test et"""
    print("=" * 80)
    print("DERECE BAZLI TAHMİN SİSTEMİ - DETAYLI TEST")
    print("=" * 80)
    
    # İstanbul yarışını yükle
    race_horses, race_info = load_race_from_program_with_idman(
        city="Istanbul",
        year=2024,
        month=1,
        day=27,
        race_number=1
    )
    
    print(f"\nYarış: {race_info['city']} - {race_info['track_type']} {race_info['distance']}m")
    print(f"Kategori: {race_info['category']}")
    print(f"Tarih: {race_info.get('race_date')}")
    print("=" * 80)
    
    race_date = race_info.get('race_date')
    
    # Her at için detaylı analiz
    for horse in race_horses[:5]:  # İlk 5 at
        print(f"\n[AT] {horse.get('horse_name')} (#{horse.get('start_no')})")
        print("-" * 80)
        
        horse_id = horse.get('horse_id')
        print(f"Horse ID: {horse_id}")
        
        # Son yarış verilerini al (programdaki yarış tarihinden önce)
        last_race = get_horse_last_race_data(horse, race_date)
        
        if last_race:
            print("\n[SON YARIS VERILERI]:")
            print(f"  Tarih: {last_race.get('race_date')}")
            print(f"  Şehir: {last_race.get('city')}")
            print(f"  Pist: {last_race.get('track_type')}")
            print(f"  Mesafe: {last_race.get('distance')}m")
            print(f"  Derece: {last_race.get('time')}")
            print(f"  Sıra: {last_race.get('finish_position')}")
            
            # Derece saniyeye çevir
            derece_saniye = time_to_seconds(last_race.get('time'))
            if derece_saniye:
                print(f"  Derece (saniye): {derece_saniye:.2f}s")
                
                # 100m süresi
                last_distance = last_race.get('distance')
                if last_distance:
                    ort_100m = derece_saniye / (last_distance / 100)
                    print(f"  100m Süresi (ham): {ort_100m:.2f}s")
                
                # Pist adaptasyonu
                kadapt = calculate_kadapt(
                    last_race.get('city'),
                    last_race.get('track_type'),
                    race_info['city'],
                    race_info['track_type']
                )
                print(f"\n[PIST ADAPTASYONU]:")
                print(f"  k_adapt: {kadapt:.4f}")
                print(f"  Adjusted Derece: {derece_saniye * kadapt:.2f}s")
                
                # Mesafe farkı
                race_distance = race_info['distance']
                mesafe_farki = race_distance - last_distance
                print(f"\n[MESAFE ANALIZI]:")
                print(f"  Son yarış: {last_distance}m")
                print(f"  Bugünkü yarış: {race_distance}m")
                print(f"  Fark: {mesafe_farki:+d}m")
                
                # Normalize edilmiş 100m süresi
                adjusted_100m = calculate_adjusted_100m_time(
                    horse, 
                    race_info['city'], 
                    race_info['track_type'],
                    race_info['distance'],
                    race_date
                )
                
                if adjusted_100m:
                    print(f"  Adjusted 100m: {adjusted_100m:.2f}s")
                    total_predicted = adjusted_100m * (race_distance / 100)
                    print(f"  Tahmini Derece: {total_predicted:.2f}s ({int(total_predicted//60)}:{int(total_predicted%60):02d}.{int((total_predicted%1)*100):02d})")
        else:
            print("\n[UYARI] Son yaris verisi bulunamadi!")
        
        print()

if __name__ == "__main__":
    test_derece_calculation()
