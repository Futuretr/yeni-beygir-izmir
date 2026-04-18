"""
Scoring Engine - Converts features to final score
"""

from typing import Dict


class ScoringEngine:
    """Converts features into a final prediction score"""
    
    def __init__(self):
        # Feature weights (total should be 100)
        self.weights = {
            'layoff_score': 15,          # Recency is critical
            'form_trend': 20,            # Recent form most important
            'city_score': 12,            # Local performance
            'track_score': 10,           # Track experience
            'class_match_score': 12,     # Class appropriateness
            'distance_match_score': 15,  # Distance suitability
            'experience': 8,             # Total races experience
            'avg_finish': 8,             # Career performance
        }
    
    def score_form_trend(self, trend: str) -> float:
        """Convert form trend to score"""
        if trend == 'improving':
            return 1.0
        elif trend == 'stable':
            return 0.7
        elif trend == 'declining':
            return 0.3
        else:  # insufficient_data
            return 0.5
    
    def score_experience(self, total_races: int) -> float:
        """Score based on total experience"""
        if total_races >= 20:
            return 1.0
        elif total_races >= 10:
            return 0.8
        elif total_races >= 5:
            return 0.6
        else:
            return 0.4
    
    def score_avg_finish(self, avg_finish: float) -> float:
        """Score based on career average finish"""
        if avg_finish is None:
            return 0.5
        
        if avg_finish <= 2.5:
            return 1.0
        elif avg_finish <= 4.0:
            return 0.8
        elif avg_finish <= 6.0:
            return 0.6
        else:
            return 0.4
    
    def calculate_risk_level(self, score: float) -> str:
        """Determine risk level based on score"""
        if score >= 75:
            return 'LOW'
        elif score >= 60:
            return 'MEDIUM'
        elif score >= 45:
            return 'HIGH'
        else:
            return 'VERY_HIGH'
    
    def calc_reliability(self, total_races: int) -> float:
        """Calculate reliability score based on total races"""
        return min(1.0, total_races / 20)
    
    def calc_adjusted_layoff_score(self, base_layoff_score: float, features: Dict) -> float:
        """Adjust layoff score based on proven performance and experience"""
        
        # Get city and track experience
        city_exp = features.get('city_experience', {})
        city_avg_finish = city_exp.get('avg_finish_in_city')
        
        track_exp = features.get('track_experience', {})
        track_races = track_exp.get('races_on_track', 0)
        
        # Start with base score
        adjusted_score = base_layoff_score
        
        # Bonus for proven city performance
        if city_avg_finish and city_avg_finish < 3.0 and track_races > 15:
            # Proven performer - reduce layoff penalty by 20%
            if base_layoff_score < 0.5:  # Only if there's a penalty
                penalty_reduction = (0.5 - base_layoff_score) * 0.20
                adjusted_score = base_layoff_score + penalty_reduction
        
        # Additional bonus for excellent track record
        if city_avg_finish and city_avg_finish < 2.5 and track_races > 20:
            # Elite performer - further reduce penalty by 10%
            if base_layoff_score < 0.5:
                penalty_reduction = (0.5 - base_layoff_score) * 0.10
                adjusted_score = adjusted_score + penalty_reduction
        
        return min(1.0, adjusted_score)
    
    def calc_surprise_potential(self, features: Dict) -> str:
        """Calculate surprise potential for longshot hunters"""
        
        city_exp = features.get('city_experience', {})
        city_avg_finish = city_exp.get('avg_finish_in_city')
        city_races = city_exp.get('races_in_city', 0)
        
        layoff_score = features.get('layoff_score', 0.5)
        avg_finish = features.get('avg_finish_position')
        
        # High surprise factors
        high_factors = 0
        
        # Strong city performance but coming back from layoff
        if city_avg_finish and city_avg_finish <= 3.0 and city_races >= 2:
            high_factors += 1
        
        # Good historical performance but recent layoff
        if avg_finish and avg_finish <= 4.0 and layoff_score < 0.3:
            high_factors += 1
        
        # Proven performer with extended break
        if city_avg_finish and city_avg_finish <= 2.5:
            high_factors += 1
        
        # Form was improving before layoff
        if features.get('form_trend') == 'improving':
            high_factors += 1
        
        if high_factors >= 3:
            return 'HIGH'
        elif high_factors >= 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def calculate_confidence(self, features: Dict, reliability: float, 
                           adjusted_layoff_score: float) -> float:
        """Calculate confidence based on data quality and recency"""
        
        # Base confidence on reliability and recency
        layoff_penalty = max(0, 0.5 - adjusted_layoff_score)  # Penalty when score < 0.5
        confidence = reliability * (1.0 - layoff_penalty)
        
        # Boost confidence if we have good experience data
        city_exp = features.get('city_experience', {})
        track_exp = features.get('track_experience', {})
        
        if city_exp.get('races_in_city', 0) >= 3:
            confidence = min(1.0, confidence + 0.1)
        
        if track_exp.get('races_on_track', 0) >= 10:
            confidence = min(1.0, confidence + 0.1)
        
        return round(confidence, 2)
    
    def score(self, features: Dict) -> Dict:
        """
        Calculate final score from features
        
        Returns dict with:
        - final_score (0-100)
        - risk_level (LOW/MEDIUM/HIGH/VERY_HIGH)
        - confidence (0-1)
        - reliability (0-1)
        - surprise_potential (HIGH/MEDIUM/LOW)
        - breakdown (component scores)
        """
        
        # Calculate reliability
        total_races = features.get('total_races', 0)
        reliability = self.calc_reliability(total_races)
        
        # Adjust layoff score based on proven performance
        base_layoff = features.get('layoff_score', 0.5)
        adjusted_layoff = self.calc_adjusted_layoff_score(base_layoff, features)
        
        # Calculate surprise potential
        surprise_potential = self.calc_surprise_potential(features)
        
        # Component scores (0-1 scale) - use adjusted layoff
        components = {
            'layoff_score': adjusted_layoff,  # Use adjusted instead of base
            'form_trend': self.score_form_trend(features.get('form_trend', 'insufficient_data')),
            'city_score': features.get('city_score', 0.5),
            'track_score': features.get('track_score', 0.5),
            'class_match_score': features.get('class_match_score', 0.5),
            'distance_match_score': features.get('distance_match_score', 0.5),
            'experience': self.score_experience(total_races),
            'avg_finish': self.score_avg_finish(features.get('avg_finish_position')),
        }
        
        # Apply reliability factor to prevent inexperienced horses from scoring too high
        weighted_score = 0
        for component, score in components.items():
            component_score = score * self.weights[component]
            # Apply reliability damping to all components except experience
            if component != 'experience':
                component_score *= (0.7 + 0.3 * reliability)  # Min 70% of score
            weighted_score += component_score
        
        # Round to integer
        final_score = round(weighted_score)
        
        # Calculate risk, confidence
        risk_level = self.calculate_risk_level(final_score)
        confidence = self.calculate_confidence(features, reliability, adjusted_layoff)
        
        return {
            'final_score': final_score,
            'risk_level': risk_level,
            'confidence': confidence,
            'reliability': round(reliability, 2),
            'surprise_potential': surprise_potential,
            'layoff_adjustment': {
                'base_score': round(base_layoff, 2),
                'adjusted_score': round(adjusted_layoff, 2),
                'bonus_applied': round(adjusted_layoff - base_layoff, 2)
            },
            'breakdown': {
                k: {
                    'score': round(v, 2),
                    'weight': self.weights[k],
                    'contribution': round(v * self.weights[k], 1)
                }
                for k, v in components.items()
            }
        }
    
    def get_insights(self, features: Dict, score_result: Dict) -> list:
        """Generate human-readable insights"""
        insights = []
        breakdown = score_result['breakdown']
        layoff_adj = score_result.get('layoff_adjustment', {})
        
        # Layoff analysis with adjustment info
        days = features.get('days_since_last_race')
        if days and days > 365:
            if layoff_adj.get('bonus_applied', 0) > 0:
                insights.append(f"⚠️ Long layoff ({days} days) BUT proven performer (+{layoff_adj['bonus_applied']:.2f} bonus)")
            else:
                insights.append(f"⚠️ Very long layoff ({days} days) - high risk")
        elif days and days > 180:
            if layoff_adj.get('bonus_applied', 0) > 0:
                insights.append(f"⚠️ Extended layoff ({days} days) BUT strong record (bonus applied)")
            else:
                insights.append(f"⚠️ Extended layoff ({days} days)")
        elif days and days <= 30:
            insights.append(f"✅ Fresh - raced {days} days ago")
        
        # Form analysis
        form = features.get('form_trend')
        if form == 'improving':
            insights.append("✅ Form improving in recent races")
        elif form == 'declining':
            insights.append("⚠️ Form declining recently")
        
        # City experience
        city_exp = features.get('city_experience', {})
        city_races = city_exp.get('races_in_city', 0)
        city_avg = city_exp.get('avg_finish_in_city')
        if city_races > 0 and city_avg and city_avg <= 3.0:
            insights.append(f"✅ Excellent city record ({city_avg:.1f} avg in {city_races} races)")
        elif city_races == 0:
            insights.append("⚠️ No experience in this city")
        
        # Track experience
        track_exp = features.get('track_experience', {})
        track_races = track_exp.get('races_on_track', 0)
        if track_races >= 10:
            insights.append(f"✅ Experienced on this track ({track_races} races)")
        elif track_races == 0:
            insights.append("⚠️ No experience on this track type")
        
        # Distance match
        dist_score = features.get('distance_match_score', 0)
        if dist_score >= 0.8:
            insights.append("✅ Good distance match")
        elif dist_score < 0.5:
            insights.append("⚠️ Distance may not suit")
        
        # Class match
        class_score = features.get('class_match_score', 0)
        if class_score < 0.5:
            insights.append("⚠️ Different class level than usual")
        
        # Reliability
        reliability = score_result.get('reliability', 0)
        if reliability < 0.5:
            insights.append(f"⚠️ Limited experience ({features.get('total_races', 0)} races)")
        
        # Surprise potential
        surprise = score_result.get('surprise_potential', 'LOW')
        if surprise == 'HIGH':
            insights.append("🎯 HIGH SURPRISE POTENTIAL - proven but overlooked")
        elif surprise == 'MEDIUM':
            insights.append("🎲 MEDIUM SURPRISE POTENTIAL")
        
        return insights


