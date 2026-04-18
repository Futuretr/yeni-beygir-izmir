import json
import os
from pathlib import Path
from datetime import datetime

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

def convert_ganyan(ganyan_str):
    """Convert ganyan string like '12,25' to float"""
    if not ganyan_str or ganyan_str == "":
        return None
    try:
        return float(ganyan_str.replace(',', '.'))
    except:
        return None

def convert_agf(agf_str):
    """Convert AGF string like '%5' to numeric"""
    if not agf_str or agf_str == "":
        return None
    try:
        # Remove % sign and convert to decimal
        agf_cleaned = agf_str.replace('%', '').replace(',', '.')
        return float(agf_cleaned) / 100 if float(agf_cleaned) > 1 else float(agf_cleaned)
    except:
        return None

def get_class_level_numeric(race_category):
    """Convert race category to numeric class level"""
    if not race_category:
        return None
    
    category_upper = race_category.upper()
    
    # ŞARTLI mapping
    if 'ŞARTLI' in category_upper or 'SARTLI' in category_upper:
        if '1' in category_upper:
            return 1
        elif '2' in category_upper:
            return 2
        elif '3' in category_upper:
            return 3
        elif '4' in category_upper:
            return 4
        elif '5' in category_upper:
            return 5
        elif '6' in category_upper:
            return 6
        elif '7' in category_upper:
            return 7
    
    # Other categories
    if 'MAIDEN' in category_upper:
        return 0
    elif 'LİSTED' in category_upper or 'LISTED' in category_upper:
        return 8
    elif 'GROUP' in category_upper or 'GRUP' in category_upper:
        if 'III' in category_upper or '3' in category_upper:
            return 9
        elif 'II' in category_upper or '2' in category_upper:
            return 10
        elif 'I' in category_upper or '1' in category_upper:
            return 11
    
    return 4  # Default

def process_horse_file(horse_file_path, output_dir):
    """Process a single horse JSON file and create ML format JSONs"""
    try:
        with open(horse_file_path, 'r', encoding='utf-8') as f:
            horse_data = json.load(f)
        
        horse_id = horse_data.get('horse_id')
        races = horse_data.get('races', [])
        
        if not races:
            return 0
        
        created_count = 0
        
        for race in races:
            # Convert finish_position to int
            try:
                finish_pos = int(race.get('finish_position', 0))
            except:
                continue
            
            # Skip if invalid finish position
            if finish_pos <= 0:
                continue
            
            # Parse race_date
            race_date_str = race.get('race_date', '')
            if race_date_str:
                try:
                    race_date = datetime.fromisoformat(race_date_str.replace('Z', '+00:00'))
                    race_date_formatted = race_date.strftime('%Y-%m-%d')
                except:
                    race_date_formatted = race_date_str.split('T')[0] if 'T' in race_date_str else race_date_str
            else:
                continue
            
            # Convert time to seconds
            time_sec = convert_time_to_seconds(race.get('time', ''))
            
            # Convert ganyan
            ganyan = convert_ganyan(race.get('ganyan', ''))
            
            # Convert AGF
            agf = convert_agf(race.get('agf', ''))
            
            # Convert weights
            try:
                horse_weight = float(race.get('horse_weight', 0)) if race.get('horse_weight') else None
            except:
                horse_weight = None
            
            try:
                handicap_weight = float(race.get('handicap_weight', 0)) if race.get('handicap_weight') else None
            except:
                handicap_weight = None
            
            # Get KGS
            kgs = race.get('kgs')
            
            # Get class level
            class_level = get_class_level_numeric(race.get('race_category', ''))
            
            # Create ML format JSON
            ml_data = {
                "race_id": race.get('race_id'),
                "race_date": race_date_formatted,
                "city": race.get('city'),
                "track_type": race.get('track_type'),
                "distance": race.get('distance'),
                "class_level_numeric": class_level,
                "finish_position": finish_pos,
                "time_sec": time_sec,
                "horse_weight": horse_weight,
                "handicap_weight": handicap_weight,
                "kgs": kgs,
                "jockey_id": race.get('jockey_id'),
                "trainer_id": race.get('trainer_id'),
                "ganyan": ganyan,
                "agf": agf
            }
            
            # Create filename: horse_id_race_id.json
            race_id = race.get('race_id')
            filename = f"{horse_id}_{race_id}.json"
            output_path = output_dir / filename
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(ml_data, f, indent=2, ensure_ascii=False)
            
            created_count += 1
        
        return created_count
    
    except Exception as e:
        print(f"Error processing {horse_file_path}: {e}")
        return 0

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
            try:
                # Process directly to profile instead of raw files
                created = process_horse_to_profile(json_file, output_dir)
                if created:
                    total_profiles_created += 1
            except Exception as e:
                print(f"Error processing horse {horse_id}: {e}")
            
            if idx % 100 == 0:
                print(f"Processed {idx}/{total_horses} horses, created {total_profiles_created} profiles")
    
    print(f"\nCompleted!")
    print(f"Total horses processed: {total_horses}")
    print(f"Total profiles created: {total_profiles_created}")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    main()
