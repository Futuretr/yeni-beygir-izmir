import json
import math
from pathlib import Path
from datetime import datetime

# DERECE SKORLAMA TABLOSU (saniye farkı → puan)
DERECE_SKOR_TABLOSU = [
    (-1.00, 50, 'Efsane'),
    (-0.80, 45, 'Olağanüstü'),
    (-0.60, 40, 'Çok Güçlü'),
    (-0.40, 35, 'Üst Düzey'),
    (-0.30, 30, 'Mükemmel'),
    (-0.20, 25, 'Formda'),
    (-0.15, 20, 'Belirgin İyi'),
    (-0.10, 15, 'Avantajlı'),
    (-0.06, 10, 'Dişli'),
    (-0.04, 7, 'Hazır'),
    (-0.02, 5, 'Kıpırdanma'),
    (-0.01, 4, 'Burun Farkı'),
    (0.00, 3, 'Tam Uyum'),
    (0.01, 2, 'Baş Başa'),
    (0.02, 1, 'Eşik'),
    (0.03, 0, 'Nötr'),
    (0.05, -2, 'Sınıf Altı'),
    (0.07, -5, 'Zayıf'),
    (0.10, -8, 'Geride'),
    (0.15, -12, 'Yavaş'),
    (0.20, -16, 'Formsuz'),
    (0.30, -25, 'Çok Yavaş'),
    (0.50, -35, 'Grup Dışı'),
    (1.00, -50, 'İmkansız')
]

# İDMAN SKORLAMA TABLOSU (saniye farkı → puan PER MESAFE)
IDMAN_SKOR_TABLOSU = [
    (-3.00, 50, 'Süper Hazır'),
    (-2.80, 47, 'Çok Canlı'),
    (-2.60, 44, 'Işıltılı'),
    (-2.40, 41, 'Formda'),
    (-2.20, 38, 'Dikkat Çekici'),
    (-2.00, 35, 'Umut Veren'),
    (-1.80, 31, 'İyi Hazırlık'),
    (-1.60, 28, 'Kıpırdandı'),
    (-1.40, 25, 'Gelişiyor'),
    (-1.20, 22, 'Olumlu'),
    (-1.00, 19, 'Isınıyor'),
    (-0.80, 16, 'Diri'),
    (-0.60, 12, 'Hazır'),
    (-0.40, 8, 'Normal+'),
    (-0.20, 5, 'Standart'),
    (0.00, 3, 'Rutin'),
    (0.40, 0, 'Durağan'),
    (0.80, -5, 'Tembel'),
    (1.20, -10, 'Ağır'),
    (1.60, -15, 'Formsuz'),
    (2.00, -25, 'Çok Eksik'),
    (4.00, -50, 'Çıkmaz')
]

# Şehir + Pist kombinasyonları için ortalama hızlar (m/s)
SEHIR_PIST_HIZLARI = {
    'adana_kum': 14.7505,
    'adana_çim': 15.7531,
    'adana_sentetik': 15.2500,
    'ankara_kum': 14.7742,
    'ankara_çim': 15.7185,
    'ankara_sentetik': 15.2400,
    'bursa_kum': 14.9345,
    'bursa_çim': 15.8318,
    'bursa_sentetik': 15.3800,
    'diyarbakir_kum': 13.6108,
    'diyarbakir_çim': 14.6100,
    'diyarbakir_sentetik': 14.1000,
    'elazig_kum': 14.0952,
    'elazig_çim': 15.0900,
    'elazig_sentetik': 14.5900,
    'istanbul_kum': 14.9100,
    'istanbul_sentetik': 15.5146,
    'istanbul_çim': 15.7403,
    'antalya_kum': 14.9100,
    'antalya_sentetik': 15.5146,
    'antalya_çim': 15.7403,
    'izmir_kum': 14.9163,
    'izmir_çim': 15.7113,
    'izmir_sentetik': 15.3100,
    'kocaeli_kum': 14.8824,
    'kocaeli_çim': 15.8800,
    'kocaeli_sentetik': 15.3800,
    'sanliurfa_kum': 13.9314,
    'sanliurfa_çim': 14.9300,
    'sanliurfa_sentetik': 14.4300
}

