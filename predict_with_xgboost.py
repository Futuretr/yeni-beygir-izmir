"""
XGBoost Modeli ile Yarış Tahmini
"""
import json
import pandas as pd
import numpy as np
from pathlib import Path
import xgboost as xgb
from create_ml_features import RaceFeatureExtractor
import sys
import re

def normalize_city_name(city):
    """Şehir ismini normalize et - Türkçe karakterleri kaldır ve capitalize yap"""
    if not city:
        return None
    
    # Türkçe karakterleri İngilizce'ye çevir
    replacements = {
        'ı': 'i', 'İ': 'I',
        'ş': 's', 'Ş': 'S',
        'ğ': 'g', 'Ğ': 'G',
        'ü': 'u', 'Ü': 'U',
        'ö': 'o', 'Ö': 'O',
        'ç': 'c', 'Ç': 'C'
    }
    
    city_normalized = city
    for tr_char, en_char in replacements.items():
        city_normalized = city_normalized.replace(tr_char, en_char)
    
    # İlk harfi büyük, geri kalanı küçük
    return city_normalized.capitalize()

def normalize_date(date_str):
    """Tarih formatını YYYY-MM-DD'ye çevir"""
    # Nokta veya slash'i tire ile değiştir
    date_str = date_str.replace('.', '-').replace('/', '-')
    
    # DD-MM-YYYY formatını algıla ve YYYY-MM-DD'ye çevir
    parts = date_str.split('-')
    
    if len(parts) != 3:
        return date_str  # Geçersiz format, olduğu gibi dön
    
    # İlk parça 4 haneliyse YYYY-MM-DD, değilse DD-MM-YYYY
    if len(parts[0]) == 4:
        # Zaten YYYY-MM-DD formatında
        return date_str
    else:
        # DD-MM-YYYY formatında, çevir
        day, month, year = parts
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

