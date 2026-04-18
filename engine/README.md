# Feature Builder & Scoring Engine

ML feature extraction and scoring system for horse race prediction.

## 📁 Structure

```
/engine
  ├─ feature_builder.py    # Feature extraction from profiles
  ├─ scoring_engine.py     # Convert features to final score
  ├─ test_features.py      # Feature tests
  ├─ test_scoring.py       # Scoring comparison tests
  └─ README.md            # This file
```

## 🚀 Quick Start

### 1️⃣ Feature Building

```python
from engine.feature_builder import FeatureBuilder

builder = FeatureBuilder(
    horse_profiles_dir=r"E:\data\horse_profiles",
    race_conditions_dir=r"E:\data\race_condition"
)

horse = builder.load_horse_profile(45354)
condition = builder.load_race_condition("H14_IZMIR_KUM_1400_INGILIZ")
features = builder.build_features(condition, horse)
```

### 2️⃣ Scoring

```python
from engine.scoring_engine import ScoringEngine

scorer = ScoringEngine()
result = scorer.score(features)
insights = scorer.get_insights(features, result)

print(f"Score: {result['final_score']}/100")
print(f"Risk: {result['risk_level']}")
```

## 📊 Features (v2.0)

### ✅ Core Scores (0-1 normalized)
- **layoff_score** - Recency impact (1041 days → 0.0)
- **distance_match_score** - Distance suitability (0.2-1.0)
- **city_score** - City performance history
- **track_score** - Track type experience
- **class_match_score** - Class level appropriateness

### ✅ Form Analysis
- **form_trend** - improving / stable / declining (last 3-5 races)

### ✅ Context
- **total_races** - Career experience
- **avg_finish_position** - Career average
- **days_since_last_race** - Raw days (for reference)
- **class_level** - Race class (1-9)

### ❌ Removed (v1 → v2)
- ~~avg_time_vs_race_avg~~ - Unreliable across different conditions

## 🎯 Scoring Weights

```python
{
    'form_trend': 20%,           # Most important
    'layoff_score': 15%,         # Recency critical
    'distance_match_score': 15%, # Distance fit
    'city_score': 12%,           # Local performance
    'class_match_score': 12%,    # Class appropriateness
    'track_score': 10%,          # Track experience
    'experience': 8%,            # Total races
    'avg_finish': 8%,            # Career quality
}
```

## 📈 Example Output

```
🐎 Horse 105542 → H14_IZMIR_KUM_1400_INGILIZ

📊 FINAL SCORE: 69/100
⚠️  RISK LEVEL: MEDIUM
🎯 CONFIDENCE: 1.0

📈 Score Breakdown:
  form_trend          : 0.30 × 20% =   6.0
  layoff_score        : 1.00 × 15% =  15.0
  distance_match_score: 0.80 × 15% =  12.0
  city_score          : 0.60 × 12% =   7.2
  ...

💡 Insights:
  ✅ Fresh - raced 5 days ago
  ⚠️ Form declining recently
  ✅ Experienced on this track (16 races)
  ✅ Good distance match
```

## 🔧 Adding New Features

```python
# In feature_builder.py
def calc_new_feature(self, horse_profile: Dict) -> float:
    # Your logic
    return score

# In build_features()
features['new_feature'] = self.calc_new_feature(horse_profile)
```

## 💡 Next Steps

1. ✅ Normalize critical features (DONE)
2. ✅ Add form trend analysis (DONE)
3. ✅ Add scoring engine (DONE)
4. 🔄 Add jockey/trainer features
5. 🔄 Historical head-to-head analysis
6. 🔄 ML model integration
