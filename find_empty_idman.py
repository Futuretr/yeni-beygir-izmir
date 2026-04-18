# -*- coding: utf-8 -*-
"""
İdman Dosyası Var Ama İçi Boş Olan Atları Bul
"""
import json
from pathlib import Path

def find_empty_idman_files():
    """İdman dosyası var ama 0 kayıt olan atları bul"""
    idman_dir = Path("E:\\data\\idman")
    
    empty_horses = []
    total_files = 0
    has_idman = 0
    
    print("=" * 80)
    print("BOŞ İDMAN DOSYALARI TESPİTİ")
    print("=" * 80)
    print("\nİdman klasörleri taranıyor...")
    
    for folder in idman_dir.iterdir():
        if not folder.is_dir():
            continue
        
        for json_file in folder.glob("*.json"):
            total_files += 1
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                horse_id = int(json_file.stem)
                idman_records = data.get('idman_records', [])
                
                if len(idman_records) == 0:
                    empty_horses.append({
                        'horse_id': horse_id,
                        'file': str(json_file)
                    })
                else:
                    has_idman += 1
                
                if total_files % 5000 == 0:
                    print(f"  İşlenen: {total_files:,} dosya...", flush=True)
            
            except Exception as e:
                continue
    
    print(f"\n✓ Toplam {total_files:,} dosya tarandı")
    
    print("\n" + "=" * 80)
    print("SONUÇ")
    print("=" * 80)
    print(f"Toplam idman dosyası: {total_files:,}")
    print(f"İdmanı OLAN at: {has_idman:,}")
    print(f"İdmanı BOŞ olan at: {len(empty_horses):,}")
    print(f"Dolu dosya oranı: {has_idman/total_files*100:.1f}%")
    
    if empty_horses:
        # Boş dosyaları kaydet
        output_file = Path("E:\\data\\empty_idman_horses.json")
        
        data = {
            'total_files': total_files,
            'files_with_idman': has_idman,
            'empty_files_count': len(empty_horses),
            'empty_horses': sorted(empty_horses, key=lambda x: x['horse_id'])
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Boş idman listesi kaydedildi: {output_file}")
        
        # İlk 30 boş horse ID'yi göster
        print(f"\nİlk 30 BOŞ idman dosyası (siteden kontrol için):")
        print("-" * 80)
        for i, item in enumerate(empty_horses[:30], 1):
            horse_id = item['horse_id']
            url = f"https://www.tjk.org/TR/YarisSever/Query/Page/HorseDetail/{horse_id}"
            print(f"{i:3}. Horse ID: {horse_id:6} - {url}")
        
        # Son 30'u da göster
        if len(empty_horses) > 30:
            print(f"\nSon 30 BOŞ idman dosyası:")
            print("-" * 80)
            for i, item in enumerate(empty_horses[-30:], len(empty_horses)-29):
                horse_id = item['horse_id']
                url = f"https://www.tjk.org/TR/YarisSever/Query/Page/HorseDetail/{horse_id}"
                print(f"{i:3}. Horse ID: {horse_id:6} - {url}")
        
        print(f"\n💡 TJK sitesinde kontrol edin:")
        print(f"   https://www.tjk.org/TR/YarisSever/Query/Page/HorseDetail/[HORSE_ID]")
        print(f"   Eğer sitede de idman yoksa → Normal (yeni atlar)")
        print(f"   Eğer sitede idman varsa → Scraper sorunu")
    else:
        print("\n✅ Tüm dosyalarda idman var!")
    
    return empty_horses

if __name__ == "__main__":
    empty_horses = find_empty_idman_files()
