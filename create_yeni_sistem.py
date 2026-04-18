"""
Yeni Sistem Data Birleştirici
Tüm kaynaklardan (sonuclar, program, idman, stats) veri toplayarak
temiz bir yapıya dönüştürür ve Şehir+Pist+Mesafe+Kategori bazında gruplar.
"""

import json
import os
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import glob

# Veri dizinleri
SONUCLAR_DIR = r"E:\data\sonuclar"
PROGRAM_DIR = r"E:\data\program"
IDMAN_DIR = r"E:\data\idman"
HORSES_DIR = r"E:\data\horses"
STATS_DIR = r"E:\data\stats"
OUTPUT_DIR = r"E:\data\yeni_sistem"

# Global cache'ler
HORSE_CACHE = {}
IDMAN_CACHE = {}


def load_horse_data(horse_id, race_id):
    """Bir at için belirli bir yarış için time ve kgs bilgilerini yükle (cache ile)"""
    global HORSE_CACHE
    
    try:
        # Cache'de var mı kontrol et
        if horse_id not in HORSE_CACHE:
            # Klasör yapısı: E:\data\horses\{horse_id}\{horse_id}.json
            horse_file = os.path.join(HORSES_DIR, str(horse_id), f"{horse_id}.json")
            
            if not os.path.exists(horse_file):
                HORSE_CACHE[horse_id] = None
                return None, None
            
            with open(horse_file, 'r', encoding='utf-8') as f:
                HORSE_CACHE[horse_id] = json.load(f)
        
        data = HORSE_CACHE[horse_id]
        if not data:
            return None, None
        
        # Bu yarış için time ve kgs bul
        races = data.get("races", [])
        for race in races:
            if race.get("race_id") == race_id:
                time_value = race.get("time")
                kgs_value = race.get("kgs")
                return time_value, kgs_value
        
        # Eğer bu yarış yoksa, en son yarışın verilerini kullan
        if races:
            latest = races[-1]
            return latest.get("time"), latest.get("kgs")
        
        return None, None
    except Exception as e:
        return None, None


def load_idman_for_horse(horse_id, race_date):
    """Bir at için yarış tarihinden önce en yakın idman bilgisini yükle (cache ile)"""
    global IDMAN_CACHE
    
    try:
        # Cache'de var mı kontrol et
        if horse_id not in IDMAN_CACHE:
            # Klasör yapısı: E:\data\idman\{horse_id}\{horse_id}.json
            idman_file = os.path.join(IDMAN_DIR, str(horse_id), f"{horse_id}.json")
            
            if not os.path.exists(idman_file):
                IDMAN_CACHE[horse_id] = None
                return None
            
            with open(idman_file, 'r', encoding='utf-8') as f:
                IDMAN_CACHE[horse_id] = json.load(f)
        
        data = IDMAN_CACHE[horse_id]
        if not data:
            return None
        
        idman_records = data.get("idman_records", [])
        if not idman_records:
            return None
        
        # Yarış tarihini parse et
        try:
            race_dt = datetime.strptime(race_date, "%Y-%m-%d")
        except:
            return None
        
        # Yarıştan önce olan idmanları filtrele ve en yakını bul
        valid_idmans = []
        for idman in idman_records:
            idman_date_str = idman.get("İ. Tarihi", "")
            if not idman_date_str:
                continue
            
            try:
                # Tarihi parse et (format: "22.06.2023")
                idman_dt = datetime.strptime(idman_date_str, "%d.%m.%Y")
                
                # Sadece yarıştan önce olanları al
                if idman_dt < race_dt:
                    valid_idmans.append({
                        "date": idman_dt,
                        "data": idman
                    })
            except:
                continue
        
        # En yakın idmanı döndür
        if valid_idmans:
            # Tarihe göre sırala, en yakını al
            valid_idmans.sort(key=lambda x: x["date"], reverse=True)
            return valid_idmans[0]["data"]
        
        return None
    except Exception as e:
        return None


