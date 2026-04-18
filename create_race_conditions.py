import json
import os
from pathlib import Path
from datetime import datetime

def convert_time_to_seconds(time_str):
    """Convert time string like '1.37.16' to seconds"""
    if not time_str or time_str == "":
        return None
    try:
        parts = time_str.split('.')
        if len(parts) == 3:
            minutes = int(parts[0])
            seconds = int(parts[1])
            centiseconds = int(parts[2])
            return minutes * 60 + seconds + centiseconds / 100
        elif len(parts) == 2:
            seconds = int(parts[0])
            centiseconds = int(parts[1])
            return seconds + centiseconds / 100
        else:
            return float(time_str)
    except:
        return None

def convert_agf(agf_str):
    """Convert AGF string like '%19' to numeric"""
    if not agf_str or agf_str == "":
        return None
    try:
        agf_cleaned = agf_str.replace('%', '').replace(',', '.')
        return float(agf_cleaned) / 100
    except:
        return None

def get_class_level(race_category):
    """Get class level from race category"""
    if not race_category:
        return None
    
    category_upper = race_category.upper()
    
    # Level 9: KV-10, G 1
    if 'KV-10' in category_upper or 'KV 10' in category_upper:
        return 9
    if ('GROUP' in category_upper or 'GRUP' in category_upper or 'G ' in category_upper) and '1' in category_upper:
        if 'G 3' not in category_upper and 'G 2' not in category_upper and 'GRUP 3' not in category_upper and 'GRUP 2' not in category_upper:
            return 9
    
    # Level 8: KV-7, Kısa Vade 24, KV-9, G 2, A 2, Handikap 24
    if 'KV-7' in category_upper or 'KV 7' in category_upper or 'KV-9' in category_upper or 'KV 9' in category_upper:
        return 8
    if 'KISA VADE 24' in category_upper or 'KISA V 24' in category_upper:
        return 8
    if 'A 2' in category_upper or 'A2' in category_upper:
        return 8
    if 'HANDIKAP 24' in category_upper or 'HANDİKAP 24' in category_upper:
        return 8
    if ('GROUP' in category_upper or 'GRUP' in category_upper or 'G ' in category_upper) and '2' in category_upper:
        if 'G 3' not in category_upper and 'GRUP 3' not in category_upper:
            return 8
    
    # Level 7: KV-6, Handikap 21, Kısa Vade 22, KV-8, G 3, A 3, Handikap 22
    if 'KV-6' in category_upper or 'KV 6' in category_upper or 'KV-8' in category_upper or 'KV 8' in category_upper:
        return 7
    if 'KISA VADE 22' in category_upper or 'KISA V 22' in category_upper:
        return 7
    if 'A 3' in category_upper or 'A3' in category_upper:
        return 7
    if 'HANDIKAP 21' in category_upper or 'HANDİKAP 21' in category_upper:
        return 7
    if 'HANDIKAP 22' in category_upper or 'HANDİKAP 22' in category_upper:
        return 7
    if ('GROUP' in category_upper or 'GRUP' in category_upper or 'G ' in category_upper) and '3' in category_upper:
        return 7
    
    # Level 6: Şartlı 5, Handikap 17, Satış 4
    if 'ŞARTLI 5' in category_upper or 'SARTLI 5' in category_upper:
        return 6
    if 'HANDIKAP 17' in category_upper or 'HANDİKAP 17' in category_upper:
        return 6
    if 'SATIŞ 4' in category_upper or 'SATIS 4' in category_upper:
        return 6
    
    # Level 5: Şartlı 4, Handikap 16, Satış 3
    if 'ŞARTLI 4' in category_upper or 'SARTLI 4' in category_upper:
        return 5
    if 'HANDIKAP 16' in category_upper or 'HANDİKAP 16' in category_upper:
        return 5
    if 'SATIŞ 3' in category_upper or 'SATIS 3' in category_upper:
        return 5
    
    # Level 4: Şartlı 3, Handikap 15, Satış 2
    if 'ŞARTLI 3' in category_upper or 'SARTLI 3' in category_upper:
        return 4
    if 'HANDIKAP 15' in category_upper or 'HANDİKAP 15' in category_upper:
        return 4
    if 'SATIŞ 2' in category_upper or 'SATIS 2' in category_upper:
        return 4
    
    # Level 3: Şartlı 2, Handikap 14, Satış 1
    if 'ŞARTLI 2' in category_upper or 'SARTLI 2' in category_upper:
        return 3
    if 'HANDIKAP 14' in category_upper or 'HANDİKAP 14' in category_upper:
        return 3
    if 'SATIŞ 1' in category_upper or 'SATIS 1' in category_upper:
        return 3
    
    # Level 2: Maiden, Handikap 13, Şartlı 19
    if 'MAIDEN' in category_upper:
        return 2
    if 'HANDIKAP 13' in category_upper or 'HANDİKAP 13' in category_upper:
        return 2
    if 'ŞARTLI 19' in category_upper or 'SARTLI 19' in category_upper:
        return 2
    
    # Level 1: Şartlı 1
    if 'ŞARTLI 1' in category_upper or 'SARTLI 1' in category_upper:
        return 1
    
    return 4

