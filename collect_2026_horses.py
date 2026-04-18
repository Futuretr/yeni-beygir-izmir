# -*- coding: utf-8 -*-
"""
2026 Yarışlarındaki Atların Horse ID'lerini Topla
"""
import json
from pathlib import Path
from collections import defaultdict

def collect_2026_horse_ids():
    """2026 yılındaki tüm yarışlardaki atları topla"""
    program_dir = Path("E:\\data\\program")
    horse_ids = set()
    race_count = 0
    city_stats = defaultdict(int)
    
    print("=" * 80)
    print("2026 YARIŞLARINDA HORSE ID TOPLAMA")
    print("=" * 80)
    
    # Tüm şehirleri tara
    for city_folder in program_dir.iterdir():
        if not city_folder.is_dir():
            continue
        
        city = city_folder.name
        year_folder = city_folder / "2026"
        
        if not year_folder.exists():
            continue
        
        print(f"\n📍 {city} 2026 yarışları kontrol ediliyor...")
        
        # Tüm ay dosyalarını tara
        for month_file in year_folder.glob("*.json"):
            try:
                with open(month_file, 'r', encoding='utf-8') as f:
                    month_data = json.load(f)
                
                # Her gün için
                for day_key, day_races in month_data.items():
                    # Her koşu için
                    for race_key, race_horses in day_races.items():
                        race_count += 1
                        
                        # Her at için
                        for horse in race_horses:
                            horse_id = horse.get('horse_id')
                            if horse_id:
                                horse_ids.add(horse_id)
                                city_stats[city] += 1
            
            except Exception as e:
                print(f"   ❌ Hata {month_file.name}: {e}")
                continue
        
        print(f"   ✓ {city}: {city_stats[city]} at")
    
    print("\n" + "=" * 80)
    print("ÖZET")
    print("=" * 80)
    print(f"Toplam yarış: {race_count}")
    print(f"Unique at sayısı: {len(horse_ids)}")
    print(f"\nŞehir bazında:")
    for city, count in sorted(city_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {city}: {count} at")
    
    # Listeyi kaydet
    output_file = Path("E:\\data\\horse_ids_2026.json")
    
    data = {
        'year': 2026,
        'total_races': race_count,
        'total_unique_horses': len(horse_ids),
        'horse_ids': sorted(list(horse_ids)),
        'city_stats': dict(city_stats)
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Horse ID'ler kaydedildi: {output_file}")
    print(f"   {len(horse_ids)} unique at")
    
    # İlk 10 ID'yi göster
    print(f"\nİlk 10 horse ID:")
    for i, hid in enumerate(sorted(list(horse_ids))[:10], 1):
        print(f"  {i}. {hid}")
    
    return sorted(list(horse_ids))

if __name__ == "__main__":
    horse_ids = collect_2026_horse_ids()