def example_scoring():
    """Example of scoring engine usage"""
    from feature_builder import FeatureBuilder
    
    # Initialize
    builder = FeatureBuilder(
        horse_profiles_dir=r"E:\data\horse_profiles",
        race_conditions_dir=r"E:\data\race_condition"
    )
    scorer = ScoringEngine()
    
    # Load data
    horse = builder.load_horse_profile(45354)
    condition = builder.load_race_condition("H14_IZMIR_KUM_1400_INGILIZ")
    
    if horse and condition:
        # Build features
        features = builder.build_features(condition, horse)
        
        # Calculate score
        result = scorer.score(features)
        insights = scorer.get_insights(features, result)
        
        print(f"\n{'='*60}")
        print(f"🐎 Horse {horse['horse_id']} → {condition['condition_id']}")
        print(f"{'='*60}")
        
        print(f"\n📊 FINAL SCORE: {result['final_score']}/100")
        print(f"⚠️  RISK LEVEL: {result['risk_level']}")
        print(f"🎯 CONFIDENCE: {result['confidence']}")
        print(f"🔧 RELIABILITY: {result['reliability']}")
        print(f"🎲 SURPRISE POTENTIAL: {result['surprise_potential']}")
        
        # Show layoff adjustment if any
        if result.get('layoff_adjustment'):
            adj = result['layoff_adjustment']
            if adj['bonus_applied'] > 0:
                print(f"\n💪 Layoff Adjustment:")
                print(f"  Base Score: {adj['base_score']}")
                print(f"  Adjusted: {adj['adjusted_score']} (+{adj['bonus_applied']:.2f} bonus)")
        
        print(f"\n📈 Score Breakdown:")
        for component, data in sorted(result['breakdown'].items(), 
                                     key=lambda x: x[1]['contribution'], 
                                     reverse=True):
            print(f"  {component:20s}: {data['score']:.2f} × {data['weight']:2d}% = {data['contribution']:5.1f}")
        
        print(f"\n💡 Insights:")
        for insight in insights:
            print(f"  {insight}")


if __name__ == "__main__":
    example_scoring()