class XGBoostRacePredictor:
    """XGBoost modeli ile yarış tahmini"""
    
    def __init__(self, model_dir='xgboost_results'):
        """Eğitilmiş modelleri yükle"""
        self.model_dir = Path(model_dir)
        
        # Regression model (derece tahmini)
        reg_path = self.model_dir / 'xgboost_regression.json'
        self.reg_model = xgb.XGBRegressor()
        self.reg_model.load_model(reg_path)
        
        # Classification model (top 3 tahmini)
        clf_path = self.model_dir / 'xgboost_classification.json'
        self.clf_model = xgb.XGBClassifier()
        self.clf_model.load_model(clf_path)
        
        # Feature extractor
        self.extractor = RaceFeatureExtractor()
        
        # Model feature listesini yükle
        import pandas as pd
        feature_csv = self.model_dir / 'feature_importance_regression.csv'
        self.model_features = pd.read_csv(feature_csv)['feature'].tolist()
        
        print(f"✓ Modeller yüklendi: {model_dir}")
        print(f"✓ Feature sayısı: {len(self.model_features)}")
    
    def load_race_json(self, city, year, race_id):
        """Race JSON dosyasını yükle"""
        race_path = Path(f"E:/data/race_jsons/{city}/{year}/{race_id}.json")
        
        if not race_path.exists():
            return None
        
        with open(race_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Liste formatındaysa ilk elemanı al
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
    
    def prepare_race_data(self, race_data):
        """Yarış verisini ML formatına çevir"""
        horses = []
        
        # Race info oluştur
        race_info = {
            'category': race_data.get('race_category', ''),
            'track_type': race_data.get('track_type', ''),
            'distance': race_data.get('distance', 0),
            'age_group': race_data.get('age_group', ''),
            'city': race_data.get('city', '')
        }
        
        for horse in race_data.get('horses', []):
            # Her at için feature'ları çıkar
            features = self.extractor.extract_all_features(
                horse, 
                race_info
            )
            
            if features:
                features['horse_name'] = horse['horse_name']
                features['start_no'] = horse.get('start_no', 0)
                horses.append(features)
        
        if not horses:
            return None
        
        # DataFrame oluştur
        df = pd.DataFrame(horses)
        
        # Horse name ve start_no'yu kaydet
        horse_info = df[['horse_name', 'start_no']].copy()
        
        # Sadece modelde kullanılan VE mevcut olan feature'ları al
        available_features = [f for f in self.model_features if f in df.columns]
        missing_features = [f for f in self.model_features if f not in df.columns]
        
        # Eksik feature'ları 0 ile doldur
        X = df[available_features].copy()
        for feature in missing_features:
            X[feature] = 0
        
        # Model feature sırasına göre sırala
        X = X[self.model_features]
        
        # NaN ve inf değerleri temizle
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)
        
        return X, horse_info
    
    def predict_race(self, city, year, race_id):
        """Yarış için tahmin yap"""
        
        # Race verisini yükle
        race_data = self.load_race_json(city, year, race_id)
        
        if not race_data:
            return {'error': f'Yarış bulunamadı: {city}/{year}/{race_id}'}
        
        # Veriyi hazırla
        result = self.prepare_race_data(race_data)
        
        if result is None:
            return {'error': 'Feature extraction başarısız'}
        
        X, horse_info = result
        
        # Tahminleri yap
        predicted_positions = self.reg_model.predict(X)
        top3_probabilities = self.clf_model.predict_proba(X)[:, 1]  # Top 3 olma olasılığı
        
        # Gelişmiş skorlama: Her iki modeli de kullan
        # 1. Tahmini derece (düşük = iyi) -> normalize et (1-16 arası -> 100-0)
        # 2. Top 3 olasılığı (0-1 arası -> 0-100)
        # 3. İkisini birleştir
        
        max_pos = max(predicted_positions) if len(predicted_positions) > 0 else 16
        min_pos = min(predicted_positions) if len(predicted_positions) > 0 else 1
        
        # Sonuçları birleştir
        predictions = []
        for idx, (_, row) in enumerate(horse_info.iterrows()):
            # start_no'yu güvenli şekilde int'e çevir
            try:
                start_no = int(str(row['start_no']).split()[0]) if row['start_no'] else 0
            except (ValueError, AttributeError):
                start_no = idx + 1
            
            pred_pos = float(predicted_positions[idx])
            top3_prob = float(top3_probabilities[idx])
            
            # Derece skorunu normalize et (düşük derece = yüksek skor)
            if max_pos > min_pos:
                position_score = 100 * (1 - (pred_pos - min_pos) / (max_pos - min_pos))
            else:
                position_score = 50
            
            # Top 3 skorunu 0-100'e çevir
            prob_score = top3_prob * 100
            
            # YENİ SKORLAMA V2: Gerçek sonuçlar gösteriyor ki
            # Regression model (predicted position) ÇOK DAHA DOĞRU!
            # Position çok daha önemli -> %80 position, %20 probability
            combined_score = (position_score * 0.8) + (prob_score * 0.2)
            
            # Bonuslar:
            # 1. Çok iyi predicted position -> bonus
            if pred_pos < 6:
                combined_score = combined_score * 1.10  # %10 bonus
            elif pred_pos < 8:
                combined_score = combined_score * 1.05  # %5 bonus
            
            # 2. Hem iyi position hem iyi prob -> ekstra bonus
            if pred_pos < 8 and top3_prob > 0.3:
                combined_score = combined_score * 1.03  # %3 bonus
            
            predictions.append({
                'horse_name': row['horse_name'],
                'start_no': start_no,
                'predicted_position': pred_pos,
                'top3_probability': top3_prob,
                'position_score': position_score,
                'combined_score': min(combined_score, 100)  # Max 100
            })
        
        # Skorlara göre sırala
        predictions.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return {
            'race_info': {
                'category': race_data.get('race_category', 'N/A'),
                'track_type': race_data.get('track_type', 'N/A'),
                'distance': race_data.get('distance', 0),
                'age_group': race_data.get('age_group', 'N/A')
            },
            'predictions': predictions,
            'total_horses': len(predictions)
        }
    
    def predict_from_race_json_dir(self, city, year, target_date=None, race_number=None):
        """Race JSON dizininden doğrudan tahmin yap"""
        
        # Şehir ismini normalize et
        city = normalize_city_name(city)
        
        race_dir = Path(f"E:/data/race_jsons/{city}/{year}")
        
        if not race_dir.exists():
            return {'error': f'Şehir/yıl bulunamadı: {city}/{year}'}
        
        # Tüm race JSON dosyalarını al ve tarihe göre filtrele
        all_race_files = sorted(list(race_dir.glob("*.json")))
        
        if not all_race_files:
            return {'error': f'Yarış bulunamadı: {city}/{year}'}
        
        # Tarihe göre filtrele
        race_files = []
        for race_file in all_race_files:
            try:
                with open(race_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        race_data = data[0]
                    else:
                        race_data = data
                    
                    # Tarihe göre filtrele
                    if target_date:
                        if race_data.get('race_date') == target_date:
                            race_files.append((race_file, race_data.get('race_number', 0)))
                    else:
                        race_files.append((race_file, race_data.get('race_number', 0)))
            except Exception as e:
                continue
        
        if not race_files:
            return {'error': f'Belirtilen tarihte yarış bulunamadı: {target_date}'}
        
        # Race number'a göre sırala
        race_files.sort(key=lambda x: x[1])
        
        results = []
        
        # Belirli bir yarış numarası verilmişse
        if race_number is not None:
            # Race number'ı bul
            found = False
            for race_file, rnum in race_files:
                if rnum == race_number + 1:  # race_number 0-indexed, dosyada 1-indexed
                    race_id = race_file.stem
                    prediction = self.predict_race(city, year, race_id)
                    if 'error' not in prediction:
                        prediction['race_number'] = race_number
                        prediction['race_id'] = race_id
                        results.append(prediction)
                    found = True
                    break
            
            if not found:
                return {'error': f'Yarış numarası bulunamadı: {race_number + 1} (toplam {len(race_files)} yarış)'}
        else:
            # Tüm yarışları işle
            for idx, (race_file, rnum) in enumerate(race_files[:20]):  # max 20
                race_id = race_file.stem
                prediction = self.predict_race(city, year, race_id)
                if 'error' not in prediction:
                    prediction['race_number'] = idx
                    prediction['race_id'] = race_id
                    prediction['actual_race_number'] = rnum
                    results.append(prediction)
        
        return {
            'city': city,
            'year': year,
            'target_date': target_date,
            'total_races': len(results),
            'races': results
        }
    
    def predict_from_program(self, city, date, race_number=None):
        """Program verisinden tahmin yap"""
        
        # Şehir ismini normalize et
        city = normalize_city_name(city)
        
        # Tarihi normalize et
        date = normalize_date(date)
        
        program_dir = Path(f"E:/data/program/{city}")
        
        if not program_dir.exists():
            return {'error': f'Şehir bulunamadı: {city}'}
        
        # Tarih formatı: YYYY-MM-DD
        date_str = date.replace('.', '-').replace('/', '-')
        
        # Program dosyasını bul
        program_files = list(program_dir.glob(f"program_{date_str}_*.json"))
        
        if not program_files:
            return {'error': f'Tarih için program bulunamadı: {date}'}
        
        program_file = program_files[0]
        
        with open(program_file, 'r', encoding='utf-8') as f:
            program_data = json.load(f)
        
        results = []
        
        # Belirli bir yarış numarası verilmişse sadece onu işle
        if race_number is not None:
            if race_number >= len(program_data):
                return {'error': f'Yarış numarası geçersiz: {race_number} (toplam {len(program_data)} yarış)'}
            
            race = program_data[race_number]
            race_id = race.get('race_id')
            
            if race_id:
                year = date_str.split('-')[0]
                prediction = self.predict_race(city, year, race_id)
                if 'error' not in prediction:
                    prediction['race_number'] = race_number
                results.append(prediction)
        else:
            # Tüm yarışları işle
            year = date_str.split('-')[0]
            for idx, race in enumerate(program_data):
                race_id = race.get('race_id')
                if race_id:
                    prediction = self.predict_race(city, year, race_id)
                    if 'error' not in prediction:
                        prediction['race_number'] = idx
                        results.append(prediction)
        
        return {
            'city': city,
            'date': date,
            'total_races': len(results),
            'races': results
        }


def display_predictions(result):
    """Tahmin sonuçlarını göster"""
    
    if 'error' in result:
        print(f"❌ HATA: {result['error']}")
        return
    
    print("\n" + "="*100)
    if 'date' in result:
        print(f"📍 {result['city'].upper()} - {result['date']}")
    else:
        print(f"📍 {result['city'].upper()} - {result['year']}")
    print(f"📊 Toplam {result['total_races']} yarış")
    print("="*100)
    
    for race in result['races']:
        race_info = race['race_info']
        
        print(f"\n{'─'*100}")
        actual_num = race.get('actual_race_number', race['race_number'] + 1)
        print(f"🏇 YARIŞ #{actual_num}")
        print(f"{'─'*100}")
        print(f"Kategori: {race_info.get('category', 'N/A')}")
        print(f"Pist: {race_info.get('track_type', 'N/A')} - {race_info.get('distance', 'N/A')}m")
        print(f"Yaş: {race_info.get('age_group', 'N/A')}")
        print(f"Toplam At: {race['total_horses']}")
        
        print(f"\n{'Top 5 Tahmin':-^100}")
        
        for i, pred in enumerate(race['predictions'][:5], 1):
            print(f"\n{i}. {pred['horse_name']:30s} (#{pred['start_no']})")
            print(f"   🎯 SKOR: {pred['combined_score']:6.2f}/100")
            print(f"   📈 Tahmini Derece: {pred['predicted_position']:.2f}")
            print(f"   🏆 Top 3 Olasılığı: {pred['top3_probability']*100:.1f}%")
        
        print(f"\n{'─'*100}")
        print(f"💡 ÖNERİ: #{race['predictions'][0]['start_no']} {race['predictions'][0]['horse_name']} "
              f"(Skor: {race['predictions'][0]['combined_score']:.2f})")
        print(f"{'─'*100}")


def main():
    """Ana program"""
    
    print("\n" + "="*100)
    print("🐎 XGBOOST MODEL İLE AT YARIŞI TAHMİNİ")
    print("="*100)
    
    # Modeli yükle
    try:
        predictor = XGBoostRacePredictor()
    except Exception as e:
        print(f"❌ Model yüklenemedi: {e}")
        return
    
    print("\nÖrnek Kullanım:")
    print("  Şehir: Istanbul, Izmir, Ankara, Bursa, Adana vb.")
    print("  Tarih: 29.01.2026 veya 2026-01-29 formatında")
    print("  Yarış No: Boş bırakırsanız tüm yarışlar gösterilir (max 20)\n")
    
    while True:
        print("\n" + "─"*100)
        
        # Şehir
        city = input("Şehir [çıkmak için 'q']: ").strip()
        if city.lower() == 'q':
            print("\n👋 Görüşürüz!")
            break
        
        if not city:
            print("❌ Şehir giriniz!")
            continue
        
        # Tarih
        date = input("Tarih (GG.AA.YYYY veya YYYY-MM-DD): ").strip()
        if not date:
            print("❌ Tarih giriniz!")
            continue
        
        date = normalize_date(date)
        year = date.split('-')[0]
        
        # Yarış numarası (opsiyonel)
        race_input = input("Yarış No (boş=tümü, max 20): ").strip()
        race_number = None
        if race_input:
            try:
                race_number = int(race_input) - 1  # 0-indexed
            except ValueError:
                print("❌ Geçersiz yarış numarası!")
                continue
        
        # Tahmin yap
        print("\n⏳ Tahmin yapılıyor...")
        result = predictor.predict_from_race_json_dir(city, year, date, race_number)
        
        # Tarihi ekle
        if 'error' not in result:
            result['date'] = date
        
        # Sonuçları göster
        display_predictions(result)


if __name__ == "__main__":
    main()
