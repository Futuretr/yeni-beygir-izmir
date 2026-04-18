# -*- coding: utf-8 -*-
"""
Eksik İdman Tespiti - Program'daki atlardan idmanı olmayanları bul
"""
import json
from pathlib import Path
from collections import defaultdict

def get_existing_idman_ids():
    """İdman klasöründeki mevcut horse ID'leri"""
    idman_dir = Path("E:\\data\\idman")
    existing_ids = set()
    
    print("🔍 Mevcut idman dosyaları taranıyor...")
    
    folder_count = 0
    for folder in idman_dir.iterdir():
        if folder.is_dir():
            folder_count += 1
            for json_file in folder.glob("*.json"):
                try:
                    horse_id = int(json_file.stem)
                    existing_ids.add(horse_id)
                except:
                    continue
    
    print(f"   ✓ {folder_count} klasör, {len(existing_ids)} idman dosyası bulundu")
    return existing_ids

def get_program_horse_ids():
    """Program dosyalarındaki tüm horse ID'leri"""
    program_dir = Path("E:\\data\\program")
    all_horse_ids = set()
    city_stats = defaultdict(int)
    
    print("\n🔍 Program dosyalarındaki atlar taranıyor...")
    
    for city_folder in program_dir.iterdir():
        if not city_folder.is_dir():
            continue
        
        city = city_folder.name
        city_count = 0
        
        # Tüm yıl/ay dosyalarını tara
        for year_folder in city_folder.iterdir():
            if not year_folder.is_dir():
                continue
            
            for month_file in year_folder.glob("*.json"):
                try:
                    with open(month_file, 'r', encoding='utf-8') as f:
                        month_data = json.load(f)
                    
                    # Her gün için
                    for day_key, day_races in month_data.items():
                        # Her koşu için
                        for race_key, race_horses in day_races.items():
                            # Her at için
                            for horse in race_horses:
                                horse_id = horse.get('horse_id')
                                if horse_id:
                                    all_horse_ids.add(horse_id)
                                    city_count += 1
                
                except Exception as e:
                    continue
        
        if city_count > 0:
            city_stats[city] = city_count
            print(f"   {city}: {city_count} at")
    
    print(f"\n   ✓ Toplam {len(all_horse_ids)} unique at bulundu")
    return all_horse_ids, city_stats

def main():
    """Eksik idmanları tespit et"""
    print("=" * 100)
    print("EKSİK İDMAN TESPİTİ")
    print("=" * 100)
    
    # Mevcut idmanları al
    existing_ids = get_existing_idman_ids()
    
    # Program'daki atları al
    program_ids, city_stats = get_program_horse_ids()
    
    # Eksik olanları bul
    missing_ids = program_ids - existing_ids
    
    print("\n" + "=" * 100)
    print("SONUÇ")
    print("=" * 100)
    print(f"Program'daki toplam at: {len(program_ids):,}")
    print(f"İdmanı olan at: {len(existing_ids):,}")
    print(f"İdmanı EKSİK at: {len(missing_ids):,}")
    print(f"Kapsam: {len(existing_ids)/len(program_ids)*100:.1f}%")
    
    if missing_ids:
        # Eksik ID'leri kaydet
        output_file = Path("E:\\data\\missing_idman_horses.json")
        
        data = {
            'total_program_horses': len(program_ids),
            'existing_idman_count': len(existing_ids),
            'missing_idman_count': len(missing_ids),
            'coverage_percentage': len(existing_ids)/len(program_ids)*100,
            'missing_horse_ids': sorted(list(missing_ids)),
            'city_stats': dict(city_stats)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Eksik idman listesi kaydedildi: {output_file}")
        print(f"\nİlk 20 eksik horse ID:")
        for i, hid in enumerate(sorted(list(missing_ids))[:20], 1):
            print(f"  {i}. {hid}")
        
        print(f"\n💡 Bu {len(missing_ids):,} atın idmanını çekmek için:")
        print(f"   python scrape_missing_idman.py")
    else:
        print("\n✅ Tüm atların idmanı mevcut!")
    
    return sorted(list(missing_ids))

if __name__ == "__main__":
    missing_ids = main()
