# -*- coding: utf-8 -*-
"""
ML için veri hazırlama - Gerçek kazanan/kaybeden patternleri bul
"""
import json
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

def time_to_seconds(time_str):
    """Süre string'ini saniyeye çevir"""
    if not time_str or time_str == '':
        return None
    try:
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        return float(time_str)
    except:
        return None

def extract_features_from_horse(horse, race_info, race_date):
    """Attan özellikler çıkar"""
    features = {}
    
    # Temel bilgiler
    features['horse_id'] = horse.get('horse_id')
    features['horse_name'] = horse.get('horse_name')
    features['start_no'] = horse.get('start_no', 0)
    features['age'] = horse.get('horse_age', '0y').split('y')[0] if horse.get('horse_age') else 0
    
    # Kilo
    weight_str = str(horse.get('horse_weight', '0'))
    features['weight'] = float(weight_str.replace(',', '.')) if weight_str else 0
    
    # Handicap
    hw = horse.get('handicap_weight', 'YOK')
    if hw and hw != 'YOK':
        features['handicap'] = float(str(hw).replace(',', '.'))
    else:
        features['handicap'] = 0
    
    # Yarış bilgileri
    features['race_distance'] = int(race_info.get('distance', 0))
    features['track_type'] = race_info.get('track_type', 'Kum')
    features['category'] = race_info.get('category', 'Unknown')
    
    # Geçmiş performans
    horse_file = Path(f"E:/data/horses/{horse.get('horse_id')}/{horse.get('horse_id')}.json")
    if horse_file.exists():
        try:
            with open(horse_file, 'r', encoding='utf-8') as f:
                horse_history = json.load(f)
                
            # Son 5 yarışın ortalaması
            races = horse_history.get('races', [])
            recent_races = []
            for race in races:
                race_date_str = race.get('date')
                if race_date_str:
                    try:
                        r_date = datetime.strptime(race_date_str, '%d.%m.%Y')
                        program_date = datetime.strptime(race_date, '%d.%m.%Y')
                        if r_date < program_date:
                            recent_races.append(race)
                    except:
                        pass
            
            recent_races = sorted(recent_races, key=lambda x: x.get('date', ''), reverse=True)[:5]
            
            if recent_races:
                # Son 5 yarıştaki ortalama derece
                times = []
                for race in recent_races:
                    time_str = race.get('time')
                    distance = race.get('distance')
                    if time_str and distance:
                        seconds = time_to_seconds(time_str)
                        if seconds and int(distance) > 0:
                            time_100m = seconds / (int(distance) / 100)
                            times.append(time_100m)
                
                features['avg_100m_time'] = sum(times) / len(times) if times else 0
                features['best_100m_time'] = min(times) if times else 0
                features['recent_race_count'] = len(recent_races)
                
                # Son yarıştaki sıralama
                if recent_races[0].get('rank'):
                    features['last_rank'] = int(recent_races[0].get('rank', 0))
                else:
                    features['last_rank'] = 0
            else:
                features['avg_100m_time'] = 0
                features['best_100m_time'] = 0
                features['recent_race_count'] = 0
                features['last_rank'] = 0
                
        except Exception as e:
            features['avg_100m_time'] = 0
            features['best_100m_time'] = 0
            features['recent_race_count'] = 0
            features['last_rank'] = 0
    else:
        features['avg_100m_time'] = 0
        features['best_100m_time'] = 0
        features['recent_race_count'] = 0
        features['last_rank'] = 0
    
    # İdman verileri
    idman_file = Path(f"E:/data/idman/{horse.get('horse_id')}.json")
    if idman_file.exists() and os.path.getsize(idman_file) > 10:
        try:
            with open(idman_file, 'r', encoding='utf-8') as f:
                idman_data = json.load(f)
            
            if idman_data and 'idman_records' in idman_data:
                records = idman_data['idman_records']
                if records:
                    # Son idman
                    latest = records[0]
                    
                    # 400m idman süresi
                    time_400 = time_to_seconds(latest.get('400m', ''))
                    features['idman_400m'] = time_400 if time_400 else 0
                    
                    # 800m idman süresi
                    time_800 = time_to_seconds(latest.get('800m', ''))
                    features['idman_800m'] = time_800 if time_800 else 0
                    
                    features['has_idman'] = 1
                else:
                    features['idman_400m'] = 0
                    features['idman_800m'] = 0
                    features['has_idman'] = 0
            else:
                features['idman_400m'] = 0
                features['idman_800m'] = 0
                features['has_idman'] = 0
        except:
            features['idman_400m'] = 0
            features['idman_800m'] = 0
            features['has_idman'] = 0
    else:
        features['idman_400m'] = 0
        features['idman_800m'] = 0
        features['has_idman'] = 0
    
    return features

def load_program_data(city, year, month):
    """Program verilerini yükle"""
    # Dosya adı 01, 02, ... formatında
    month_str = f"{month:02d}"
    program_file = Path(f"E:/data/program/{city}/{year}/{month_str}.json")
    if not program_file.exists():
        return []
    
    with open(program_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Format: {"30.01.2026": {"races": [...]}, ...}
    return data

def main():
    """Ana fonksiyon - Tüm yarış verilerini topla"""
    print("ML VERİ HAZIRLAMA BAŞLIYOR...")
    print("=" * 80)
    
    all_data = []
    
    # Örnek: Antalya, Ocak 2026
    cities = ['Antalya', 'Istanbul', 'Izmir', 'Ankara']
    
    for city in cities:
        print(f"\n{city} verileri yükleniyor...")
        
        for year in [2025, 2026]:
            for month in range(1, 13):
                program_data = load_program_data(city, year, month)
                
                if not program_data:
                    continue
                
                # Format: {day: {race_number: [horses]}}
                for day_key, day_races in program_data.items():
                    for race_key, race_horses in day_races.items():
                        if not race_horses:
                            continue
                        
                        # İlk atın bilgilerinden yarış bilgilerini al
                        first_horse = race_horses[0]
                        race_date = first_horse.get('race_date')
                        
                        race_info = {
                            'distance': first_horse.get('distance'),
                            'track_type': first_horse.get('track_type'),
                            'category': first_horse.get('race_category', '').split('/')[0].strip(),
                            'city': city
                        }
                        
                        # Her attan features çıkar
                        for horse in race_horses:
                            features = extract_features_from_horse(horse, race_info, race_date)
                            
                            # Label ekle (kazanan mı?)
                            # Gerçek sonuç verisi olması gerekiyor
                            # Şimdilik varsayılan
                            features['won'] = 0  # Bunu gerçek sonuçlarla güncelleyeceğiz
                            
                            all_data.append(features)
                
                if program_data:
                    print(f"  {year}/{month:02d}: {len(program_data)} gün, toplam {len(all_data)} at")
    
    # DataFrame'e çevir
    df = pd.DataFrame(all_data)
    
    # Kaydet
    output_file = 'ml_training_data.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n{'=' * 80}")
    print(f"Toplam {len(df)} at verisi hazırlandı")
    print(f"Dosya kaydedildi: {output_file}")
    print(f"{'=' * 80}")
    
    # Özet istatistikler
    print(f"\nÖzellikler:")
    print(df.columns.tolist())
    print(f"\nİlk 5 satır:")
    print(df.head())

if __name__ == "__main__":
    main()