def normalize_city_name(city):
    """Şehir ismini normalize et"""
    if not city:
        return None
    city_lower = city.lower()
    city_lower = city_lower.replace('ı', 'i').replace('ş', 's').replace('ğ', 'g').replace('ü', 'u').replace('ö', 'o').replace('ç', 'c')
    
    city_mapping = {
        'istanbul': 'istanbul',
        'ankara': 'ankara',
        'izmir': 'izmir',
        'bursa': 'bursa',
        'adana': 'adana',
        'antalya': 'antalya',
        'kocaeli': 'kocaeli',
        'sanliurfa': 'sanliurfa',
        'diyarbakir': 'diyarbakir',
        'elazig': 'elazig'
    }
    
    for key in city_mapping:
        if key in city_lower:
            return city_mapping[key]
    return None

def normalize_track_type(track):
    """Pist tipini normalize et"""
    if not track:
        return None
    track_lower = track.lower()
    
    if 'kum' in track_lower:
        return 'kum'
    elif 'çim' in track_lower or 'cim' in track_lower:
        return 'çim'
    elif 'sentetik' in track_lower:
        return 'sentetik'
    return None

def get_sehir_pist_key(sehir, pist):
    """Şehir ve pist türünden anahtar oluştur"""
    sehir_clean = normalize_city_name(sehir)
    pist_clean = normalize_track_type(pist)
    if sehir_clean and pist_clean:
        return f"{sehir_clean}_{pist_clean}"
    return None

def calculate_kadapt(gecmis_sehir, gecmis_pist, hedef_sehir, hedef_pist):
    """Pist adaptasyon katsayısını hesapla"""
    hedef_key = get_sehir_pist_key(hedef_sehir, hedef_pist)
    gecmis_key = get_sehir_pist_key(gecmis_sehir, gecmis_pist)
    
    if not hedef_key or not gecmis_key:
        return 1.0
    
    hedef_hiz = SEHIR_PIST_HIZLARI.get(hedef_key)
    gecmis_hiz = SEHIR_PIST_HIZLARI.get(gecmis_key)
    
    if hedef_hiz and gecmis_hiz:
        return gecmis_hiz / hedef_hiz

def get_score_from_table(time_diff, table):
    """Zaman farkından tablo bazlı skor hesapla (interpolasyon ile)"""
    # Eğer tam eşleşme varsa
    for threshold, score, _ in table:
        if abs(time_diff - threshold) < 0.001:
            return score
    
    # İnterpolasyon yap
    for i in range(len(table) - 1):
        curr_threshold, curr_score, _ = table[i]
        next_threshold, next_score, _ = table[i + 1]
        
        # time_diff bu iki eşik arasındaysa
        if curr_threshold <= time_diff <= next_threshold:
            # Lineer interpolasyon
            ratio = (time_diff - curr_threshold) / (next_threshold - curr_threshold)
            return curr_score + ratio * (next_score - curr_score)
    
    # Tablonun dışındaysa en uç değeri kullan
    if time_diff < table[0][0]:
        return table[0][1]
    else:
        return table[-1][1]
    
    return 1.0

def extract_age_years(horse_age):
    """Yaş string'inden yıl çıkar"""
    if not horse_age or not isinstance(horse_age, str):
        return None
    try:
        age_str = horse_age.split('y')[0].strip()
        return int(age_str)
    except:
        return None

def extract_weight(horse_weight):
    """Ağırlık string'inden sayı çıkar"""
    if not horse_weight:
        return None
    try:
        weight_str = str(horse_weight).replace(',', '.')
        return float(weight_str)
    except:
        return None

def time_to_seconds(time_str):
    """Süre string'ini saniyeye çevir: "1.13.46" -> 73.46"""
    if not time_str or time_str == 'N/A':
        return None
    try:
        parts = str(time_str).split('.')
        if len(parts) >= 2:
            minutes = int(parts[0]) if parts[0] else 0
            seconds = int(parts[1]) if parts[1] else 0
            centiseconds = int(parts[2]) if len(parts) > 2 and parts[2] else 0
            return minutes * 60 + seconds + centiseconds / 100
    except:
        return None

