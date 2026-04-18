"""
Test scoring with multiple horses
"""

from feature_builder import FeatureBuilder
from scoring_engine import ScoringEngine


def compare_horses():
    builder = FeatureBuilder(
        horse_profiles_dir=r"E:\data\horse_profiles",
        race_conditions_dir=r"E:\data\race_condition"
    )
    scorer = ScoringEngine()
    
    # Try to find some horses with recent races
    condition = builder.load_race_condition("H14_IZMIR_KUM_1400_INGILIZ")
    
    if not condition:
        print("Condition not found")
        return
    
    print(f"{'='*70}")
    print(f"Race Condition: {condition['condition_id']}")
    print(f"{'='*70}\n")
    
    # Test with a few horses
    test_horses = [45354, 100001, 105542, 100002, 100003]
    results = []
    
    for horse_id in test_horses:
        horse = builder.load_horse_profile(horse_id)
        if not horse:
            continue
        
        features = builder.build_features(condition, horse)
        score_result = scorer.score(features)
        insights = scorer.get_insights(features, score_result)
        
        results.append({
            'horse_id': horse_id,
            'score': score_result['final_score'],
            'risk': score_result['risk_level'],
            'confidence': score_result['confidence'],
            'surprise': score_result.get('surprise_potential', 'N/A'),
            'days_ago': features.get('days_since_last_race'),
            'total_races': features.get('total_races'),
            'insights': insights
        })
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print("🏆 RANKING:")
    print(f"{'Rank':<6} {'Horse':<10} {'Score':<8} {'Risk':<12} {'Surprise':<10} {'Days':<10} {'Races':<8}")
    print("-" * 80)
    
    for i, r in enumerate(results, 1):
        print(f"{i:<6} {r['horse_id']:<10} {r['score']:<8} {r['risk']:<12} {r.get('surprise', 'N/A'):<10} {r['days_ago']:<10} {r['total_races']:<8}")
    
    print(f"\n{'='*70}")
    print("📋 DETAILED ANALYSIS")
    print(f"{'='*70}\n")
    
    for i, r in enumerate(results, 1):
        print(f"\n#{i} - Horse {r['horse_id']} (Score: {r['score']}/100)")
        print(f"Risk: {r['risk']} | Confidence: {r['confidence']}")
        for insight in r['insights']:
            print(f"  {insight}")


if __name__ == "__main__":
    compare_horses()