def parse_ganyan(ganyan_str):
    """Ganyan değerini temizle ve float'a çevir"""
    if not ganyan_str:
        return None
    try:
        return float(ganyan_str.replace(',', '.'))
    except:
        return None


def parse_agf(agf_str):
    """AGF yüzdesini temizle ve int'e çevir"""
    if not agf_str:
        return None
    try:
        return int(agf_str.replace('%', ''))
    except:
        return None


def extract_horse_type(age_group):
    """At türünü belirle: Arap veya İngiliz"""
    if not age_group:
        return "Unknown"
    
    age_group_lower = age_group.lower()
    if 'arap' in age_group_lower:
        return "Arap"
    elif 'ingiliz' in age_group_lower or 'İngiliz' in age_group:
        return "Ingiliz"
    else:
        return "Unknown"


def load_idman_data():
    """İdman verilerini yükle - horse_id bazlı dictionary"""
    print("İdman verileri yükleniyor...")
    idman_data = {}
    
    idman_files = glob.glob(os.path.join(IDMAN_DIR, "**/*.json"), recursive=True)
    
    for file_path in idman_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Dosya formatına göre parse et
                if isinstance(data, dict):
                    if 'value' in data:
                        # value içinde liste var
                        for item in data.get('value', []):
                            if 'horse_id' in item and 'error' not in item:
                                horse_id = item['horse_id']
                                if horse_id not in idman_data:
                                    idman_data[horse_id] = item
                    else:
                        # Direkt dict
                        for horse_id_str, item in data.items():
                            if isinstance(item, dict) and 'error' not in item:
                                try:
                                    horse_id = int(horse_id_str)
                                    if horse_id not in idman_data:
                                        idman_data[horse_id] = item
                                except:
                                    pass
        except Exception as e:
            print(f"  Hata (idman): {file_path} - {e}")
    
    print(f"  {len(idman_data)} at için idman verisi yüklendi")
    return idman_data


def extract_race_time(idman_entry):
    """İdman verisinden race_time bilgisini çıkar"""
    if not idman_entry:
        return None, None
    
    # Çeşitli alan isimleri kontrol et
    for time_field in ['race_time', 'race_time_total', 'time', 'derece']:
        if time_field in idman_entry:
            return idman_entry[time_field], None
    
    return None, None


def extract_workout_info(idman_data):
    """İdman verisinden workout bilgilerini çıkar (400m, 600m, 800m, 1000m vb.)"""
    if not idman_data:
        return None, None
    
    workout_time = None
    workout_distance = None
    
    # 400m, 600m, 800m, 1000m, 1200m, 1400m gibi alanları kontrol et
    for distance in ['400m', '600m', '800m', '1000m', '1200m', '1400m']:
        if distance in idman_data and idman_data[distance]:
            workout_time = idman_data[distance]
            # Mesafeyi çıkar (örn: "400m" -> 400)
            workout_distance = int(distance.replace('m', ''))
            break
    
    return workout_time, workout_distance


def calculate_days_since_last_race(race_date_str, horse_last_race_date):
    """Son yarıştan geçen gün sayısını hesapla"""
    if not horse_last_race_date or not race_date_str:
        return None
    
    try:
        race_date = datetime.fromisoformat(race_date_str.replace('Z', '+00:00'))
        last_race = datetime.fromisoformat(horse_last_race_date.replace('Z', '+00:00'))
        delta = race_date - last_race
        return delta.days
    except:
        return None


