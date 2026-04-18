"""
Feature Builder Engine
Builds ML features from horse profiles and race conditions
"""

import json
from pathlib import Path
from typing import Dict, Optional


class FeatureBuilder:
    """Builds features for ML prediction"""
    
    def __init__(self, horse_profiles_dir: str, race_conditions_dir: str):
        self.horse_profiles_dir = Path(horse_profiles_dir)
        self.race_conditions_dir = Path(race_conditions_dir)
        self._horse_cache = {}
        self._condition_cache = {}
    
    def load_horse_profile(self, horse_id: int) -> Optional[Dict]:
        """Load horse profile from file with caching"""
        if horse_id in self._horse_cache:
            return self._horse_cache[horse_id]
        
        profile_path = self.horse_profiles_dir / f"{horse_id}.json"
        if not profile_path.exists():
            return None
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        self._horse_cache[horse_id] = profile
        return profile
    
    def load_race_condition(self, condition_id: str) -> Optional[Dict]:
        """Load race condition by ID with caching"""
        if condition_id in self._condition_cache:
            return self._condition_cache[condition_id]
        
        # Search for condition file
        for condition_file in self.race_conditions_dir.glob("*.json"):
            with open(condition_file, 'r', encoding='utf-8') as f:
                condition = json.load(f)
            
            if condition.get('condition_id') == condition_id:
                self._condition_cache[condition_id] = condition
                return condition
        
        return None
    
    def find_race_condition(self, category: str, city: str, track_type: str, 
                           distance: int, horse_type: str) -> Optional[Dict]:
        """Find race condition by attributes"""
        # Try to build condition_id and search
        for condition_file in self.race_conditions_dir.glob("*.json"):
            with open(condition_file, 'r', encoding='utf-8') as f:
                condition = json.load(f)
            
            if (condition.get('race_category') == category and
                condition.get('city') == city and
                condition.get('distance') == distance and
                condition.get('horse_type') == horse_type):
                return condition
        
        return None
    
    def calc_distance_score(self, horse_best_distance: int, race_distance: int) -> float:
        """Calculate how well horse's best distance matches race distance"""
        diff = abs(horse_best_distance - race_distance)
        
        if diff == 0:
            return 1.0
        elif diff <= 100:
            return 0.8
        elif diff <= 200:
            return 0.5
        else:
            return 0.2
    
    def calc_layoff_score(self, days_since_last_race: int) -> float:
        """Calculate layoff impact score (fresher is better)"""
        if days_since_last_race is None:
            return 0.3
        
        if days_since_last_race <= 30:
            return 1.0
        elif days_since_last_race <= 90:
            return 0.7
        elif days_since_last_race <= 180:
            return 0.4
        elif days_since_last_race <= 365:
            return 0.2
        else:
            return 0.0
    
    def calc_form_trend(self, horse_profile: Dict) -> str:
        """Calculate recent form trend from last 3-5 races"""
        races = horse_profile.get('races', [])
        
        if len(races) < 3:
            return 'insufficient_data'
        
        # Get last 3-5 races
        recent_races = races[-5:] if len(races) >= 5 else races[-3:]
        career_avg = horse_profile.get('career_summary', {}).get('avg_finish_position')
        
        if not career_avg:
            return 'insufficient_data'
        
        # Calculate recent average
        recent_finishes = [r.get('finish_position') for r in recent_races if r.get('finish_position')]
        if not recent_finishes:
            return 'insufficient_data'
        
        recent_avg = sum(recent_finishes) / len(recent_finishes)
        
        # Compare to career
        diff = career_avg - recent_avg  # Positive = improving (lower finish = better)
        
        if diff >= 1.0:
            return 'improving'
        elif diff <= -1.0:
            return 'declining'
        else:
            return 'stable'
    
    def calc_class_match_score(self, horse_profile: Dict, race_class_level: int) -> float:
        """Calculate how well horse's usual class matches race class"""
        races = horse_profile.get('races', [])
        
        if not races or race_class_level is None:
            return 0.5
        
        # Get class levels from recent races
        recent_classes = [r.get('class_level') for r in races[-10:] if r.get('class_level')]
        
        if not recent_classes:
            return 0.5
        
        avg_class = sum(recent_classes) / len(recent_classes)
        diff = abs(race_class_level - avg_class)
        
        if diff == 0:
            return 1.0
        elif diff <= 1:
            return 0.8
        elif diff <= 2:
            return 0.5
        else:
            return 0.3
    
    def calc_city_score(self, horse_profile: Dict, city: str) -> float:
        """Calculate city experience score"""
        city_stats = horse_profile.get('city_stats', {}).get(city, {})
        races = city_stats.get('races', 0)
        avg_finish = city_stats.get('avg_finish')
        
        if races == 0:
            return 0.3  # No experience
        
        if avg_finish is None:
            return 0.5
        
        # Better finish = higher score
        if avg_finish <= 2.0:
            return 1.0
        elif avg_finish <= 3.5:
            return 0.8
        elif avg_finish <= 5.0:
            return 0.6
        else:
            return 0.4
    
    def calc_track_score(self, horse_profile: Dict, track_type: str) -> float:
        """Calculate track type experience score"""
        track_stats = horse_profile.get('track_stats', {}).get(track_type, {})
        races = track_stats.get('races', 0)
        
        if races == 0:
            return 0.3
        elif races <= 3:
            return 0.5
        elif races <= 10:
            return 0.7
        else:
            return 1.0
    
    def get_horse_best_distance(self, horse_profile: Dict) -> Optional[int]:
        """Get horse's best distance from distance_stats"""
        distance_stats = horse_profile.get('distance_stats', {})
        
        if not distance_stats:
            return None
        
        # Find distance with best average finish position
        best_distance = None
        best_avg_finish = float('inf')
        
        for distance_str, stats in distance_stats.items():
            avg_finish = stats.get('avg_finish')
            if avg_finish and avg_finish < best_avg_finish:
                best_avg_finish = avg_finish
                best_distance = int(distance_str)
        
        return best_distance
    
    def get_horse_last_time(self, horse_profile: Dict) -> Optional[float]:
        """Get horse's last race time"""
        races = horse_profile.get('races', [])
        if not races:
            return None
        
        # Races are sorted by date, last one is most recent
        last_race = races[-1]
        return last_race.get('time_sec')
    
    def get_horse_avg_time(self, horse_profile: Dict) -> Optional[float]:
        """Get horse's average race time"""
        career = horse_profile.get('career_summary', {})
        return career.get('avg_time_sec')
    
    def build_features(self, race_condition: Dict, horse_profile: Dict) -> Dict:
        """
        Build ML features from race condition and horse profile
        
        Args:
            race_condition: Race condition profile with stats
            horse_profile: Horse profile with career data
        
        Returns:
            Dictionary of features for ML model
        """
        stats = race_condition.get('stats', {})
        career = horse_profile.get('career_summary', {})
        
        # Get horse metrics
        horse_last_time = self.get_horse_last_time(horse_profile)
        horse_avg_time = self.get_horse_avg_time(horse_profile)
        horse_best_distance = self.get_horse_best_distance(horse_profile)
        days_since_last = career.get('last_race_days_ago')
        
        # Get last race data for current metrics
        races = horse_profile.get('races', [])
        last_race = races[-1] if races else {}
        horse_weight = last_race.get('horse_weight')
        
        # Build features
        features = {
            # Core scores (normalized 0-1)
            "layoff_score": self.calc_layoff_score(days_since_last),
            "distance_match_score": self.calc_distance_score(
                horse_best_distance, race_condition.get('distance')
            ) if horse_best_distance else 0.5,
            "city_score": self.calc_city_score(horse_profile, race_condition.get('city')),
            "track_score": self.calc_track_score(horse_profile, race_condition.get('track_type')),
            "class_match_score": self.calc_class_match_score(
                horse_profile, race_condition.get('class_level')
            ),
            
            # Form analysis
            "form_trend": self.calc_form_trend(horse_profile),
            
            # Time comparison (only last race vs race avg)
            "last_time_vs_avg": round(
                horse_last_time - stats.get('avg_time_sec', 0), 2
            ) if horse_last_time and stats.get('avg_time_sec') else None,
            
            # Weight features
            "weight_diff": round(
                horse_weight - stats.get('avg_winner_weight', 0), 2
            ) if horse_weight and stats.get('avg_winner_weight') else None,
            
            # Career metrics
            "total_races": career.get('total_races', 0),
            "avg_finish_position": career.get('avg_finish_position'),
            "days_since_last_race": days_since_last,
            
            # Race context
            "class_level": race_condition.get('class_level'),
            "race_distance": race_condition.get('distance'),
            
            # Detailed experience (for debugging/analysis)
            "city_experience": self.get_city_experience(
                horse_profile, race_condition.get('city')
            ),
            "track_experience": self.get_track_experience(
                horse_profile, race_condition.get('track_type')
            ),
        }
        
        return features
    
    def get_city_experience(self, horse_profile: Dict, city: str) -> Dict:
        """Get horse's experience in specific city"""
        city_stats = horse_profile.get('city_stats', {}).get(city, {})
        
        return {
            "races_in_city": city_stats.get('races', 0),
            "avg_finish_in_city": city_stats.get('avg_finish')
        }
    
    def get_track_experience(self, horse_profile: Dict, track_type: str) -> Dict:
        """Get horse's experience on specific track type"""
        track_stats = horse_profile.get('track_stats', {}).get(track_type, {})
        
        return {
            "races_on_track": track_stats.get('races', 0),
            "avg_time_on_track": track_stats.get('avg_time')
        }


def example_usage():
    """Example of how to use FeatureBuilder"""
    
    # Initialize builder
    builder = FeatureBuilder(
        horse_profiles_dir=r"E:\data\horse_profiles",
        race_conditions_dir=r"E:\data\race_condition"
    )
    
    # Load a horse profile
    horse_id = 100001
    horse = builder.load_horse_profile(horse_id)
    
    if not horse:
        print(f"Horse {horse_id} not found")
        return
    
    # Load a race condition
    condition_id = "H14_ADANA_CIM_1300_ARAP"
    condition = builder.load_race_condition(condition_id)
    
    if not condition:
        print(f"Condition {condition_id} not found")
        return
    
    # Build features
    features = builder.build_features(condition, horse)
    
    print(f"\n🐎 Horse {horse_id} in {condition_id}")
    print(f"\n📊 Features:")
    for key, value in features.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    example_usage()
