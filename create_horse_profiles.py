import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def parse_filename(filename):
    """Extract horse_id and race_id from filename like '45354_183387.json'"""
    name = filename.replace('.json', '')
    parts = name.split('_')
    if len(parts) == 2:
        return int(parts[0]), int(parts[1])
    return None, None

def clean_race_data(raw_race, horse_id):
    """Convert raw race data to clean format"""
    return {
        "race_id": raw_race.get("race_id"),
        "date": raw_race.get("race_date"),
        "city": raw_race.get("city"),
        "track_type": raw_race.get("track_type"),
        "distance": raw_race.get("distance"),
        "class_level": raw_race.get("class_level_numeric"),
        "finish_position": raw_race.get("finish_position"),
        "time_sec": raw_race.get("time_sec"),
        "horse_weight": raw_race.get("horse_weight"),
        "jockey_id": raw_race.get("jockey_id"),
        "trainer_id": raw_race.get("trainer_id")
    }

def calculate_days_ago(race_date, reference_date):
    """Calculate days between two dates"""
    try:
        race_dt = datetime.strptime(race_date, "%Y-%m-%d")
        ref_dt = datetime.strptime(reference_date, "%Y-%m-%d")
        return (ref_dt - race_dt).days
    except:
        return None

def create_horse_profile(horse_id, races):
    """Create complete horse profile with statistics"""
    
    # Sort races by date (oldest to newest)
    sorted_races = sorted(races, key=lambda x: x.get("date", ""))
    
    # Career summary calculations
    total_races = len(sorted_races)
    
    finish_positions = [r["finish_position"] for r in sorted_races if r.get("finish_position")]
    avg_finish_position = sum(finish_positions) / len(finish_positions) if finish_positions else None
    
    times = [r["time_sec"] for r in sorted_races if r.get("time_sec")]
    avg_time_sec = sum(times) / len(times) if times else None
    
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
    
    # Convert to final format
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
    
    # Convert to final format
    track_stats_final = {}
    for track, stats in track_stats.items():
        track_stats_final[track] = {
            "races": stats["races"],
            "avg_time": round(sum(stats["times"]) / len(stats["times"]), 2) if stats["times"] else None
        }
    
    # Distance stats
    distance_stats = defaultdict(lambda: {"races": 0, "finish_positions": [], "times": []})
    for race in sorted_races:
        distance = race.get("distance")
        if distance:
            distance_stats[distance]["races"] += 1
            if race.get("finish_position"):
                distance_stats[distance]["finish_positions"].append(race["finish_position"])
            if race.get("time_sec"):
                distance_stats[distance]["times"].append(race["time_sec"])
    
    distance_stats_final = {}
    for distance, stats in distance_stats.items():
        distance_stats_final[str(distance)] = {
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
            "last_race_days_ago": last_race_days_ago
        },
        "city_stats": city_stats_final,
        "track_stats": track_stats_final,
        "distance_stats": distance_stats_final,
        "races": sorted_races
    }
    
    return profile

def main():
    ml_json_dir = Path(r"E:\data\ml_json")
    output_dir = Path(r"E:\data\horse_profiles")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Reading raw JSON files...")
    
    # Group races by horse_id
    horse_races = defaultdict(list)
    
    json_files = list(ml_json_dir.glob("*.json"))
    total_files = len(json_files)
    
    print(f"Found {total_files} race files")
    
    processed = 0
    for json_file in json_files:
        horse_id, race_id = parse_filename(json_file.name)
        
        if horse_id is None:
            continue
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                raw_race = json.load(f)
            
            # Clean the race data
            clean_race = clean_race_data(raw_race, horse_id)
            horse_races[horse_id].append(clean_race)
            
            processed += 1
            if processed % 10000 == 0:
                print(f"Processed {processed}/{total_files} files, grouped into {len(horse_races)} horses")
        
        except Exception as e:
            print(f"Error processing {json_file.name}: {e}")
            continue
    
    print(f"\nTotal races processed: {processed}")
    print(f"Total unique horses: {len(horse_races)}")
    print("\nCreating horse profiles...")
    
    # Create profiles
    profiles_created = 0
    for horse_id, races in horse_races.items():
        try:
            profile = create_horse_profile(horse_id, races)
            
            # Save profile
            output_file = output_dir / f"{horse_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
            profiles_created += 1
            if profiles_created % 1000 == 0:
                print(f"Created {profiles_created}/{len(horse_races)} profiles")
        
        except Exception as e:
            print(f"Error creating profile for horse {horse_id}: {e}")
            continue
    
    print(f"\n✅ COMPLETED!")
    print(f"Total horse profiles created: {profiles_created}")
    print(f"Output directory: {output_dir}")
    
    # Show sample
    if profiles_created > 0:
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