def process_sonuclar():
    """Sonuçlar klasöründeki tüm verileri işle"""
    print("\nSonuçlar işleniyor...")
    
    all_races = []
    
    sonuc_files = glob.glob(os.path.join(SONUCLAR_DIR, "**/*.json"), recursive=True)
    total_files = len(sonuc_files)
    
    for idx, file_path in enumerate(sonuc_files, 1):
        if idx % 10 == 0:
            print(f"  İşleniyor: {idx}/{total_files} - Cache: {len(HORSE_CACHE)} horses, {len(IDMAN_CACHE)} idman")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Dosya yapısı: {"01": {"0": [race_data], "1": [race_data]}, ...}
            for day_key, day_races in data.items():
                for race_num_key, horses in day_races.items():
                    if not isinstance(horses, list) or len(horses) == 0:
                        continue
                    
                    for horse_entry in horses:
                        # Yeni formata dönüştür
                        horse_id = horse_entry.get("horse_id")
                        race_date = horse_entry.get("race_date", "").replace("T00:00:00Z", "")
                        race_id = horse_entry.get("race_id")
                        
                        race_record = {
                            "race_id": race_id,
                            "race_date": race_date,
                            "city": horse_entry.get("city"),
                            "track_type": horse_entry.get("track_type"),
                            "distance": horse_entry.get("distance"),
                            "race_category": horse_entry.get("race_category"),
                            "horse_type": extract_horse_type(horse_entry.get("age_group")),
                            "finish_position": horse_entry.get("finish_position"),
                            "horse_id": horse_id,
                            "horse_name": horse_entry.get("horse_name"),
                            "horse_weight": horse_entry.get("horse_weight"),
                            "ganyan": parse_ganyan(horse_entry.get("ganyan")),
                            "agf_percent": parse_agf(horse_entry.get("agf")),
                            "horse_age": horse_entry.get("horse_age"),
                            "horse_equipment": horse_entry.get("horse_equipment"),
                        }
                        
                        # Horse klasöründen time ve kgs bilgilerini al
                        if horse_id:
                            time_value, kgs_value = load_horse_data(horse_id, race_id)
                            race_record["race_time_total"] = time_value
                            
                            # kgs -> days_since_last_race
                            if kgs_value:
                                try:
                                    race_record["days_since_last_race"] = int(kgs_value)
                                except:
                                    race_record["days_since_last_race"] = None
                            else:
                                race_record["days_since_last_race"] = None
                            
                            # İdman bilgilerini al
                            idman_data = load_idman_for_horse(horse_id, race_date)
                            if idman_data:
                                # Workout time ve distance
                                workout_time, workout_distance = extract_workout_info(idman_data)
                                race_record["workout_time"] = workout_time
                                race_record["workout_distance"] = workout_distance
                                
                                # İdman detayları
                                race_record["idman_date"] = idman_data.get("İ. Tarihi")
                                race_record["idman_city"] = idman_data.get("İ. Hip.")
                                race_record["idman_track_type"] = idman_data.get("Pist")
                                race_record["idman_track_condition"] = idman_data.get("P.Dur")
                                race_record["idman_type"] = idman_data.get("İ. Türü")
                            else:
                                race_record["workout_time"] = None
                                race_record["workout_distance"] = None
                                race_record["idman_date"] = None
                                race_record["idman_city"] = None
                                race_record["idman_track_type"] = None
                                race_record["idman_track_condition"] = None
                                race_record["idman_type"] = None
                        else:
                            race_record["race_time_total"] = None
                            race_record["days_since_last_race"] = None
                            race_record["workout_time"] = None
                            race_record["workout_distance"] = None
                            race_record["idman_date"] = None
                            race_record["idman_city"] = None
                            race_record["idman_track_type"] = None
                            race_record["idman_track_condition"] = None
                            race_record["idman_type"] = None
                        
                        all_races.append(race_record)
        
        except Exception as e:
            print(f"  Hata: {file_path} - {e}")
    
    print(f"  Toplam {len(all_races)} yarış kaydı oluşturuldu")
    return all_races


