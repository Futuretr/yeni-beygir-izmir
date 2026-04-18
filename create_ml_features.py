"""
Gelişmiş Feature Engineering - ML için hazırlık
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


class RaceFeatureExtractor:
    """Yarış verilerinden ML için feature çıkarma"""
    
    def __init__(self):
        self.feature_names = []
    
    def extract_all_features(self, horse, race_info):
        """Tüm feature'ları çıkar"""
        
        features = {}
        
        # Temel bilgiler
        features.update(self._extract_basic_features(horse, race_info))
        
        # Performans feature'ları
        features.update(self._extract_performance_features(horse))
        
        # Pist ve mesafe uyumu
        features.update(self._extract_track_distance_features(horse, race_info))
        
        # Form analizi
        features.update(self._extract_form_features(horse))
        
        # Bahis verileri
        features.update(self._extract_betting_features(horse))
        
        # İlişkisel feature'lar (jokey, antrenör, sahip)
        features.update(self._extract_relationship_features(horse))
        
        # Genetik bilgiler
        features.update(self._extract_genetic_features(horse))
        
        # Zaman bazlı feature'lar
        features.update(self._extract_time_features(horse))
        
        return features
    
    def _extract_basic_features(self, horse, race_info):
        """Temel feature'lar"""
        
        age_str = horse.get('horse_age', '')
        age = self._parse_age(age_str)
        
        weight = horse.get('horse_weight')
        try:
            weight = int(weight) if weight else 0
        except:
            weight = 0
        
        handicap = horse.get('handicap_weight')
        try:
            handicap = int(handicap) if handicap else 0
        except:
            handicap = 0
        
        return {
            'horse_age': age,
            'horse_weight': weight,
            'handicap_weight': handicap,
            'total_weight': weight + handicap,
            'start_position': self._parse_start_no(horse.get('start_no', '')),
            'race_distance': race_info.get('distance', 0),
        }
    
    def _extract_performance_features(self, horse):
        """Performans feature'ları"""
        
        profile = horse.get('profile', {})
        career = profile.get('career_summary', {})
        past_races = horse.get('past_races', [])
        
        features = {
            'career_total_races': career.get('total_races', 0),
            'career_avg_finish': career.get('avg_finish_position', 999),
            'career_avg_time': career.get('avg_time_sec', 0),
            'last_race_days_ago': career.get('last_race_days_ago', 999),
        }
        
        # Son N yarış performansları
        for n in [1, 3, 5, 10]:
            last_n = past_races[-n:] if len(past_races) >= n else past_races
            
            if last_n:
                finishes = [r.get('finish_position', 999) for r in last_n]
                times = [r.get('time_sec', 0) for r in last_n if r.get('time_sec')]
                
                features[f'last_{n}_avg_finish'] = np.mean(finishes)
                features[f'last_{n}_best_finish'] = min(finishes)
                features[f'last_{n}_worst_finish'] = max(finishes)
                features[f'last_{n}_std_finish'] = np.std(finishes) if len(finishes) > 1 else 0
                
                if times:
                    features[f'last_{n}_avg_time'] = np.mean(times)
                    features[f'last_{n}_std_time'] = np.std(times) if len(times) > 1 else 0
                else:
                    features[f'last_{n}_avg_time'] = 0
                    features[f'last_{n}_std_time'] = 0
                
                # Kazanma oranı
                wins = sum(1 for f in finishes if f == 1)
                features[f'last_{n}_win_rate'] = wins / len(finishes)
                
                # Top 3 oranı
                top3 = sum(1 for f in finishes if f <= 3)
                features[f'last_{n}_top3_rate'] = top3 / len(finishes)
            else:
                features[f'last_{n}_avg_finish'] = 999
                features[f'last_{n}_best_finish'] = 999
                features[f'last_{n}_worst_finish'] = 999
                features[f'last_{n}_std_finish'] = 0
                features[f'last_{n}_avg_time'] = 0
                features[f'last_{n}_std_time'] = 0
                features[f'last_{n}_win_rate'] = 0
                features[f'last_{n}_top3_rate'] = 0
        
        # Trend analizi (son performans vs önceki)
        if len(past_races) >= 6:
            last_3_finishes = [r.get('finish_position', 999) for r in past_races[-3:]]
            prev_3_finishes = [r.get('finish_position', 999) for r in past_races[-6:-3]]
            
            features['performance_trend'] = np.mean(prev_3_finishes) - np.mean(last_3_finishes)
        else:
            features['performance_trend'] = 0
        
        return features
    
    def _extract_track_distance_features(self, horse, race_info):
        """Pist ve mesafe uyumu feature'ları"""
        
        profile = horse.get('profile', {})
        track_stats = profile.get('track_stats', {})
        distance_stats = profile.get('distance_stats', {})
        city_stats = profile.get('city_stats', {})
        
        race_track = race_info.get('track_type', '')
        race_distance = str(race_info.get('distance', 0))
        race_city = race_info.get('city', '')
        
        features = {}
        
        # Pist tipi deneyimi
        track_data = track_stats.get(race_track, {})
        if isinstance(track_data, dict):
            features['track_type_races'] = track_data.get('races', 0)
            features['track_type_avg_time'] = track_data.get('avg_time', 0)
        else:
            features['track_type_races'] = 0
            features['track_type_avg_time'] = 0
        
        # Mesafe deneyimi
        distance_data = distance_stats.get(race_distance, {})
        if isinstance(distance_data, dict):
            features['distance_races'] = distance_data.get('races', 0)
            features['distance_avg_finish'] = distance_data.get('avg_finish', 999)
            features['distance_avg_time'] = distance_data.get('avg_time', 0)
        else:
            features['distance_races'] = 0
            features['distance_avg_finish'] = 999
            features['distance_avg_time'] = 0
        
        # Şehir deneyimi
        city_data = city_stats.get(race_city, {})
        if isinstance(city_data, dict):
            features['city_races'] = city_data.get('races', 0)
            features['city_avg_finish'] = city_data.get('avg_finish', 999)
        else:
            features['city_races'] = 0
            features['city_avg_finish'] = 999
        
        # Toplam pist deneyimi
        total_track_races = sum(
            s.get('races', 0) if isinstance(s, dict) else 0 
            for s in track_stats.values()
        )
        features['total_track_experience'] = total_track_races
        
        # Mesafe çeşitliliği
        features['distance_variety'] = len(distance_stats)
        
        return features
    
    def _extract_form_features(self, horse):
        """Form analizi feature'ları"""
        
        last_6_form = horse.get('last_6_races', '')
        
        features = {
            'form_length': len(last_6_form),
        }
        
        # Form string analizi
        if last_6_form:
            try:
                # Sayısal pozisyonları parse et
                positions = [int(c) for c in last_6_form if c.isdigit()]
                
                if positions:
                    features['form_avg'] = np.mean(positions)
                    features['form_best'] = min(positions)
                    features['form_worst'] = max(positions)
                    features['form_consistency'] = np.std(positions) if len(positions) > 1 else 0
                    
                    # Son 3 yarıştaki trend
                    if len(positions) >= 3:
                        recent = positions[-3:]
                        features['recent_form_trend'] = recent[0] - recent[-1]  # pozitif = iyileşme
                    else:
                        features['recent_form_trend'] = 0
                else:
                    features['form_avg'] = 999
                    features['form_best'] = 999
                    features['form_worst'] = 999
                    features['form_consistency'] = 0
                    features['recent_form_trend'] = 0
            except:
                features['form_avg'] = 999
                features['form_best'] = 999
                features['form_worst'] = 999
                features['form_consistency'] = 0
                features['recent_form_trend'] = 0
        else:
            features['form_avg'] = 999
            features['form_best'] = 999
            features['form_worst'] = 999
            features['form_consistency'] = 0
            features['recent_form_trend'] = 0
        
        return features
    
    def _extract_betting_features(self, horse):
        """Bahis verileri feature'ları"""
        
        # Ganyan
        ganyan_str = str(horse.get('ganyan', '')).replace(',', '.')
        try:
            ganyan = float(ganyan_str) if ganyan_str else None
        except:
            ganyan = None
        
        # AGF
        agf_str = str(horse.get('agf', '')).replace('%', '').strip()
        try:
            agf = float(agf_str) if agf_str else None
        except:
            agf = None
        
        # KGS
        kgs = horse.get('kgs')
        try:
            kgs = int(kgs) if kgs else 0
        except:
            kgs = 0
        
        return {
            'ganyan': ganyan if ganyan else 999,
            'agf': agf if agf else 0,
            'kgs': kgs,
            'ganyan_log': np.log1p(ganyan) if ganyan and ganyan > 0 else 0,
            'is_favorite': 1 if ganyan and ganyan < 5 else 0,
        }
    
    def _extract_relationship_features(self, horse):
        """Jokey, antrenör, sahip feature'ları"""
        
        return {
            'jockey_id': horse.get('jockey_id', 0) or 0,
            'trainer_id': horse.get('trainer_id', 0) or 0,
            'owner_id': horse.get('owner_id', 0) or 0,
        }
    
    def _extract_genetic_features(self, horse):
        """Genetik bilgiler (baba, anne)"""
        
        return {
            'father_id': horse.get('father_id', 0) or 0,
            'mother_id': horse.get('mother_id', 0) or 0,
        }
    
    def _extract_time_features(self, horse):
        """Zaman bazlı feature'lar"""
        
        past_races = horse.get('past_races', [])
        
        features = {
            'races_last_30_days': 0,
            'races_last_60_days': 0,
            'races_last_90_days': 0,
        }
        
        if past_races:
            for race in past_races:
                race_date = race.get('date', '')
                if race_date:
                    try:
                        days_ago = (datetime.now() - datetime.fromisoformat(race_date)).days
                        
                        if days_ago <= 30:
                            features['races_last_30_days'] += 1
                        if days_ago <= 60:
                            features['races_last_60_days'] += 1
                        if days_ago <= 90:
                            features['races_last_90_days'] += 1
                    except:
                        pass
        
        return features
    
    def _parse_age(self, age_str):
        """Yaş bilgisini parse et"""
        if not age_str:
            return 0
        
        # "3y k d" formatından sadece sayıyı al
        try:
            age = int(age_str.split('y')[0])
            return age
        except:
            return 0
    
    def _parse_start_no(self, start_no):
        """Start numarasını parse et"""
        if not start_no:
            return 0
        
        try:
            # "11DSTercihli Start" gibi formatlardan sayıyı al
            import re
            match = re.search(r'\d+', str(start_no))
            return int(match.group()) if match else 0
        except:
            return 0


