# -*- coding: utf-8 -*-
"""
Basit ML Modeli - Gerçek sonuçlardan pattern ö ğren
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from test_with_idman import load_race_from_program_with_idman
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Gerçek sonuçlar - Antalya 30.01.2026
gercek_sonuclar = {
    (0, "ÖZGÜNVERA"): 1,
    (0, "JET ÇELİK"): 2,
    (0, "GÜNMETE"): 3,
    (1, "DİLHUN"): 1,
    (1, "ŞEHNAZ LONGA"): 2,
    (1, "ÖZKEHRİBAR"): 3,
    (2, "ERSOYHAN"): 1,
    (2, "LUNA"): 2,
    (2, "ADEN PRENSİ"): 3,
    (3, "CESURSOY"): 1,
    (3, "MİKSER"): 2,
    (3, "OĞUZHANTAY"): 3,
    (4, "UNSEEN POWER"): 1,
    (4, "TYPHOON"): 2,
    (4, "SALONIKATOR"): 3,
    (5, "BOLİDE"): 1,
    (5, "EL ALACRAN"): 2,
    (5, "RIVABELLA"): 3,
    (6, "AGE OF DISCOVERY"): 1,
    (6, "DARK SOUL"): 2,
    (6, "MAHSA"): 3,
}

def extract_simple_features(horse, race_info):
    """Basit özellikler çıkar"""
    features = []
    
    # Start numarası - string olabilir, sadece sayıyı al
    start_no_str = str(horse.get('start_no', '0'))
    # "15DSTercihli Start" gibi → "15"
    start_no = int(''.join(filter(str.isdigit, start_no_str))) if start_no_str else 0
    features.append(start_no)
    
    # Yaş
    age_str = horse.get('horse_age', '0y')
    age = int(age_str.split('y')[0]) if 'y' in age_str else 0
    features.append(age)
    
    # Kilo
    weight_str = str(horse.get('horse_weight', '0'))
    weight = float(weight_str.replace(',', '.')) if weight_str else 0
    features.append(weight)
    
    # Handicap
    hw = horse.get('handicap_weight', 'YOK')
    if hw and hw != 'YOK':
        handicap = float(str(hw).replace(',', '.'))
    else:
        handicap = 0
    features.append(handicap)
    
    # Mesafe
    distance = int(race_info.get('distance', 1200))
    features.append(distance)
    
    # İdman var mı
    has_idman = 1 if horse.get('last_idman') else 0
    features.append(has_idman)
    
    return features

def main():
    print("=" * 80)
    print("BASİT ML MODELİ - PATTERN ÖĞRENİMİ")
    print("=" * 80)
    
    # Veri topla
    X = []
    y = []
    horse_names = []
    
    print("\nAntalya 30.01.2026 verisi yükleniyor...")
    for race_num in range(7):
        result = load_race_from_program_with_idman('Antalya', 2026, 1, 30, race_num)
        if not result:
            continue
        
        race_horses, race_info = result
        
        for horse in race_horses:
            horse_name = horse.get('horse_name')
            features = extract_simple_features(horse, race_info)
            
            # Label: Kazandı mı? (1,2,3 → kazandı=1, diğer=0)
            rank = gercek_sonuclar.get((race_num, horse_name), 99)
            won = 1 if rank <= 3 else 0
            
            X.append(features)
            y.append(won)
            horse_names.append((race_num, horse_name, rank))
    
    X = np.array(X)
    y = np.array(y)
    
    print(f"\nToplam {len(X)} at, {sum(y)} kazanan")
    print(f"Özellikler: start_no, age, weight, handicap, distance, has_idman")
    
    # Model eğit
    print("\n" + "=" * 80)
    print("MODEL EĞİTİMİ")
    print("=" * 80)
    
    # Train/test split
    X_train, X_test, y_train, y_test, names_train, names_test = train_test_split(
        X, y, horse_names, test_size=0.3, random_state=42
    )
    
    # Random Forest
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
    model.fit(X_train, y_train)
    
    # Tahmin
    y_pred = model.predict(X_test)
    
    # Sonuçlar
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {accuracy:.2%}")
    
    print("\nÖzellik Önemleri:")
    feature_names = ['Start No', 'Age', 'Weight', 'Handicap', 'Distance', 'Has İdman']
    for name, importance in zip(feature_names, model.feature_importances_):
        print(f"  {name:12s}: {importance:.3f}")
    
    # Test setindeki tahminler
    print("\n" + "=" * 80)
    print("TEST SETİ TAHMİNLERİ")
    print("=" * 80)
    
    for i, (race_num, horse_name, actual_rank) in enumerate(names_test):
        pred = y_pred[i]
        actual = y_test[i]
        prob = model.predict_proba([X_test[i]])[0][1]
        
        status = "✓" if pred == actual else "✗"
        print(f"{status} Koşu #{race_num+1} {horse_name:20s} Tahmin: {pred} (prob: {prob:.2f}) Gerçek: {actual} (sıra: {actual_rank})")
    
    # Modeli kaydet
    import pickle
    with open('horse_racing_ml_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    print("\n" + "=" * 80)
    print("Model kaydedildi: horse_racing_ml_model.pkl")
    print("=" * 80)

if __name__ == "__main__":
    main()