def group_by_criteria(races):
    """
    Yarışları Şehir + Pist + Mesafe + Kategori + At Türü bazında grupla
    Grup anahtarı: "Şehir_PistTipi_Mesafe_Kategori_AtTürü"
    """
    print("\nVeriler gruplandırılıyor...")
    
    grouped = defaultdict(list)
    
    for race in races:
        city = race.get("city") or "Unknown"
        track = race.get("track_type") or "Unknown"
        distance = race.get("distance") or "Unknown"
        category = race.get("race_category") or "Unknown"
        horse_type = race.get("horse_type") or "Unknown"
        
        # Kategoriyi temizle (çok uzun kategorileri kısalt)
        category = category.split('/')[0].strip()
        
        # Grup anahtarı oluştur
        group_key = f"{city}_{track}_{distance}_{category}_{horse_type}"
        grouped[group_key].append(race)
    
    print(f"  {len(grouped)} farklı grup oluşturuldu")
    return grouped


def save_grouped_data(grouped_data):
    """Grupları ayrı dosyalara kaydet - Şehir/AtTürü/Kategori/Pist_Mesafe.json yapısında"""
    print("\nGruplar kaydediliyor...")
    
    # İstatistikler
    stats = {
        "created_at": datetime.now().isoformat(),
        "total_groups": len(grouped_data),
        "total_races": sum(len(races) for races in grouped_data.values()),
        "groups": []
    }
    
    for group_key, races in grouped_data.items():
        # Grup anahtarını parçala: Şehir_Pist_Mesafe_Kategori_AtTürü
        parts = group_key.split('_')
        city = parts[0] if len(parts) > 0 else "Unknown"
        track = parts[1] if len(parts) > 1 else "Unknown"
        distance = parts[2] if len(parts) > 2 else "Unknown"
        category = parts[3] if len(parts) > 3 else "Unknown"
        horse_type = parts[4] if len(parts) > 4 else "Unknown"
        
        # Klasör yapısı: Şehir/AtTürü/Kategori/
        category_dir = os.path.join(OUTPUT_DIR, city, horse_type, category)
        os.makedirs(category_dir, exist_ok=True)
        
        # Dosya adı: Pist_Mesafe.json
        group_filename = f"{track}_{distance}.json"
        group_filepath = os.path.join(category_dir, group_filename)
        
        # Sırala: tarih ve finish_position'a göre
        races_sorted = sorted(races, key=lambda x: (
            x.get("race_date") or "",
            int(x.get("finish_position")) if x.get("finish_position", "").isdigit() else 999
        ))
        
        # Kaydet
        with open(group_filepath, 'w', encoding='utf-8') as f:
            json.dump(races_sorted, f, ensure_ascii=False, indent=2)
        
        # İstatistik bilgisi ekle
        stats["groups"].append({
            "group_key": group_key,
            "city": city,
            "horse_type": horse_type,
            "category": category,
            "track_type": track,
            "distance": distance,
            "race_count": len(races),
            "file_path": f"{city}/{horse_type}/{category}/{group_filename}"
        })
    
    # Stats dosyasını kaydet
    stats_file = os.path.join(OUTPUT_DIR, "_GROUPS_SUMMARY.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"  {len(grouped_data)} grup dosyası oluşturuldu")
    print(f"  Özet dosya: _GROUPS_SUMMARY.json")


def main():
    """Ana işlem"""
    print("=" * 60)
    print("YENİ SİSTEM - VERİ BİRLEŞTİRME ve GRUPLAMA")
    print("=" * 60)
    
    # 1. Sonuçları işle ve temiz formata dönüştür
    all_races = process_sonuclar()
    
    if not all_races:
        print("\nHata: Hiç veri bulunamadı!")
        return
    
    # 2. Şehir + Pist + Mesafe + Kategori bazında grupla
    grouped_data = group_by_criteria(all_races)
    
    # 3. Grupları dosyalara kaydet
    save_grouped_data(grouped_data)
    
    print("\n" + "=" * 60)
    print("İŞLEM TAMAMLANDI!")
    print("=" * 60)
    print(f"Çıktı dizini: {OUTPUT_DIR}")
    print(f"Toplam grup sayısı: {len(grouped_data)}")
    print(f"Toplam yarış kaydı: {len(all_races)}")


if __name__ == "__main__":
    main()
