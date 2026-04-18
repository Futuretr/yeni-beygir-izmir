"""
Test different horse-race combinations
"""

from feature_builder import FeatureBuilder

def test_combinations():
    builder = FeatureBuilder(
        horse_profiles_dir=r"E:\data\horse_profiles",
        race_conditions_dir=r"E:\data\race_condition"
    )
    
    # Test with horse 45354 (Izmir Kum 1400m experience)
    print("=" * 60)
    print("TEST 1: Horse 45354")
    print("=" * 60)
    
    horse = builder.load_horse_profile(45354)
    if horse:
        print(f"\n🐎 Horse Career Summary:")
        print(f"  Total races: {horse['career_summary']['total_races']}")
        print(f"  Avg finish: {horse['career_summary']['avg_finish_position']}")
        print(f"  Days since last race: {horse['career_summary']['last_race_days_ago']}")
        
        print(f"\n📍 City Stats:")
        for city, stats in list(horse['city_stats'].items())[:3]:
            print(f"  {city}: {stats['races']} races, avg finish {stats['avg_finish']}")
        
        # Try Izmir condition
        condition_id = "H14_IZMIR_KUM_1400_INGILIZ"
        condition = builder.load_race_condition(condition_id)
        
        if condition:
            features = builder.build_features(condition, horse)
            print(f"\n✅ Features for {condition_id}:")
            for key, value in features.items():
                if value is not None and not isinstance(value, dict):
                    print(f"  {key}: {value}")
                elif isinstance(value, dict):
                    print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("TEST 2: Horse 100001")
    print("=" * 60)
    
    horse = builder.load_horse_profile(100001)
    if horse:
        # Try Izmir Kum condition (where horse has experience)
        condition_id = "S1_IZMIR_KUM_1600_INGILIZ"
        condition = builder.load_race_condition(condition_id)
        
        if condition:
            features = builder.build_features(condition, horse)
            print(f"\n✅ Features for {condition_id}:")
            for key, value in features.items():
                if value is not None and not isinstance(value, dict):
                    print(f"  {key}: {value}")
                elif isinstance(value, dict):
                    print(f"  {key}: {value}")
        else:
            print(f"❌ Condition {condition_id} not found")

if __name__ == "__main__":
    test_combinations()
