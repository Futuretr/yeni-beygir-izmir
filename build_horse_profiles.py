import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def convert_time_to_seconds(time_str):
    """Convert time string like '1.32.02' to seconds"""
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

def get_class_level_numeric(race_category):
    """Convert race category to numeric class level
    1 - Şartlı 1
    2 - Maiden, Handikap 13, Şartlı 19
    3 - Şartlı 2, Handikap 14, Satış 1
    4 - Şartlı 3, Handikap 15, Satış 2
    5 - Şartlı 4, Handikap 16, Satış 3
    6 - Şartlı 5, Handikap 17, Satış 4
    7 - KV-6, Handikap 21, Kısa Vade 22, KV-8, G 3, A 3, Handikap 22
    8 - KV-7, Kısa Vade 24, KV-9, G 2, A 2, Handikap 24
    9 - KV-10, G 1
    """
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
    
    # Default
    return 4

def calculate_days_ago(race_date, reference_date):
    """Calculate days between two dates"""
    try:
        race_dt = datetime.strptime(race_date, "%Y-%m-%d")
        ref_dt = datetime.strptime(reference_date, "%Y-%m-%d")
        return (ref_dt - race_dt).days
    except:
        return None

def clean_race_data(raw_race):
    """Convert raw race data to clean format (without leakage data)"""
    race_date_str = raw_race.get('race_date', '')
    if race_date_str:
        try:
            race_date = datetime.fromisoformat(race_date_str.replace('Z', '+00:00'))
            race_date_formatted = race_date.strftime('%Y-%m-%d')
        except:
            race_date_formatted = race_date_str.split('T')[0] if 'T' in race_date_str else race_date_str
    else:
        race_date_formatted = None
    
    # Convert finish_position to int
    try:
        finish_pos = int(raw_race.get('finish_position', 0))
    except:
        finish_pos = None
    
    # Convert time to seconds
    time_sec = convert_time_to_seconds(raw_race.get('time', ''))
    
    # Convert horse_weight
    try:
        horse_weight = float(raw_race.get('horse_weight', 0)) if raw_race.get('horse_weight') else None
    except:
        horse_weight = None
    
    # Get class level
    class_level = get_class_level_numeric(raw_race.get('race_category', ''))
    
    return {
        "race_id": raw_race.get('race_id'),
        "date": race_date_formatted,
        "city": raw_race.get('city'),
        "track_type": raw_race.get('track_type'),
        "distance": raw_race.get('distance'),
        "class_level": class_level,
        "finish_position": finish_pos,
        "time_sec": time_sec,
        "horse_weight": horse_weight,
        "jockey_id": raw_race.get('jockey_id'),
        "trainer_id": raw_race.get('trainer_id')
    }

