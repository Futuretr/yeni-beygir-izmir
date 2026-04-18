import json
import os
from pathlib import Path
from collections import Counter
import statistics

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
    """Şehir ismini normalize et (lowercase, Turkish chars)"""
    if not city:
        return None
    city_lower = city.lower()
    # Turkish char fixes
    city_lower = city_lower.replace('ı', 'i').replace('ş', 's').replace('ğ', 'g').replace('ü', 'u').replace('ö', 'o').replace('ç', 'c')
    
    # Şehir ismi eşleştirmeleri
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

def normalize_idman_time(idman_time_seconds, idman_city, idman_track, race_city, race_track):
    """
    İdman süresini yarış pistinin hızına göre normalize et.
    Farklı pistte yapılan idmanı, yarış pistine göre ayarlar.
    """
    # Şehir ve pist bilgilerini normalize et
    idman_city_norm = normalize_city_name(idman_city)
    idman_track_norm = normalize_track_type(idman_track)
    race_city_norm = normalize_city_name(race_city)
    race_track_norm = normalize_track_type(race_track)
    
    if not all([idman_city_norm, idman_track_norm, race_city_norm, race_track_norm]):
        return idman_time_seconds  # Normalize edilemezse orijinal süreyi döndür
    
    # Pist hızlarını al
    idman_key = f"{idman_city_norm}_{idman_track_norm}"
    race_key = f"{race_city_norm}_{race_track_norm}"
    
    idman_speed = SEHIR_PIST_HIZLARI.get(idman_key)
    race_speed = SEHIR_PIST_HIZLARI.get(race_key)
    
    if not idman_speed or not race_speed:
        return idman_time_seconds  # Hız bilgisi yoksa orijinal süreyi döndür
    
    # Hız oranına göre süreyi düzelt
    # Daha hızlı pistte idman yapıldıysa, süre daha kısa olur
    # Normalize edilmiş süre = orijinal_süre * (idman_hızı / yarış_hızı)
    normalized_time = idman_time_seconds * (idman_speed / race_speed)
    
    return normalized_time

def extract_age_years(horse_age):
    """
    Horse age string'inden yaş yılını çıkarır.
    Örnek: "2y a  e" -> 2
    """
    if not horse_age or not isinstance(horse_age, str):
        return None
    
    try:
        # İlk karakterleri al (sayı olmalı)
        age_str = horse_age.split('y')[0].strip()
        return int(age_str)
    except:
        return None

def extract_weight(horse_weight):
    """
    Horse weight string'inden sayısal değeri çıkarır.
    Örnek: "57", "55,5" -> float
    """
    if not horse_weight:
        return None
    
    try:
        # Virgülü noktaya çevir
        weight_str = str(horse_weight).replace(',', '.')
        return float(weight_str)
    except:
        return None

