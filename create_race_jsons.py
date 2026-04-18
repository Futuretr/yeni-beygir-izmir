"""
Her yarış için ayrı JSON dosyası oluşturur.
Program dosyaları: E:\data\program
At profilleri: E:\data\horse_profiles
Çıktı: E:\data\race_jsons
"""

import json
import os
from pathlib import Path
from datetime import datetime

# Dizinler
PROGRAM_DIR = Path("E:/data/program")
HORSE_PROFILES_DIR = Path("E:/data/horse_profiles")
OUTPUT_DIR = Path("E:/data/race_jsons")

# Çıktı dizinini oluştur
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_horse_profile(horse_id):
    """At profilini yükle"""
    profile_file = HORSE_PROFILES_DIR / f"{horse_id}.json"
    if profile_file.exists():
        with open(profile_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def process_program_file(program_file):
    """Program dosyasını işle ve her yarış için JSON oluştur"""
    print(f"İşleniyor: {program_file}")
    
    with open(program_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Dosya yapısı: {gün: {index: [atlar]}}
    for day, day_data in data.items():
        for index, horses_list in day_data.items():
            if not horses_list:
                continue
            
            # İlk attan yarış bilgilerini al
            first_horse = horses_list[0]
            race_id = first_horse.get('race_id')
            
            if not race_id:
                continue
            
            # Yarış bilgileri
            race_data = {
                "race_id": race_id,
                "race_date": first_horse.get('race_date', '').split('T')[0] if 'T' in first_horse.get('race_date', '') else first_horse.get('race_date'),
                "race_number": first_horse.get('race_number'),
                "race_category": first_horse.get('race_category', ''),
                "age_group": first_horse.get('age_group', ''),
                "city": first_horse.get('city', ''),
                "track_type": first_horse.get('track_type', ''),
                "distance": first_horse.get('distance'),
                "horses": []
            }
            
            # Her at için bilgi ekle
            for horse_data in horses_list:
                horse_id = horse_data.get('horse_id')
                
                # At bilgileri
                horse_info = {
                    "horse_id": horse_id,
                    "horse_name": horse_data.get('horse_name', ''),
                    "horse_age": horse_data.get('horse_age', ''),
                    "horse_weight": horse_data.get('horse_weight'),
                    "handicap_weight": horse_data.get('handicap_weight'),
                    "start_no": horse_data.get('start_no'),
                    "last_6_races": horse_data.get('last_6_races', ''),
                    "kgs": horse_data.get('kgs'),
                    "ganyan": horse_data.get('ganyan'),
                    "agf": horse_data.get('agf', ''),
                    "jockey_id": horse_data.get('jockey_id'),
                    "jockey_name": horse_data.get('jockey_name', ''),
                    "trainer_id": horse_data.get('trainer_id'),
                    "trainer_name": horse_data.get('trainer_name', ''),
                    "owner_id": horse_data.get('owner_id'),
                    "owner_name": horse_data.get('owner_name', ''),
                    "father_id": horse_data.get('horse_father_id'),
                    "father_name": horse_data.get('horse_father_name', ''),
                    "mother_id": horse_data.get('horse_mother_id'),
                    "mother_name": horse_data.get('horse_mother_name', ''),
                }
                
                # At profilini yükle
                if horse_id:
                    profile = load_horse_profile(horse_id)
                    if profile:
                        # Profil ve geçmiş yarışlar
                        horse_info["profile"] = {
                            "career_summary": profile.get('career_summary', {}),
                            "city_stats": profile.get('city_stats', {}),
                            "track_stats": profile.get('track_stats', {}),
                            "distance_stats": profile.get('distance_stats', {})
                        }
                        horse_info["past_races"] = profile.get('races', [])
                    else:
                        horse_info["profile"] = None
                        horse_info["past_races"] = []
                else:
                    horse_info["profile"] = None
                    horse_info["past_races"] = []
                
                race_data["horses"].append(horse_info)
            
            # Çıktı dosyası yolu: city/year/race_id.json
            city = race_data['city']
            race_date = race_data['race_date']
            if race_date and len(race_date) >= 4:
                year = race_date[:4]
            else:
                year = "unknown"
            
            output_city_dir = OUTPUT_DIR / city / year
            output_city_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_city_dir / f"{race_id}.json"
            
            # JSON dosyasını kaydet
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump([race_data], f, ensure_ascii=False, indent=2)
            
            print(f"  ✓ Oluşturuldu: {output_file}")


def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("YARIŞ JSON DOSYALARI OLUŞTURULUYOR")
    print("=" * 60)
    print(f"Program dizini: {PROGRAM_DIR}")
    print(f"At profilleri: {HORSE_PROFILES_DIR}")
    print(f"Çıktı dizini: {OUTPUT_DIR}")
    print("=" * 60)
    
    # Tüm program dosyalarını bul ve işle
    program_files = list(PROGRAM_DIR.glob("**/*.json"))
    
    print(f"\nToplam {len(program_files)} program dosyası bulundu.")
    print()
    
    total_races = 0
    for i, program_file in enumerate(program_files, 1):
        try:
            print(f"[{i}/{len(program_files)}] ", end="")
            process_program_file(program_file)
            total_races += 1
        except Exception as e:
            print(f"  ✗ Hata: {e}")
    
    print()
    print("=" * 60)
    print(f"TAMAMLANDI! Toplam {total_races} dosya işlendi.")
    print(f"Çıktılar: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