def create_horse_profile(horse_id, races):
    """Create complete horse profile with statistics"""
    
    # Filter out races with invalid data
    valid_races = [r for r in races if r.get("date") and r.get("finish_position")]
    
    if not valid_races:
        return None
    
    # Sort races by date (oldest to newest)
    sorted_races = sorted(valid_races, key=lambda x: x.get("date", ""))
    
    # Career summary calculations
    total_races = len(sorted_races)
    
    finish_positions = [r["finish_position"] for r in sorted_races if r.get("finish_position")]
    avg_finish_position = sum(finish_positions) / len(finish_positions) if finish_positions else None
    
    times = [r["time_sec"] for r in sorted_races if r.get("time_sec")]
    avg_time_sec = sum(times) / len(times) if times else None
    
    # Class level ortalaması
    class_levels = [r["class_level"] for r in sorted_races if r.get("class_level")]
    avg_class_level = sum(class_levels) / len(class_levels) if class_levels else None
    
    # Last race days ago (from today: 2026-02-03)
    today = "2026-02-03"
    last_race_date = sorted_races[-1].get("date") if sorted_races else None
    last_race_days_ago = calculate_days_ago(last_race_date, today) if last_race_date else None
    
    # City stats
    city_stats = defaultdict(lambda: {"races": 0, "finish_positions": [], "times": []})
    for race in sorted_races:
        city = race.get("city")
        if city:
            city_stats[city]["races"] += 1
            if race.get("finish_position"):
                city_stats[city]["finish_positions"].append(race["finish_position"])
            if race.get("time_sec"):
                city_stats[city]["times"].append(race["time_sec"])
    
    city_stats_final = {}
    for city, stats in city_stats.items():
        city_stats_final[city] = {
            "races": stats["races"],
            "avg_finish": round(sum(stats["finish_positions"]) / len(stats["finish_positions"]), 2) if stats["finish_positions"] else None
        }
    
    # Track stats
    track_stats = defaultdict(lambda: {"races": 0, "finish_positions": [], "times": []})
    for race in sorted_races:
        track = race.get("track_type")
        if track:
            track_stats[track]["races"] += 1
            if race.get("finish_position"):
                track_stats[track]["finish_positions"].append(race["finish_position"])
            if race.get("time_sec"):
                track_stats[track]["times"].append(race["time_sec"])
    
    track_stats_final = {}
    for track, stats in track_stats.items():
        track_stats_final[track] = {
            "races": stats["races"],
            "avg_time": round(sum(stats["times"]) / len(stats["times"]), 2) if stats["times"] else None
        }
    
    # Distance stats - TRACK TYPE VE ŞEHİR AYRIMLI
    # Her mesafe için track_type ve city'ye göre ayrı stats
    distance_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"races": 0, "finish_positions": [], "times": []})))
    for race in sorted_races:
        distance = race.get("distance")
        track_type = race.get("track_type")
        city = race.get("city")
        if distance and track_type and city:
            distance_stats[distance][track_type][city]["races"] += 1
            if race.get("finish_position"):
                distance_stats[distance][track_type][city]["finish_positions"].append(race["finish_position"])
            if race.get("time_sec"):
                distance_stats[distance][track_type][city]["times"].append(race["time_sec"])
    
    distance_stats_final = {}
    for distance, track_dict in distance_stats.items():
        distance_stats_final[str(distance)] = {}
        for track_type, city_dict in track_dict.items():
            distance_stats_final[str(distance)][track_type] = {}
            for city, stats in city_dict.items():
                distance_stats_final[str(distance)][track_type][city] = {
                    "races": stats["races"],
                    "avg_finish": round(sum(stats["finish_positions"]) / len(stats["finish_positions"]), 2) if stats["finish_positions"] else None,
                    "avg_time": round(sum(stats["times"]) / len(stats["times"]), 2) if stats["times"] else None
                }
    
    # Create profile
    profile = {
        "horse_id": horse_id,
        "career_summary": {
            "total_races": total_races,
            "avg_finish_position": round(avg_finish_position, 2) if avg_finish_position else None,
            "avg_time_sec": round(avg_time_sec, 2) if avg_time_sec else None,
            "avg_class_level": round(avg_class_level, 2) if avg_class_level else None,
            "last_race_days_ago": last_race_days_ago
        },
        "city_stats": city_stats_final,
        "track_stats": track_stats_final,
        "distance_stats": distance_stats_final,
        "races": sorted_races
    }
    
    return profile

def process_horse_file(horse_file_path, output_dir):
    """Process a single horse JSON file and create profile"""
    try:
        with open(horse_file_path, 'r', encoding='utf-8') as f:
            horse_data = json.load(f)
        
        horse_id = horse_data.get('horse_id')
        raw_races = horse_data.get('races', [])
        
        if not raw_races:
            return False
        
        # Clean all races
        cleaned_races = []
        for raw_race in raw_races:
            clean_race = clean_race_data(raw_race)
            # Only add if has valid finish position
            if clean_race.get("finish_position") and clean_race.get("date"):
                cleaned_races.append(clean_race)
        
        if not cleaned_races:
            return False
        
        # Create profile
        profile = create_horse_profile(horse_id, cleaned_races)
        
        if not profile:
            return False
        
        # Save profile
        output_path = output_dir / f"{horse_id}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        return True
    
    except Exception as e:
        print(f"Error processing {horse_file_path}: {e}")
        return False

def main():
    horses_dir = Path(r"E:\data\horses")
    output_dir = Path(r"E:\data\horse_profiles")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all horse folders
    horse_folders = [f for f in horses_dir.iterdir() if f.is_dir()]
    
    total_profiles_created = 0
    total_horses = len(horse_folders)
    
    print(f"Processing {total_horses} horses directly to profiles...")
    
    for idx, horse_folder in enumerate(horse_folders, 1):
        horse_id = horse_folder.name
        json_file = horse_folder / f"{horse_id}.json"
        
        if json_file.exists():
            created = process_horse_file(json_file, output_dir)
            if created:
                total_profiles_created += 1
            
            if idx % 500 == 0:
                print(f"Processed {idx}/{total_horses} horses, created {total_profiles_created} profiles")
    
    print(f"\n✅ COMPLETED!")
    print(f"Total horses processed: {total_horses}")
    print(f"Total profiles created: {total_profiles_created}")
    print(f"Output directory: {output_dir}")
    
    # Show sample
    if total_profiles_created > 0:
        sample_file = list(output_dir.glob("*.json"))[0]
        print(f"\n📄 Sample profile: {sample_file.name}")
        with open(sample_file, 'r', encoding='utf-8') as f:
            sample = json.load(f)
        print(f"   Horse ID: {sample['horse_id']}")
        print(f"   Total races: {sample['career_summary']['total_races']}")
        print(f"   Avg finish: {sample['career_summary']['avg_finish_position']}")
        print(f"   Last race days ago: {sample['career_summary']['last_race_days_ago']}")

if __name__ == "__main__":
    main()