def extract_horse_type(age_group):
    """Extract horse type from age_group"""
    if not age_group:
        return None
    
    if 'İngiliz' in age_group or 'Ingiliz' in age_group:
        return 'İngiliz'
    elif 'Arap' in age_group:
        return 'Arap'
    else:
        return None

def calculate_favorite_win_rate(agf):
    """Estimate favorite win rate based on average AGF"""
    if agf is None:
        return None
    # This is a simplified calculation - higher AGF generally means favorites win more
    # AGF around 0.15-0.25 typically indicates 30-40% favorite win rate
    if agf >= 0.25:
        return 0.45
    elif agf >= 0.20:
        return 0.40
    elif agf >= 0.15:
        return 0.35
    else:
        return 0.30

def create_condition_id(category, city, track_type, distance, horse_type):
    """Create a unique condition ID for quick lookup"""
    # Abbreviate category
    cat_abbr = category.upper()
    cat_abbr = cat_abbr.replace('HANDIKAP', 'H').replace('HANDİKAP', 'H')
    cat_abbr = cat_abbr.replace('ŞARTLI', 'S').replace('SARTLI', 'S')
    cat_abbr = cat_abbr.replace('MAIDEN', 'M')
    cat_abbr = cat_abbr.replace('SATIŞ', 'ST').replace('SATIS', 'ST')
    cat_abbr = cat_abbr.replace('KISA VADE', 'KV').replace('KISA V', 'KV')
    cat_abbr = cat_abbr.replace('AMATÖR BINICI', 'AB').replace('AMATOR BINICI', 'AB')
    cat_abbr = cat_abbr.replace('GROUP', 'G').replace('GRUP', 'G')
    cat_abbr = cat_abbr.replace(' ', '').replace('/', '_')
    
    # Clean city name
    city_clean = city.upper().replace(' ', '_')
    
    # Clean track type
    track_clean = track_type.upper()
    track_clean = track_clean.replace('Ç', 'C').replace('Ğ', 'G').replace('İ', 'I')
    track_clean = track_clean.replace('Ö', 'O').replace('Ü', 'U').replace('Ş', 'S')
    track_clean = track_clean.replace('ı', 'I').replace('ç', 'C').replace('ğ', 'G')
    track_clean = track_clean.replace('ö', 'O').replace('ü', 'U').replace('ş', 'S')
    
    # Clean horse type
    horse_clean = horse_type.upper() if horse_type else 'UNKNOWN'
    horse_clean = horse_clean.replace('İ', 'I').replace('ı', 'I')
    
    return f"{cat_abbr}_{city_clean}_{track_clean}_{distance}_{horse_clean}"

