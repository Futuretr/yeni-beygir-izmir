"""
E:\data\program klasöründeki tüm JSON'lardan unique horse_id'leri topla
"""
import json
import os
from pathlib import Path

PROGRAM_DIR = r"E:\data\program"
OUTPUT_FILE = r"E:\data\all_horse_ids.json"

def collect_horse_ids():
    """Tüm JSON dosyalarından unique horse_id'leri topla"""
    horse_ids = set()  # SET kullanıyoruz - her ID sadece 1 kere eklenir!
    total_files = 0
    total_horses = 0  # Toplam kayıt sayısı (aynı at birden fazla yarışta olabilir)
    
    print("🔍 JSON dosyaları taranıyor...")
    print("⚠️  SET kullanılıyor - her at ID'si sadece BİR KERE eklenecek!\n")
    
    # Tüm şehir klasörlerini tara
    for city_dir in Path(PROGRAM_DIR).iterdir():
        if not city_dir.is_dir():
            continue
            
        print(f"📂 {city_dir.name} taranıyor...")
        
        # Tüm JSON dosyalarını bul
        for json_file in city_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_files += 1
                    
                    # Her gün için (day_key: "02", "15", etc.)
                    for day_key, day_data in data.items():
                        # day_data bir dict: {"0": [...], "1": [...]}
                        if isinstance(day_data, dict):
                            for race_num, horses in day_data.items():
                                if isinstance(horses, list):
                                    for horse in horses:
                                        if 'horse_id' in horse and horse['horse_id']:
                                            horse_ids.add(horse['horse_id'])  # SET - otomatik unique
                                            total_horses += 1
                        # Eski format: day_data bir list
                        elif isinstance(day_data, list):
                            for horse in day_data:
                                if 'horse_id' in horse and horse['horse_id']:
                                    horse_ids.add(horse['horse_id'])
                                    total_horses += 1
            except Exception as e:
                print(f"⚠️ Hata ({json_file}): {e}")
                continue
    
    # Sırala ve kaydet
    horse_ids_sorted = sorted(list(horse_ids))
    
    # JSON olarak kaydet
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "total_unique_horses": len(horse_ids_sorted),
            "total_records": total_horses,
            "total_files": total_files,
            "horse_ids": horse_ids_sorted
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ TAMAMLANDI!")
    print(f"Taranan dosya: {total_files}")
    print(f"Toplam kayıt: {total_horses:,} (aynı at birden fazla yarışta)")
    print(f"Unique at: {len(horse_ids_sorted):,} ⭐ (her at sadece 1 kere)")
    if len(horse_ids_sorted) > 0:
        print(f"Tekrar oranı: {total_horses / len(horse_ids_sorted):.1f}x (ortalama her at {total_horses / len(horse_ids_sorted):.1f} yarışta)")
    print(f"Çıktı: {OUTPUT_FILE}")
    print(f"{'='*80}")
    
    return horse_ids_sorted

if __name__ == "__main__":
    collect_horse_ids()