def find_dream_horse(category, city, breed, track_type, distance):
    """Dream Horse profilini bul"""
    dream_dir = Path("E:\\data\\stats\\dream_horse")
    
    # Kategori klasörü
    category_dir = dream_dir / category
    if not category_dir.exists():
        return None
    
    # Şehir klasörü
    city_dir = category_dir / city
    if not city_dir.exists():
        return None
    
    # Breed klasörü
    breed_dir = city_dir / breed
    if not breed_dir.exists():
        return None
    
    # Pist + mesafe dosyası
    dream_file = breed_dir / f"{track_type}_{distance}m.json"
    if not dream_file.exists():
        return None
    
    try:
        with open(dream_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def get_horse_last_race_data(horse, race_date):
    """
    Atın programdaki yarış tarihinden ÖNCE olan son yarışını al
    
    Args:
        horse: Programdaki at verisi
        race_date: Programdaki yarış tarihi (ISO format: "2024-01-27T00:00:00Z")
    
    Returns:
        Bir önceki yarış verisi veya None
    """
    horse_id = horse.get('horse_id')
    if not horse_id:
        return None
    
    # Horses klasöründen veriyi yükle - her at kendi klasöründe
    horse_file = Path(f"E:\\data\\horses\\{horse_id}\\{horse_id}.json")
    
    if not horse_file.exists():
        return None
    
    try:
        with open(horse_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        races = data.get('races', [])
        if not races:
            return None
        
        # Programdaki yarış tarihini parse et
        try:
            if isinstance(race_date, str):
                # ISO format: "2024-01-27T00:00:00Z"
                program_date = datetime.fromisoformat(race_date.replace('Z', '+00:00'))
            else:
                return None
        except:
            return None
        
        # Yarış tarihinden ÖNCE olan yarışları filtrele
        previous_races = []
        for race in races:
            try:
                race_date_str = race.get('race_date', '')
                if race_date_str:
                    race_dt = datetime.fromisoformat(race_date_str.replace('Z', '+00:00'))
                    if race_dt < program_date:
                        previous_races.append(race)
            except:
                continue
        
        if not previous_races:
            return None
        
        # En son olanı (tarihe göre) bul
        last_race = max(previous_races, key=lambda r: r.get('race_date', ''))
        return last_race
        
    except Exception as e:
        return None

def calculate_adjusted_100m_time(horse, race_city, race_track, race_distance, race_date):
    """Atın normalize edilmiş 100m süresini hesapla (programdaki yarıştan önceki son yarışa göre)"""
    last_race = get_horse_last_race_data(horse, race_date)
    
    if not last_race:
        return None
    
    # Son yarış derece verisi
    last_time_str = last_race.get('time')
    last_distance = last_race.get('distance')
    last_city = last_race.get('city')
    last_track = last_race.get('track_type')
    
    if not all([last_time_str, last_distance, last_city, last_track]):
        return None
    
    # Süreyi saniyeye çevir
    derece_saniye = time_to_seconds(last_time_str)
    if not derece_saniye:
        return None
    
    # Pist adaptasyonu
    kadapt = calculate_kadapt(last_city, last_track, race_city, race_track)
    adjusted_derece = derece_saniye * kadapt
    
    # 100m başına süre hesapla (son yarışta)
    mevcut_100m_sure = adjusted_derece / (last_distance / 100)
    
    # Mesafe farklılığını hesapla
    try:
        last_distance_float = float(last_distance)
        race_distance_float = float(race_distance)
        mesafe_farki = race_distance_float - last_distance_float
        
        if mesafe_farki > 0:
            # Uzun mesafeye geçiş - 100m başına +0.04 saniye
            mesafe_faktoru = 0.04
            yeni_100m_sure = mevcut_100m_sure + (abs(mesafe_farki) / 100) * mesafe_faktoru
        elif mesafe_farki < 0:
            # Kısa mesafeye geçiş - 100m başına -0.03 saniye
            mesafe_faktoru = -0.03
            yeni_100m_sure = mevcut_100m_sure + (abs(mesafe_farki) / 100) * mesafe_faktoru
        else:
            # Aynı mesafe
            yeni_100m_sure = mevcut_100m_sure
        
        return yeni_100m_sure
    except:
        return None

def calculate_euclidean_distance(horse, dream, race_city, race_track, race_distance, race_date):
    """
    Euclidean Distance hesapla - YAŞ VE START ÇIKARILDI, DERECE EKLENDİ
    
    Bileşenler:
    1. Kilo farkı (kg)
    2. Handicap farkı (kg) 
    3. 100m süre farkı (saniye × 3 çarpan)
    """
    differences = []
    
    # Ağırlık farkı (ÖNEMLİ)
    horse_weight = extract_weight(horse.get('horse_weight'))
    dream_weight = extract_weight(dream.get('horse_weight'))
    if horse_weight and dream_weight:
        weight_diff = horse_weight - dream_weight
        differences.append(weight_diff ** 2)
    
    # Handicap weight farkı (ÖNEMLİ) - DÜZELTİLDİ
    horse_hw = extract_weight(horse.get('handicap_weight')) or 0  # YOK ise 0
    dream_hw = extract_weight(dream.get('handicap_weight')) or 0  # YOK ise 0
    hw_diff = horse_hw - dream_hw
    differences.append(hw_diff ** 2)
    
    # DERECE FARKI (EN ÖNEMLİ) - normalize edilmiş 100m süreleri
    horse_100m = calculate_adjusted_100m_time(horse, race_city, race_track, race_distance, race_date)
    dream_time_str = dream.get('time')
    
    if horse_100m and dream_time_str:
        dream_time_seconds = time_to_seconds(dream_time_str)
        if dream_time_seconds:
            dream_100m = dream_time_seconds / (int(race_distance) / 100)
            # 100m süre farkı (saniye cinsinden, ağırlıklandırılmış)
            # x3 çarpanı - derece önemli ama çok agresif olmamalı
            time_diff = (horse_100m - dream_100m) * 3
            differences.append(time_diff ** 2)
    
    # Eğer hiç fark yoksa, en azından sabit bir değer dön
    if not differences:
        return 10.0  # Orta seviye mesafe (varsayılan)
    
    return math.sqrt(sum(differences))

def normalize_idman_time(idman_time_seconds, idman_turu):
    """İdman süresini normalize et - İç/Sprint durumuna göre"""
    if not idman_time_seconds or not idman_turu:
        return idman_time_seconds
    
    turu_lower = str(idman_turu).lower()
    
    # İç yapıldıysa daha kolay, süreyi düşür (1 saniye bonus)
    if 'iç' in turu_lower or 'ic' in turu_lower:
        return idman_time_seconds - 1.0
    
    # Sprint yapıldıysa daha zor, süreyi arttır (1 saniye ceza)
    if 'sprint' in turu_lower:
        return idman_time_seconds + 1.0
    
    return idman_time_seconds

def calculate_idman_score(horse_idman, dream, race_city, race_track):
    """İdman karşılaştırması ve bonus hesaplama - YENİ TABLO SİSTEMİ"""
    if not horse_idman:
        return 0, {}
    
    idman_distances = ['400m', '600m', '800m', '1000m', '1200m']
    bonus_points = 0
    comparison = {}
    
    # İdman şehir, pist ve tur bilgisi
    idman_city = horse_idman.get('İ. Hip.') or horse_idman.get('Ä°. Hip.')
    idman_track = horse_idman.get('Pist')
    idman_turu = horse_idman.get('Tur')  # İç/Sprint/Normal bilgisi
    
    for dist in idman_distances:
        horse_time_str = horse_idman.get(dist)
        dream_time_str = dream.get(f'idman_{dist}')
        
        if not horse_time_str or not dream_time_str or horse_time_str == '' or dream_time_str == '':
            continue
        
        # Süreleri saniyeye çevir
        horse_time = time_to_seconds(horse_time_str)
        dream_time = time_to_seconds(dream_time_str)
        
        if not horse_time or not dream_time:
            continue
        
        # İç/Sprint normalizasyonu uygula
        horse_time = normalize_idman_time(horse_time, idman_turu)
        
        # Normalize et: İdman farklı pistteyse düzelt
        idman_city_norm = normalize_city_name(idman_city)
        idman_track_norm = normalize_track_type(idman_track)
        race_city_norm = normalize_city_name(race_city)
        race_track_norm = normalize_track_type(race_track)
        
        if all([idman_city_norm, idman_track_norm, race_city_norm, race_track_norm]):
            idman_key = f"{idman_city_norm}_{idman_track_norm}"
            race_key = f"{race_city_norm}_{race_track_norm}"
            
            idman_speed = SEHIR_PIST_HIZLARI.get(idman_key)
            race_speed = SEHIR_PIST_HIZLARI.get(race_key)
            
            if idman_speed and race_speed:
                # Pist normalizasyonu
                horse_time = horse_time * (idman_speed / race_speed)
        
        # NORMAL: İyi idman = bonus
        time_diff = dream_time - horse_time  # Negatif = at hızlı (iyi)
        bonus = get_score_from_table(time_diff, IDMAN_SKOR_TABLOSU)
        
        bonus_points += bonus
        comparison[dist] = {
            'horse': horse_time_str,
            'dream': dream_time_str,
            'normalized_horse': round(horse_time, 2),
            'normalized_dream': dream_time,
            'time_diff': round(time_diff, 2),
            'bonus': round(bonus, 2),
            'faster': time_diff < 0
        }
    
    return bonus_points, comparison

def predict_race(race_data, race_info):
    """
    Yarış tahmin sistemi - YENİ TABLO SİSTEMİ
    
    Args:
        race_data: Yarıştaki atların listesi
        race_info: Yarış bilgileri (kategori, şehir, pist, mesafe)
    
    Returns:
        Tahmin sonuçları
    """
    category = race_info['category']
    city = race_info['city']
    track_type = race_info['track_type']
    distance = race_info['distance']
    age_group = race_info.get('age_group', '')
    
    # Breed belirle
    if 'İngiliz' in age_group:
        breed = 'İngiliz'
    elif 'Arap' in age_group:
        breed = 'Arap'
    else:
        breed = 'Diğer'
    
    # Dream Horse'u bul
    dream = find_dream_horse(category, city, breed, track_type, distance)
    
    if not dream:
        return {
            'error': f'Dream Horse bulunamadı: {category}/{city}/{breed}/{track_type}_{distance}m',
            'predictions': []
        }
    
    predictions = []
    
    for horse in race_data:
        race_date = race_info.get('race_date')
        
        # DERECE SKORU - YENİ TABLO SİSTEMİ
        horse_100m = calculate_adjusted_100m_time(horse, city, track_type, distance, race_date)
        dream_time_str = dream.get('time')
        
        derece_score = 0
        derece_time_diff = None
        
        if horse_100m and dream_time_str:
            dream_time_seconds = time_to_seconds(dream_time_str)
            if dream_time_seconds:
                dream_100m = dream_time_seconds / (int(distance) / 100)
                # NORMAL: Negatif = at daha hızlı (iyi)
                derece_time_diff = dream_100m - horse_100m
                derece_score = get_score_from_table(derece_time_diff, DERECE_SKOR_TABLOSU)
        
        # İdman skoru hesapla - YENİ TABLO SİSTEMİ
        horse_idman = horse.get('last_idman')
        idman_score, idman_comparison = calculate_idman_score(horse_idman, dream, city, track_type)
        
        # MESAFE ÇARPANLARI
        try:
            distance_int = int(distance)
            
            # 1200m-1400m: Derece önemli (hız önemli)
            if 1200 <= distance_int <= 1400:
                derece_score *= 1.2
            
            # 1900m-2400m: İdman önemli (kondisyon önemli)
            if 1900 <= distance_int <= 2400:
                idman_score *= 1.2
        except:
            pass
        
        # Final skor
        final_score = derece_score + idman_score
        
        # 100 üzerinden normalizasyon (negatif de olabilir)
        # Skorları makul aralıkta tut (teorik max: 50 derece + 50 idman = 100)
        # Ancak mesafe çarpanlarıyla 120'ye çıkabilir, bunu 100'e normalize et
        if final_score > 100:
            final_score = 100
        elif final_score < -50:
            final_score = -50
        
        predictions.append({
            'horse_name': horse.get('horse_name'),
            'horse_id': horse.get('horse_id'),
            'start_no': horse.get('start_no'),
            'jockey': horse.get('jockey_name'),
            'trainer': horse.get('trainer_name'),
            'score': round(final_score, 2),
            'derece_score': round(derece_score, 2),
            'idman_score': round(idman_score, 2),
            'derece_time_diff': round(derece_time_diff, 2) if derece_time_diff else None,
            'idman_comparison': idman_comparison,
            'details': {
                'age': horse.get('horse_age'),
                'weight': horse.get('horse_weight'),
                'handicap_weight': horse.get('handicap_weight'),
                'has_idman': horse_idman is not None,
                'distance': distance
            }
        })
    
    # Skora göre sırala (yüksekten düşüğe - NORMAL SISTEM)
    predictions.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'race_info': race_info,
        'dream_horse': {
            'category': category,
            'city': city,
            'breed': breed,
            'track_type': track_type,
            'distance': distance,
            'total_wins_analyzed': dream['_metadata']['total_wins_analyzed']
        },
        'predictions': predictions
    }

def main():
    """Test için örnek kullanım"""
    print("=" * 80)
    print("AT YARIŞI TAHMİN SİSTEMİ")
    print("=" * 80)
    print("\nKullanım:")
    print("1. Program dosyasından yarış verilerini yükle")
    print("2. predict_race() fonksiyonuna gönder")
    print("3. 0-100 arası kazanma uyumu skorları al")
    print("\nÖrnek:")
    print("  from predict_race import predict_race")
    print("  results = predict_race(race_horses, race_info)")
    print("  for pred in results['predictions']:")
    print("      print(f\"{pred['horse_name']}: {pred['score']}/100\")")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