def create_ml_dataset(race_files, output_file=None):
    """ML için dataset oluştur"""
    
    extractor = RaceFeatureExtractor()
    all_data = []
    
    print(f"📊 {len(race_files)} yarış işleniyor...")
    
    for i, race_file in enumerate(race_files, 1):
        if i % 50 == 0:
            print(f"   {i}/{len(race_files)} tamamlandı...")
        
        try:
            with open(race_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            race_data = data[0] if isinstance(data, list) else data
            
            race_info = {
                'race_id': race_data.get('race_id'),
                'race_date': race_data.get('race_date'),
                'city': race_data.get('city', ''),
                'track_type': race_data.get('track_type', ''),
                'distance': race_data.get('distance'),
            }
            
            for horse in race_data.get('horses', []):
                features = extractor.extract_all_features(horse, race_info)
                
                # Yarış bilgilerini ekle
                features['race_id'] = race_info['race_id']
                features['race_date'] = race_info['race_date']
                features['race_city'] = race_info['city']
                features['race_track_type'] = race_info['track_type']
                
                # At bilgilerini ekle
                features['horse_id'] = horse.get('horse_id')
                features['horse_name'] = horse.get('horse_name', '')
                
                all_data.append(features)
                
        except Exception as e:
            print(f"   ⚠️ Hata ({race_file.name}): {e}")
            continue
    
    # DataFrame oluştur
    df = pd.DataFrame(all_data)
    
    print(f"\n✓ {len(df)} at verisi işlendi")
    print(f"✓ {len(df.columns)} feature oluşturuldu")
    
    # Kaydet
    if output_file:
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✓ Dataset kaydedildi: {output_file}")
    
    return df


def main():
    """Ana fonksiyon"""
    
    race_jsons_dir = Path(r"E:\data\race_jsons")
    output_dir = Path(r"C:\Users\emir\Desktop\HorseRacingAPI-master\ml_data")
    output_dir.mkdir(exist_ok=True)
    
    print("="*80)
    print("ML DATASET OLUŞTURMA")
    print("="*80)
    print()
    
    # İlk 100 yarışı al
    all_files = list(race_jsons_dir.glob("**/*.json"))[:100]
    
    print(f"Toplam {len(all_files)} yarış dosyası bulundu\n")
    
    # Dataset oluştur
    output_file = output_dir / "ml_features_dataset.csv"
    df = create_ml_dataset(all_files, output_file)
    
    # Özet bilgiler
    print(f"\n{'='*80}")
    print("DATASET ÖZETİ")
    print(f"{'='*80}\n")
    print(df.describe().to_string())
    
    print(f"\n\nFeature İsimleri:")
    print(f"{'='*80}")
    for i, col in enumerate(df.columns, 1):
        print(f"{i:3d}. {col}")
    
    return df


if __name__ == "__main__":
    df = main()
