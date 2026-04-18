# -*- coding: utf-8 -*-
"""
Feature Importance Analizi - Hangi faktör birinciliği etkiliyor?
Linear Regression ile geçmiş yarışlardan öğren
"""
import sys
import json
import os
from pathlib import Path
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pickle
import numpy as np

def time_to_seconds(time_str):
    """Süre string'ini saniyeye çevir"""
    if not time_str or time_str == '' or time_str == 'YOK':
        return None
    try:
        time_str = str(time_str).strip()
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
        return float(time_str)
    except:
        return None

def extract_weight(weight_str):
    """Ağırlık çıkar"""
    if not weight_str or weight_str == 'YOK':
        return None
    try:
        return float(str(weight_str).replace(',', '.'))
    except:
        return None

def load_horse_data(horse_id):
    """Atın geçmiş yarış verilerini yükle"""
    horse_path = Path(f'E:/data/horses/{horse_id}/{horse_id}.json')
    if horse_path.exists():
        try:
            with open(horse_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('race_results', [])
        except:
            pass
    return []

def load_idman_data(horse_id):
    """Atın idman verilerini yükle"""
    idman_path = Path(f'E:/data/idman/{horse_id}.json')
    if idman_path.exists():
        try:
            with open(idman_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'idman_records' in data:
                    return data['idman_records']
        except:
            pass
    return []

def extract_features(horse, race_distance):
    """
    Bir atın özelliklerini çıkar
    Returns: dict of features
    """
    features = {}
    
    # KİLO
    kilo = extract_weight(horse.get('horse_weight'))
    features['kilo'] = kilo if kilo else 58.0  # Varsayılan
    
    # HANDİKAP
    handicap = extract_weight(horse.get('handicap_weight'))
    features['handicap'] = handicap if handicap else 0.0
    
    # DERECE (son yarıştan)
    horse_id = horse.get('horse_id')
    last_race_time = None
    
    if horse_id:
        races = load_horse_data(horse_id)
        if races:
            # En son yarışı al
            last_race = races[0]  # İlk eleman en son
            derece_str = last_race.get('derece')
            mesafe = last_race.get('mesafe')
            
            if derece_str and mesafe:
                derece_sec = time_to_seconds(derece_str)
                mesafe_val = int(mesafe.replace('m', '')) if mesafe else None
                
                if derece_sec and mesafe_val and mesafe_val > 0:
                    # 100m başına süre
                    last_race_time = derece_sec / (mesafe_val / 100)
    
    features['derece_100m'] = last_race_time if last_race_time else 8.0  # Varsayılan
    
    # İDMAN (en son idman)
    idman_records = load_idman_data(horse_id) if horse_id else []
    idman_400m = None
    idman_800m = None
    
    if idman_records:
        last_idman = idman_records[0]  # En son idman
        
        time_400 = time_to_seconds(last_idman.get('400m'))
        time_800 = time_to_seconds(last_idman.get('800m'))
        
        if time_400:
            idman_400m = time_400
        if time_800:
            idman_800m = time_800
    
    features['idman_400m'] = idman_400m if idman_400m else 30.0  # Varsayılan
    features['idman_800m'] = idman_800m if idman_800m else 60.0  # Varsayılan
    
    # START NO
    start_no = horse.get('start_no')
    try:
        start_int = int(str(start_no).replace('DS', '').replace('Tercihli Start', '').strip())
        features['start_no'] = start_int
    except:
        features['start_no'] = 5  # Varsayılan
    
    # MESAFE
    try:
        features['race_distance'] = int(race_distance)
    except:
        features['race_distance'] = 1200
    
    return features

def load_race_data_for_ml(city, year, month, max_races=50):
    """
    Bir şehir/ay için tüm yarışları yükle ve ML verisi oluştur
    Returns: X (features), y (target: 1=kazandı, 0=kaybetti)
    """
    program_path = Path(f'E:/data/program/{city}/{year}/{month:02d}.json')
    
    if not program_path.exists():
        return None, None
    
    try:
        with open(program_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Hata: {e}")
        return None, None
    
    X = []  # Features
    y = []  # Target (1=kazandı, 0=kaybetti)
    
    races_processed = 0
    
    # Her gün için
    for day_key, races in data.items():
        if not isinstance(races, dict):
            continue
            
        # Her yarış için
        for race_num, race_data in races.items():
            if races_processed >= max_races:
                break
            
            # race_data bir list ise horses o
            if isinstance(race_data, list):
                horses = race_data
                race_distance = '1200'  # Varsayılan
            else:
                horses = race_data.get('horses', [])
                race_distance = race_data.get('distance', '1200')
            
            if len(horses) < 3:  # En az 3 at olmalı
                continue
            
            # Kazananı bul (AGF'ye göre - en düşük = kazanan)
            winner_agf = None
            winner_idx = None
            
            for idx, horse in enumerate(horses):
                agf = horse.get('AGF')
                if agf and agf.strip():
                    try:
                        agf_val = int(agf)
                        if winner_agf is None or agf_val < winner_agf:
                            winner_agf = agf_val
                            winner_idx = idx
                    except:
                        pass
            
            if winner_idx is None:
                continue  # Kazanan belirlenemedi
            
            # Her at için features çıkar
            for idx, horse in enumerate(horses):
                features = extract_features(horse, race_distance)
                
                # Feature vector oluştur
                feature_vector = [
                    features['kilo'],
                    features['handicap'],
                    features['derece_100m'],
                    features['idman_400m'],
                    features['idman_800m'],
                    features['start_no'],
                    features['race_distance']
                ]
                
                # Target: Bu at kazandı mı?
                target = 1 if idx == winner_idx else 0
                
                X.append(feature_vector)
                y.append(target)
            
            races_processed += 1
        
        if races_processed >= max_races:
            break
    
    return np.array(X), np.array(y)

def main():
    print("=" * 80)
    print("FEATURE IMPORTANCE ANALİZİ")
    print("=" * 80)
    
    # Veri toplama
    print("\n📊 Geçmiş yarışlardan veri toplama...")
    
    all_X = []
    all_y = []
    
    # Son 3 aydan veri topla
    cities = ['Istanbul', 'Izmir', 'Ankara', 'Antalya', 'Bursa']
    months = [12, 11, 1]  # Aralık, Kasım, Ocak
    
    total_races = 0
    for city in cities:
        for month in months:
            year = 2025 if month in [11, 12] else 2026
            
            print(f"  {city} {month:02d}/{year}...", end=' ')
            
            X, y = load_race_data_for_ml(city, year, month, max_races=30)
            
            if X is not None and len(X) > 0:
                all_X.append(X)
                all_y.append(y)
                races = len(set(range(len(y))))
                total_races += races
                print(f"✓ {len(X)} at, {races} yarış")
            else:
                print("✗ Veri yok")
    
    if not all_X:
        print("\n❌ Hiç veri bulunamadı!")
        return
    
    # Veriyi birleştir
    X = np.vstack(all_X)
    y = np.hstack(all_y)
    
    print(f"\n✓ Toplam: {len(X)} at, {sum(y)} kazanan, {len(y) - sum(y)} kaybeden")
    
    # Veriyi normalize et
    print("\n🔧 Veriyi normalize ediyorum...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Model eğit
    print("\n🤖 Logistic Regression modeli eğitiliyor...")
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_scaled, y)
    
    # Accuracy
    accuracy = model.score(X_scaled, y)
    print(f"   Doğruluk: %{accuracy * 100:.1f}")
    
    # FEATURE IMPORTANCE!
    print("\n" + "=" * 80)
    print("🎯 FEATURE IMPORTANCE (HANGİ FAKTÖR BİRİNCİLİĞİ ETKİLİYOR?)")
    print("=" * 80)
    
    feature_names = [
        'Kilo',
        'Handicap', 
        'Derece (100m)',
        'İdman 400m',
        'İdman 800m',
        'Start No',
        'Yarış Mesafesi'
    ]
    
    coefficients = model.coef_[0]
    
    # Coefficient'lara göre sırala (mutlak değer)
    importance = list(zip(feature_names, coefficients))
    importance.sort(key=lambda x: abs(x[1]), reverse=True)
    
    print("\nÖnem Sıralaması (En önemliden en önemsize):")
    print("-" * 80)
    
    for i, (name, coef) in enumerate(importance, 1):
        etki = "ARTTIRIYOR ↑" if coef > 0 else "AZALTIYOR ↓"
        oran = abs(coef) / max(abs(c) for _, c in importance) * 100
        
        bar = "█" * int(oran / 5)
        
        print(f"{i}. {name:20s} | Katsayı: {coef:+8.4f} | {etki} | {bar} {oran:.1f}%")
    
    # Modeli kaydet
    print("\n💾 Model kaydediliyor...")
    with open('ml_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('ml_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    print("   ✓ ml_model.pkl")
    print("   ✓ ml_scaler.pkl")
    
    print("\n" + "=" * 80)
    print("✅ ANALİZ TAMAMLANDI!")
    print("=" * 80)
    
    print("\n📝 Sonuç:")
    print(f"   • En önemli faktör: {importance[0][0]}")
    print(f"   • En az önemli faktör: {importance[-1][0]}")
    print(f"   • Model doğruluğu: %{accuracy * 100:.1f}")

if __name__ == "__main__":
    main()
