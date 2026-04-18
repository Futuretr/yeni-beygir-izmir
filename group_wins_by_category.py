import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def load_idman_for_horse(horse_id):
    """
    Belirli bir atın idman dosyasını yükler (lazy loading).
    Klasör yapısı: horse_id // 100 * 100 (örn: 55712 → 055700 klasörü)
    """
    idman_dir = Path("E:\\data\\idman")
    
    # Klasör ismini hesapla: (horse_id // 100) * 100, 6 haneye tamamla
    folder_id = (int(horse_id) // 100) * 100
    folder_name = str(folder_id).zfill(6)
    horse_folder = idman_dir / folder_name
    
    if not horse_folder.exists():
        return []
    
    # JSON dosyasını bul
    json_file = horse_folder / f"{horse_id}.json"
    
    if not json_file.exists():
        return []
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            idman_data = json.load(f)
            return idman_data.get('idman_records', [])
    except:
        return []

def get_last_idman_before_race(idman_records, race_date_str):
    """
    Yarış tarihinden önce olan en son idmanı bulur.
    Tarih formatları: "DD.MM.YYYY" veya "YYYY-MM-DDTHH:MM:SSZ"
    """
    if not idman_records or not race_date_str:
        return None
    
    try:
        # Yarış tarihini parse et - farklı formatları dene
        if 'T' in race_date_str:
            # ISO format: "2024-01-27T00:00:00Z"
            race_date = datetime.fromisoformat(race_date_str.replace('Z', '+00:00'))
            # Timezone'u kaldır (naive datetime yap)
            race_date = race_date.replace(tzinfo=None)
        else:
            # DD.MM.YYYY format
            race_date = datetime.strptime(race_date_str, "%d.%m.%Y")
    except:
        return None
    
    # Yarıştan önceki idmanları filtrele ve tarihe göre sırala
    valid_idmans = []
    
    for idman in idman_records:
        # Tarih field'ını bul - encoding sorunları olabilir
        idman_date_str = idman.get('İ. Tarihi') or idman.get('Ä°. Tarihi') or idman.get('I. Tarihi')
        if not idman_date_str:
            continue
        
        try:
            idman_date = datetime.strptime(idman_date_str, "%d.%m.%Y")
            
            # Yarış tarihinden ÖNCE olan idmanları al
            if idman_date < race_date:
                valid_idmans.append((idman_date, idman))
        except:
            continue
    
    # En son idmanı bul (tarihe göre sırala, en yeni olanı al)
    if valid_idmans:
        valid_idmans.sort(key=lambda x: x[0], reverse=True)
        return valid_idmans[0][1]  # En son idmanı döndür
    
    return None

def load_program_data():
    """
    Program dosyalarını yükler ve race_id + horse_id bazında bir lookup dictionary oluşturur.
    """
    program_dir = Path("E:\\data\\program")
    program_lookup = {}
    
    print("Program dosyaları yükleniyor...")
    
    # Tüm şehir klasörlerini tara
    for city_folder in program_dir.iterdir():
        if not city_folder.is_dir():
            continue
        
        # Yıl klasörlerini tara
        for year_folder in city_folder.iterdir():
            if not year_folder.is_dir():
                continue
            
            # Ay dosyalarını tara
            for month_file in year_folder.glob("*.json"):
                try:
                    with open(month_file, 'r', encoding='utf-8') as f:
                        month_data = json.load(f)
                    
                    # Tüm yarışları tara
                    for day, day_data in month_data.items():
                        if isinstance(day_data, dict):
                            for race_num, races in day_data.items():
                                if isinstance(races, list):
                                    for race in races:
                                        race_id = race.get('race_id')
                                        horse_id = race.get('horse_id')
                                        
                                        if race_id and horse_id:
                                            key = f"{race_id}_{horse_id}"
                                            program_lookup[key] = {
                                                'horse_father_id': race.get('horse_father_id'),
                                                'horse_mother_id': race.get('horse_mother_id'),
                                                'horse_father_name': race.get('horse_father_name'),
                                                'horse_mother_name': race.get('horse_mother_name')
                                            }
                except Exception as e:
                    continue
    
    print(f"Program verisi yüklendi: {len(program_lookup)} at kaydı")
    return program_lookup


def group_wins_by_category(horses_dir="E:\\data\\horses"):
    """
    Horses klasöründeki tüm atları tarar ve 1. gelen yarışları
    race_category'lerine göre gruplar.
    """
    
    # Program verilerini yükle
    program_lookup = load_program_data()
    
    # İdman verileri lazy loading ile yüklenecek (ihtiyaç duyulduğunda)
    
    def fix_encoding(text):
        """
        Bozuk Türkçe karakterleri düzelt
        """
        if not text:
            return text
        
        replacements = {
            'Ĺž': 'Ş', 'ĹŸ': 'ş',
            'Äą': 'ı', 'Ä°': 'İ',
            'Ä': 'ğ', 'Ä': 'Ğ',
            'Ã¼': 'ü', 'Ã': 'Ü',
            'Ã§': 'ç', 'Ã': 'Ç',
            'Ã¶': 'ö', 'Ã': 'Ö'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def extract_main_category(race_category):
        """
        Race category'den ana grubu çıkarır.
        Örnek: "ŞARTLI 1/DHÖW" -> "ŞARTLI 1"
               "Handikap 15/DHÖW /H2" -> "Handikap 15"
               "SATIŞ 1/DHÖW" -> "SATIŞ 1"
               "Kısa Vade 24/DHÖ" -> "Kısa Vade 24"
        """
        if not race_category:
            return "Bilinmiyor"
        
        # Önce karakterleri düzelt
        race_category = fix_encoding(race_category)
        
        # İlk / işaretine kadar al veya tüm stringi al
        main_part = race_category.split('/')[0].strip()
        
        # Kelimelere ayır
        words = main_part.split()
        if len(words) == 0:
            return race_category
        elif len(words) == 1:
            return words[0]
        elif len(words) == 2:
            return ' '.join(words[:2])
        else:
            # 3 veya daha fazla kelime var
            # "Kısa Vade Handikap 24" -> "Kısa Vade 24" gibi durumlar için
            # Eğer son kelime sayıysa ve "Handikap" gibi bir kelime varsa
            last_word = words[-1]
            if last_word.replace('-', '').isdigit():
                # Son kelime sayı, ortada "Handikap" gibi kelime olabilir
                # "Kısa Vade Handikap 24" -> ilk iki kelime + son kelime
                if len(words) == 4 and words[2].lower() in ['handikap', 'handicap']:
                    return f"{words[0]} {words[1]} {words[3]}"
                # "ŞARTLI 1" gibi zaten 2 kelime
                elif words[1].replace('-', '').isdigit():
                    return ' '.join(words[:2])
                # Diğer durumlar için son sayıyı da al
                else:
                    return ' '.join(words[:3])
            # "Kısa Vade Handikap" gibi 3 kelime ama sayı yok
            elif words[2].replace('-', '').isdigit():
                return ' '.join(words[:3])
            else:
                return ' '.join(words[:2])
    
    # Kategorilere göre gruplamak için dictionary
    category_groups = defaultdict(list)
    
    # İstatistikler
    total_horses = 0
    total_wins = 0
    
    # Horses dizinini tara
    horses_path = Path(horses_dir)
    
    if not horses_path.exists():
        print(f"Hata: {horses_dir} dizini bulunamadı!")
        return
    
    print(f"Tarama başlıyor: {horses_dir}")
    print("-" * 80)
    
    # Tüm klasörleri listele (daha hızlı)
    all_folders = [f for f in horses_path.iterdir() if f.is_dir()]
    total_folders = len(all_folders)
    
    print(f"Toplam {total_folders} at klasörü bulundu. Tarama başlıyor...\n")
    
    # Her at klasörünü tara
    for idx, horse_folder in enumerate(all_folders, 1):
        # Her 1000 klasörde bir ilerleme göster
        if idx % 1000 == 0:
            print(f"İlerleme: {idx}/{total_folders} klasör tarandı ({idx*100//total_folders}%)")
        
        # JSON dosyasını bul
        json_files = list(horse_folder.glob("*.json"))
        
        if not json_files:
            continue
            
        json_file = json_files[0]  # İlk JSON dosyasını al
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                horse_data = json.load(f)
            
            total_horses += 1
            horse_name = horse_data.get('horse_name', 'Bilinmiyor')
            horse_id = horse_data.get('horse_id', 'Bilinmiyor')
            
            # Sadece finish_position = "1" olan yarışları filtrele
            races = horse_data.get('races', [])
            
            for race in races:
                if race.get('finish_position') == "1":
                    total_wins += 1
                    race_category = race.get('race_category', 'Bilinmiyor')
                    
                    # Ana kategoriyi çıkar (örn: "ŞARTLI 1", "Handikap 15")
                    main_category = extract_main_category(race_category)
                    
                    # Program dosyasından ana/baba bilgilerini al
                    race_id = race.get('race_id')
                    lookup_key = f"{race_id}_{horse_id}"
                    parent_info = program_lookup.get(lookup_key, {})
                    
                    # Yarıştan önceki son idmanı bul
                    race_date = race.get('race_date')
                    horse_idman_records = load_idman_for_horse(horse_id)  # Lazy loading
                    last_idman = get_last_idman_before_race(horse_idman_records, race_date)
                    
                    # Kategori grubuna ekle - TÜM BİLGİLERLE
                    category_groups[main_category].append({
                        'race_id': race_id,
                        'race_date': race.get('race_date'),
                        'race_number': race.get('race_number'),
                        'finish_position': race.get('finish_position'),
                        'race_category': race_category,  # Orijinal kategori bilgisi
                        'main_category': main_category,   # Gruplandırılmış kategori
                        'age_group': race.get('age_group'),
                        'prize_1': race.get('prize_1'),
                        'prize_2': race.get('prize_2'),
                        'prize_3': race.get('prize_3'),
                        'prize_4': race.get('prize_4'),
                        'prize_5': race.get('prize_5'),
                        'horse_id': horse_id,
                        'horse_name': horse_name,
                        'horse_age': race.get('horse_age'),
                        'horse_weight': race.get('horse_weight'),
                        'horse_equipment': race.get('horse_equipment'),
                        'horse_father_id': parent_info.get('horse_father_id'),
                        'horse_mother_id': parent_info.get('horse_mother_id'),
                        'horse_father_name': parent_info.get('horse_father_name'),
                        'horse_mother_name': parent_info.get('horse_mother_name'),
                        'jockey_id': race.get('jockey_id'),
                        'jockey_name': race.get('jockey_name'),
                        'trainer_id': race.get('trainer_id'),
                        'trainer_name': race.get('trainer_name'),
                        'owner_id': race.get('owner_id'),
                        'owner_name': race.get('owner_name'),
                        'track_type': race.get('track_type'),
                        'distance': race.get('distance'),
                        'city': race.get('city'),
                        'start_no': race.get('start_no'),
                        'handicap_weight': race.get('handicap_weight'),
                        'ganyan': race.get('ganyan'),
                        'agf': race.get('agf'),
                        'kgs': race.get('kgs'),
                        'last_6_races': race.get('last_6_races'),
                        'time': race.get('time'),
                        'fark': race.get('fark'),
                        'last_idman': last_idman  # Yarıştan önceki son idman
                    })
            
        except Exception as e:
            print(f"Hata ({json_file.name}): {e}")
            continue
    
    # Sonuçları yazdır
    print(f"\nToplam taranan at: {total_horses}")
    print(f"Toplam 1. gelen yarış: {total_wins}")
    print(f"Toplam kategori sayısı: {len(category_groups)}")
    print("\n" + "=" * 80)
    
    # Her kategori için özet bilgi
    print("\nKATEGORİ ÖZETİ:")
    print("-" * 80)
    
    # Kategorileri galibiyet sayısına göre sırala
    sorted_categories = sorted(category_groups.items(), 
                               key=lambda x: len(x[1]), 
                               reverse=True)
    
    for category, wins in sorted_categories:
        print(f"{category}: {len(wins)} galibiyet")
    
    # Ana stats klasörünü oluştur
    base_stats_dir = Path("E:\\data\\stats")
    base_stats_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 80)
    print("Kategori klasörleri oluşturuluyor ve gruplandırılıyor...")
    print("-" * 80)
    
    # Her kategori için ayrı klasör oluştur ve JSON kaydet
    for category, wins in category_groups.items():
        # Kategori adını klasör adı olarak kullan (geçersiz karakterleri temizle)
        # Önce karakterleri düzelt
        clean_category = fix_encoding(category)
        safe_category_name = clean_category.replace('/', '-').replace('\\', '-').replace(':', '-')
        
        # Kategori klasörünü oluştur
        category_dir = base_stats_dir / safe_category_name
        category_dir.mkdir(parents=True, exist_ok=True)
        
        # Şehirlere göre grupla
        city_groups = defaultdict(list)
        for win in wins:
            city = fix_encoding(win.get('city', 'Bilinmiyor'))
            city_groups[city].append(win)
        
        # Her şehir için
        for city, city_wins in city_groups.items():
            # Şehir klasörünü oluştur
            safe_city_name = city.replace('/', '-').replace('\\', '-').replace(':', '-')
            city_dir = category_dir / safe_city_name
            city_dir.mkdir(parents=True, exist_ok=True)
            
            # İngiliz/Arap ayrımı yap
            breed_groups = defaultdict(list)
            for win in city_wins:
                age_group = win.get('age_group', '')
                # İngiliz mi Arap mı belirle
                if 'İngiliz' in age_group or 'ingiliz' in age_group.lower():
                    breed = 'İngiliz'
                elif 'Arap' in age_group or 'arap' in age_group.lower():
                    breed = 'Arap'
                else:
                    breed = 'Diğer'
                breed_groups[breed].append(win)
            
            # Her breed için
            for breed, breed_wins in breed_groups.items():
                # Breed klasörünü oluştur
                breed_dir = city_dir / breed
                breed_dir.mkdir(parents=True, exist_ok=True)
                
                # Track type ve distance kombinasyonlarına göre grupla
                track_distance_groups = defaultdict(list)
                for win in breed_wins:
                    track_type = fix_encoding(win.get('track_type', 'Bilinmiyor'))
                    distance = win.get('distance', 'Bilinmiyor')
                    key = f"{track_type}_{distance}m"
                    track_distance_groups[key].append(win)
                
                # Her track_type + distance kombinasyonu için JSON dosyası oluştur
                for key, group_wins in track_distance_groups.items():
                    safe_filename = key.replace('/', '-').replace('\\', '-').replace(':', '-')
                    wins_file = breed_dir / f"{safe_filename}.json"
                    
                    with open(wins_file, 'w', encoding='utf-8') as f:
                        json.dump(group_wins, f, ensure_ascii=False, indent=2)
        
        # Kategori özeti dosyasını kaydet
        summary_file = category_dir / "CATEGORY_SUMMARY.json"
        summary = {
            'category': clean_category,
            'total_wins': len(wins),
            'unique_horses': len(set(w['horse_id'] for w in wins)),
            'cities': {
                city: {
                    'total_wins': len(city_wins),
                    'breeds': {}
                }
                for city, city_wins in city_groups.items()
            }
        }
        
        # Her şehir için breed bilgilerini ekle
        for city, city_wins in city_groups.items():
            breed_info = {}
            for win in city_wins:
                age_group = win.get('age_group', '')
                if 'İngiliz' in age_group or 'ingiliz' in age_group.lower():
                    breed = 'İngiliz'
                elif 'Arap' in age_group or 'arap' in age_group.lower():
                    breed = 'Arap'
                else:
                    breed = 'Diğer'
                
                if breed not in breed_info:
                    breed_info[breed] = {'count': 0, 'track_distance_combinations': set()}
                breed_info[breed]['count'] += 1
                
                track_type = fix_encoding(win.get('track_type', 'Bilinmiyor'))
                distance = win.get('distance', 'Bilinmiyor')
                breed_info[breed]['track_distance_combinations'].add(f"{track_type}_{distance}m")
            
            # Set'leri list'e çevir
            for breed in breed_info:
                breed_info[breed]['track_distance_combinations'] = list(breed_info[breed]['track_distance_combinations'])
            
            summary['cities'][city]['breeds'] = breed_info
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"✓ {safe_category_name}: {len(wins)} galibiyet - {len(city_groups)} şehir")
    
    # Genel özet dosyası
    overall_stats_file = base_stats_dir / "OVERALL_STATISTICS.json"
    overall_stats = {
        'scan_date': '2026-02-01',
        'total_horses_scanned': total_horses,
        'total_wins': total_wins,
        'total_categories': len(category_groups),
        'categories': sorted(list(category_groups.keys()))
    }
    
    with open(overall_stats_file, 'w', encoding='utf-8') as f:
        json.dump(overall_stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Genel istatistikler '{overall_stats_file}' dosyasına kaydedildi.")
    
    return category_groups


if __name__ == "__main__":
    # Fonksiyonu çalıştır
    category_groups = group_wins_by_category()
    
    # Örnek: Belirli bir kategorideki galibiyetleri göster
    print("\n" + "=" * 80)
    print("ÖRNEK: 'SATIŞ 1/DHÖW' kategorisindeki galibiyetler:")
    print("-" * 80)
    
    if category_groups and "SATIŞ 1/DHÖW" in category_groups:
        satis_wins = category_groups["SATIŞ 1/DHÖW"]
        print(f"Toplam {len(satis_wins)} galibiyet bulundu.\n")
        
        # İlk 5 galibiyeti göster
        for i, win in enumerate(satis_wins[:5], 1):
            print(f"{i}. {win['horse_name']} - {win['race_date'][:10]} - {win['city']} - {win['distance']}m")