def process_dream_horse_file(dream_file, output_dir):
    """Process a single dream horse file and create race condition profile"""
    try:
        with open(dream_file, 'r', encoding='utf-8') as f:
            dream_data = json.load(f)
        
        # Extract basic info
        main_category = dream_data.get('main_category', dream_data.get('race_category', ''))
        city = dream_data.get('city')
        track_type = dream_data.get('track_type')
        distance = dream_data.get('distance')
        age_group = dream_data.get('age_group', '')
        
        # Get horse type
        horse_type = extract_horse_type(age_group)
        
        # Get class level
        class_level = get_class_level(main_category)
        
        # Create condition ID
        condition_id = create_condition_id(main_category, city, track_type, distance, horse_type)
        
        # Get metadata
        metadata = dream_data.get('_metadata', {})
        total_wins = metadata.get('total_wins_analyzed', 0)
        
        # Convert values
        avg_weight = float(dream_data.get('horse_weight', 0)) if dream_data.get('horse_weight') else None
        avg_handicap = float(dream_data.get('handicap_weight', 0)) if dream_data.get('handicap_weight') else None
        avg_time_sec = convert_time_to_seconds(dream_data.get('time', ''))
        avg_agf = convert_agf(dream_data.get('agf', ''))
        
        # Calculate favorite win rate
        fav_win_rate = calculate_favorite_win_rate(avg_agf)
        
        # Create race condition profile
        race_condition = {
            "profile_type": "race_condition",
            "condition_id": condition_id,
            "race_category": main_category,
            "class_level": class_level,
            "city": city,
            "track_type": track_type,
            "distance": distance,
            "horse_type": horse_type,
            "stats": {
                "total_races_analyzed": total_wins,
                "avg_time_sec": round(avg_time_sec, 2) if avg_time_sec else None,
                "avg_winner_weight": round(avg_weight, 1) if avg_weight else None,
                "avg_handicap_weight": round(avg_handicap, 1) if avg_handicap else None,
                "avg_winner_agf": round(avg_agf, 2) if avg_agf else None,
                "favorite_win_rate": round(fav_win_rate, 2) if fav_win_rate else None
            },
            "_metadata": {
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
        }
        
        # Create filename: category_city_track_distance_horsetype.json
        # Clean names for filename
        category_clean = main_category.replace(' ', '_').replace('/', '_')
        track_clean = track_type.replace('ı', 'i').replace('ç', 'c').replace('ğ', 'g').replace('ö', 'o').replace('ü', 'u').replace('ş', 's').replace('İ', 'I').replace('Ç', 'C').replace('Ğ', 'G').replace('Ö', 'O').replace('Ü', 'U').replace('Ş', 'S')
        horsetype_clean = horse_type.replace('İ', 'I').replace('ı', 'i') if horse_type else 'unknown'
        
        filename = f"{category_clean}_{city}_{track_clean}_{distance}m_{horsetype_clean}.json"
        output_path = output_dir / filename
        
        # Write JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(race_condition, f, indent=2, ensure_ascii=False)
        
        return True
    
    except Exception as e:
        print(f"Error processing {dream_file}: {e}")
        return False

def main():
    dream_horse_dir = Path(r"E:\data\stats\dream_horse")
    output_dir = Path(r"E:\data\race_condition")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Processing dream horse files to race conditions...")
    
    created_count = 0
    
    # Walk through all directories
    for category_dir in dream_horse_dir.iterdir():
        if not category_dir.is_dir():
            continue
        
        for city_dir in category_dir.iterdir():
            if not city_dir.is_dir():
                continue
            
            for horse_type_dir in city_dir.iterdir():
                if not horse_type_dir.is_dir():
                    continue
                
                # Process all JSON files in this directory
                for json_file in horse_type_dir.glob("*.json"):
                    if process_dream_horse_file(json_file, output_dir):
                        created_count += 1
                        
                        if created_count % 50 == 0:
                            print(f"Created {created_count} race condition profiles")
    
    print(f"\n✅ COMPLETED!")
    print(f"Total race condition profiles created: {created_count}")
    print(f"Output directory: {output_dir}")
    
    # Show sample
    if created_count > 0:
        sample_file = list(output_dir.glob("*.json"))[0]
        print(f"\n📄 Sample profile: {sample_file.name}")
        with open(sample_file, 'r', encoding='utf-8') as f:
            sample = json.load(f)
        print(json.dumps(sample, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