def create_dream_horse_profile(wins_data, category_name, city_name, track_distance):
    """
    Birinci gelen atlardan ideal at profili oluşturur - normal at formatında.
    """
    if not wins_data:
        return None
    
    # Yaşları topla
    ages = [extract_age_years(w.get('horse_age')) for w in wins_data]
    ages = [a for a in ages if a is not None]
    
    # Ağırlıkları topla
    weights = [extract_weight(w.get('horse_weight')) for w in wins_data]
    weights = [w for w in weights if w is not None]
    
    # Handicap weights
    handicap_weights = []
    for w in wins_data:
        hw = w.get('handicap_weight')
        if hw and hw != '':
            try:
                handicap_weights.append(float(str(hw).replace(',', '.')))
            except:
                pass
    
    # Start numbers
    start_numbers = []
    for w in wins_data:
        sn = w.get('start_no')
        if sn and sn != '':
            try:
                start_numbers.append(int(sn))
            except:
                pass
    
    # Jockey, Trainer, Owner sayıları
    jockey_counter = Counter()
    trainer_counter = Counter()
    owner_counter = Counter()
    equipment_counter = Counter()
    
    for win in wins_data:
        jockey = win.get('jockey_name')
        jockey_id = win.get('jockey_id')
        if jockey:
            jockey_counter[(jockey, jockey_id)] += 1
        
        trainer = win.get('trainer_name')
        trainer_id = win.get('trainer_id')
        if trainer:
            trainer_counter[(trainer, trainer_id)] += 1
        
        owner = win.get('owner_name')
        owner_id = win.get('owner_id')
        if owner:
            owner_counter[(owner, owner_id)] += 1
        
        equipment = win.get('horse_equipment')
        if equipment and equipment.strip():
            # Tüm ekipmanı kaydet
            equipment_counter[equipment.strip()] += 1
    
    # Ana/Baba istatistikleri
    father_counter = Counter()
    mother_counter = Counter()
    
    for win in wins_data:
        father = win.get('horse_father_name')
        father_id = win.get('horse_father_id')
        if father:
            father_counter[(father, father_id)] += 1
        
        mother = win.get('horse_mother_name')
        mother_id = win.get('horse_mother_id')
        if mother:
            mother_counter[(mother, mother_id)] += 1
    
    # En çok kullanılanları al
    top_jockey = jockey_counter.most_common(1)[0] if jockey_counter else ((None, None), 0)
    top_trainer = trainer_counter.most_common(1)[0] if trainer_counter else ((None, None), 0)
    top_owner = owner_counter.most_common(1)[0] if owner_counter else ((None, None), 0)
    top_father = father_counter.most_common(1)[0] if father_counter else ((None, None), 0)
    top_mother = mother_counter.most_common(1)[0] if mother_counter else ((None, None), 0)
    top_equipment = equipment_counter.most_common(1)[0] if equipment_counter else (("", 0))
    
    # Ortalama yaş formatı oluştur
    avg_age = round(statistics.mean(ages), 1) if ages else 0
    age_years = int(avg_age)
    age_format = f"{age_years}y d  a"  # Genel format
    
    # Track type ve distance ayır
    track_type = track_distance.split('_')[0] if '_' in track_distance else "Bilinmiyor"
    distance = track_distance.split('_')[1].replace('m', '') if '_' in track_distance else 0
    
    # Ödül ortalaması
    prizes = []
    for w in wins_data:
        p = w.get('prize_1')
        if p:
            try:
                prizes.append(float(str(p).replace('.', '').replace(',', '.')))
            except:
                pass
    
    avg_prize = int(statistics.mean(prizes)) if prizes else 0
    
    # Ganyan ortalaması
    ganyans = []
    for w in wins_data:
        g = w.get('ganyan')
        if g and g != 'N/A':
            try:
                ganyans.append(float(str(g).replace(',', '.')))
            except:
                pass
    
    # AGF ortalaması
    agfs = []
    for w in wins_data:
        a = w.get('agf')
        if a and a not in ['N/A', '-', '']:
            try:
                # % işaretini kaldır
                agf_val = str(a).replace('%', '').strip()
                agfs.append(float(agf_val.replace(',', '.')))
            except:
                pass
    
    # Time analizi (örnek: "1.37.97" -> saniyeye çevir)
    times_in_seconds = []
    for w in wins_data:
        t = w.get('time')
        if t and t != 'N/A':
            try:
                # "1.37.97" formatı -> dakika.saniye.salise
                parts = str(t).split('.')
                if len(parts) >= 2:
                    minutes = int(parts[0]) if parts[0] else 0
                    seconds = int(parts[1]) if parts[1] else 0
                    centiseconds = int(parts[2]) if len(parts) > 2 and parts[2] else 0
                    total_seconds = minutes * 60 + seconds + centiseconds / 100
                    times_in_seconds.append(total_seconds)
            except:
                pass
    
    # Fark analizi (en çok görülen)
    fark_counter = Counter()
    for w in wins_data:
        f = w.get('fark')
        if f and f.strip():
            fark_counter[f.strip()] += 1
    
    # KGS (Koşmadığı Gün Sayısı) ortalaması
    kgs_values = []
    for w in wins_data:
        k = w.get('kgs')
        if k and k not in ['N/A', '-', '']:
            try:
                kgs_values.append(int(str(k)))
            except:
                pass
    
    # İdman verileri analizi
    # İdman mesafeleri: 200m, 400m, 600m, 800m, 1000m, 1200m, 1400m
    idman_distances = ['200m', '400m', '600m', '800m', '1000m', '1200m', '1400m']
    idman_averages = {}
    idman_counts = {}
    
    for distance_key in idman_distances:
        times_for_distance = []
        
        for w in wins_data:
            last_idman = w.get('last_idman')
            if last_idman and distance_key in last_idman:
                time_value = last_idman.get(distance_key)
                if time_value and time_value.strip() and time_value != '-':
                    # "0.44.20" formatındaki süreyi saniyeye çevir
                    try:
                        parts = time_value.split('.')
                        if len(parts) >= 2:
                            minutes = int(parts[0]) if parts[0] else 0
                            seconds = int(parts[1]) if parts[1] else 0
                            centiseconds = int(parts[2]) if len(parts) > 2 and parts[2] else 0
                            total_seconds = minutes * 60 + seconds + centiseconds / 100
                            
                            # İdman pistiyle yarış pistini karşılaştır ve normalize et
                            idman_city = last_idman.get('İ. Hip.')  # İdman hipodromu (şehir)
                            idman_track = last_idman.get('Pist')  # İdman pist tipi
                            race_city = w.get('city')  # Yarış şehri
                            race_track = w.get('track_type')  # Yarış pist tipi
                            
                            # Farklı pistteyse normalize et
                            normalized_time = normalize_idman_time(
                                total_seconds, 
                                idman_city, 
                                idman_track, 
                                race_city, 
                                race_track
                            )
                            
                            times_for_distance.append(normalized_time)
                    except:
                        pass
        
        # Ortalama hesapla
        if times_for_distance:
            avg_seconds = statistics.mean(times_for_distance)
            minutes = int(avg_seconds // 60)
            seconds = int(avg_seconds % 60)
            centiseconds = int((avg_seconds % 1) * 100)
            idman_averages[distance_key] = f"{minutes}.{seconds:02d}.{centiseconds:02d}"
            idman_counts[distance_key] = len(times_for_distance)
        else:
            idman_averages[distance_key] = ""
            idman_counts[distance_key] = 0
    
    # Ortalama time'ı formata geri çevir
    avg_time = "N/A"
    if times_in_seconds:
        avg_total = statistics.mean(times_in_seconds)
        minutes = int(avg_total // 60)
        seconds = int(avg_total % 60)
        centiseconds = int((avg_total % 1) * 100)
        avg_time = f"{minutes}.{seconds:02d}.{centiseconds:02d}"
    
    # Dream Horse profili - normal at formatında
    dream_profile = {
        "race_id": "DREAM",
        "race_date": "IDEAL_PROFILE",
        "race_number": 0,
        "finish_position": "1",
        "race_category": wins_data[0].get('race_category', category_name),
        "main_category": category_name,
        "age_group": wins_data[0].get('age_group', 'Bilinmiyor'),
        "prize_1": str(avg_prize),
        "prize_2": str(int(avg_prize * 0.4)) if avg_prize else "0",
        "prize_3": str(int(avg_prize * 0.2)) if avg_prize else "0",
        "prize_4": str(int(avg_prize * 0.1)) if avg_prize else "0",
        "prize_5": str(int(avg_prize * 0.05)) if avg_prize else "0",
        "horse_id": "DREAM",
        "horse_name": f"DREAM HORSE ({len(wins_data)} wins analyzed)",
        "horse_age": age_format,
        "horse_weight": str(round(statistics.mean(weights), 1)) if weights else "0",
        "horse_equipment": top_equipment[0][0] if top_equipment[0][0] else "",
        "horse_father_id": top_father[0][1] if top_father[0][1] else None,
        "horse_mother_id": top_mother[0][1] if top_mother[0][1] else None,
        "horse_father_name": top_father[0][0] if top_father[0][0] else None,
        "horse_mother_name": top_mother[0][0] if top_mother[0][0] else None,
        "jockey_id": top_jockey[0][1] if top_jockey[0][1] else None,
        "jockey_name": top_jockey[0][0] if top_jockey[0][0] else None,
        "trainer_id": top_trainer[0][1] if top_trainer[0][1] else None,
        "trainer_name": top_trainer[0][0] if top_trainer[0][0] else None,
        "owner_id": top_owner[0][1] if top_owner[0][1] else None,
        "owner_name": top_owner[0][0] if top_owner[0][0] else None,
        "track_type": track_type,
        "distance": int(distance) if distance else 0,
        "city": city_name,
        "start_no": str(int(round(statistics.mean(start_numbers)))) if start_numbers else "0",
        "handicap_weight": str(round(statistics.mean(handicap_weights), 1)) if handicap_weights else "",
        "ganyan": str(round(statistics.mean(ganyans), 2)) if ganyans else "N/A",
        "agf": f"%{int(round(statistics.mean(agfs)))}" if agfs else "N/A",
        "kgs": str(int(round(statistics.mean(kgs_values)))) if kgs_values else "0",
        "last_6_races": "N/A",  # Dream horse için geçerli değil
        "time": avg_time,
        "fark": fark_counter.most_common(1)[0][0] if fark_counter else "N/A",
        "idman_200m": idman_averages.get('200m', ''),
        "idman_400m": idman_averages.get('400m', ''),
        "idman_600m": idman_averages.get('600m', ''),
        "idman_800m": idman_averages.get('800m', ''),
        "idman_1000m": idman_averages.get('1000m', ''),
        "idman_1200m": idman_averages.get('1200m', ''),
        "idman_1400m": idman_averages.get('1400m', ''),
        "_metadata": {
            "total_wins_analyzed": len(wins_data),
            "jockey_win_count": top_jockey[1] if top_jockey[1] else 0,
            "trainer_win_count": top_trainer[1] if top_trainer[1] else 0,
            "owner_win_count": top_owner[1] if top_owner[1] else 0,
            "father_win_count": top_father[1] if top_father[1] else 0,
            "mother_win_count": top_mother[1] if top_mother[1] else 0,
            "equipment_usage_count": top_equipment[1] if top_equipment[1] else 0,
            "average_age": round(statistics.mean(ages), 2) if ages else None,
            "average_weight": round(statistics.mean(weights), 2) if weights else None,
            "average_handicap": round(statistics.mean(handicap_weights), 2) if handicap_weights else None,
            "idman_data_counts": {
                "200m": idman_counts.get('200m', 0),
                "400m": idman_counts.get('400m', 0),
                "600m": idman_counts.get('600m', 0),
                "800m": idman_counts.get('800m', 0),
                "1000m": idman_counts.get('1000m', 0),
                "1200m": idman_counts.get('1200m', 0),
                "1400m": idman_counts.get('1400m', 0)
            }
        }
    }
    
    return dream_profile

def process_stats_directory():
    """
    Stats klasöründeki tüm kategori/şehir/pist kombinasyonları için dream horse profili oluşturur.
    """
    stats_dir = Path("E:\\data\\stats")
    dream_dir = stats_dir / "dream_horse"
    dream_dir.mkdir(parents=True, exist_ok=True)
    
    print("Dream Horse profilleri oluşturuluyor...")
    print("=" * 80)
    
    total_profiles = 0
    
    # Tüm kategori klasörlerini tara
    for category_folder in stats_dir.iterdir():
        if not category_folder.is_dir() or category_folder.name in ['dream_horse', 'OVERALL_STATISTICS.json']:
            continue
        
        category_name = category_folder.name
        category_dream_dir = dream_dir / category_name
        category_dream_dir.mkdir(parents=True, exist_ok=True)
        
        # Tüm şehir klasörlerini tara
        for city_folder in category_folder.iterdir():
            if not city_folder.is_dir() or city_folder.name == 'CATEGORY_SUMMARY.json':
                continue
            
            city_name = city_folder.name
            city_dream_dir = category_dream_dir / city_name
            city_dream_dir.mkdir(parents=True, exist_ok=True)
            
            # Tüm breed klasörlerini tara (İngiliz, Arap, Diğer)
            for breed_folder in city_folder.iterdir():
                if not breed_folder.is_dir():
                    continue
                
                breed_name = breed_folder.name
                breed_dream_dir = city_dream_dir / breed_name
                breed_dream_dir.mkdir(parents=True, exist_ok=True)
                
                # Tüm track_distance JSON dosyalarını tara
                for json_file in breed_folder.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            wins_data = json.load(f)
                        
                        if not wins_data:
                            continue
                        
                        # Dream horse profili oluştur
                        dream_profile = create_dream_horse_profile(
                            wins_data, 
                            category_name, 
                            city_name, 
                            json_file.stem
                        )
                        
                        if dream_profile:
                            # Dream profili kaydet
                            dream_file = breed_dream_dir / json_file.name
                            with open(dream_file, 'w', encoding='utf-8') as f:
                                json.dump(dream_profile, f, ensure_ascii=False, indent=2)
                            
                            total_profiles += 1
                            
                            if total_profiles % 50 == 0:
                                print(f"İşlendi: {total_profiles} profil")
                    
                    except Exception as e:
                        print(f"Hata ({json_file}): {e}")
                        continue
        
        print(f"✓ {category_name}: Dream profilleri oluşturuldu")
    
    print("=" * 80)
    print(f"Toplam {total_profiles} dream horse profili oluşturuldu!")
    print(f"Dream horse profilleri: E:\\data\\stats\\dream_horse\\")

if __name__ == "__main__":
    process_stats_directory()
