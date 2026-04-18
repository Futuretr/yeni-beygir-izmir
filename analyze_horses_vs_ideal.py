"""
Atları İdeal Dream Horse ile Karşılaştır
- Horse profiles'dan atların verilerini getirir
- Dream horse ideal zamanı ile karşılaştırır
- Zaman farklarını hesaplar
"""
import json
import sys
from pathlib import Path

# Windows terminal encoding sorunu için
if sys.platform == 'win32':
    import codecs
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

def time_to_seconds(time_str):
    """Convert time string like '2.18.15' to seconds"""
    if not time_str or time_str == "":
        return None
    try:
        parts = time_str.split('.')
        if len(parts) == 3:
            minutes = int(parts[0])
            seconds = int(parts[1])
            centiseconds = int(parts[2])
            return minutes * 60 + seconds + centiseconds / 100
        elif len(parts) == 2:
            seconds = int(parts[0])
            centiseconds = int(parts[1])
            return seconds + centiseconds / 100
        else:
            return float(time_str)
    except:
        return None

def seconds_to_time(seconds):
    """Convert seconds back to time string"""
    if seconds is None:
        return "N/A"
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes}.{int(remaining_seconds):02d}.{int((remaining_seconds % 1) * 100):02d}"

def normalize_category_name(category_input, dream_dir="E:/data/stats/dream_horse"):
    """Normalize and find the correct category folder name"""
    # Kullanıcı girişini normalize et
    normalized_input = category_input.strip()
    
    # Dream horse klasöründeki tüm kategorileri al
    dream_path = Path(dream_dir)
    if not dream_path.exists():
        return category_input
    
    # Mevcut kategorileri listele
    available_categories = [d.name for d in dream_path.iterdir() if d.is_dir()]
    
    # 1. Tam eşleşme ara (case-insensitive)
    for cat in available_categories:
        if cat.upper() == normalized_input.upper():
            return cat
    
    # 2. Kısmi eşleşme ara (boşlukları dikkate almadan)
    normalized_input_no_space = normalized_input.upper().replace(" ", "")
    for cat in available_categories:
        cat_normalized = cat.upper().replace(" ", "")
        if cat_normalized == normalized_input_no_space:
            return cat
    
    # 3. ASCII dönüşümü ile eşleşme (Türkçe karakter sorunları için)
    # Ş->S, İ->I, Ğ->G, Ü->U, Ö->O, Ç->C
    turkish_map = str.maketrans('ŞİĞÜÖÇşığüöç', 'SIGUOCsiguoc')
    normalized_ascii = normalized_input.upper().translate(turkish_map).replace(" ", "")
    
    for cat in available_categories:
        cat_ascii = cat.upper().translate(turkish_map).replace(" ", "")
        if cat_ascii == normalized_ascii:
            return cat
    
    # 4. ? karakterini Ş ile değiştir (Windows terminal sorunu)
    if '?' in normalized_input:
        fixed_input = normalized_input.replace('?', 'Ş').replace('?', 'ş')
        # Tekrar dene
        for cat in available_categories:
            if cat.upper() == fixed_input.upper():
                return cat
            if cat.upper().replace(" ", "") == fixed_input.upper().replace(" ", ""):
                return cat
    
    # 5. Benzer isimleri bul (başlangıç eşleşmesi)
    for cat in available_categories:
        if cat.upper().startswith(normalized_input.upper()) or normalized_input.upper().startswith(cat.upper()):
            return cat
    
    # Hiçbir eşleşme bulunamazsa orijinal değeri döndür
    return category_input

def find_similar_categories(category_input, dream_dir="E:/data/stats/dream_horse"):
    """Find similar category names to help user"""
    dream_path = Path(dream_dir)
    if not dream_path.exists():
        return []
    
    available = [d.name for d in dream_path.iterdir() if d.is_dir()]
    normalized_input = category_input.strip().upper()
    
    # Benzer kategorileri bul
    similar = []
    for cat in available:
        cat_upper = cat.upper()
        # İçeren veya içinde geçen
        if normalized_input in cat_upper or cat_upper in normalized_input:
            similar.append(cat)
        # İlk kelime eşleşmesi
        elif normalized_input.split()[0] in cat_upper or cat_upper.split()[0] in normalized_input:
            similar.append(cat)
    
    return similar[:5]  # En fazla 5 öneri

def normalize_text(text):
    """Normalize text for matching (handles Turkish chars and encoding issues)"""
    if not text:
        return text
    
    # ? karakterlerini Türkçe karakterlere çevir
    replacements = {
        '?': ['Ş', 'ş', 'İ', 'i', 'Ğ', 'ğ', 'Ü', 'ü', 'Ö', 'ö', 'Ç', 'ç']
    }
    
    # Türkçe karakterleri normalize et
    turkish_map = str.maketrans('ŞİĞÜÖÇşığüöç', 'SIGUOCsiguoc')
    return text.translate(turkish_map)

def find_matching_folder(input_name, parent_path, folder_type="folder"):
    """Find matching folder name from available options"""
    parent = Path(parent_path)
    if not parent.exists():
        return input_name
    
    available = [d.name for d in parent.iterdir() if d.is_dir()]
    if not available:
        return input_name
    
    # Tam eşleşme
    for item in available:
        if item.upper() == input_name.upper():
            return item
    
    # Normalize edilmiş eşleşme
    normalized_input = normalize_text(input_name.upper())
    for item in available:
        if normalize_text(item.upper()) == normalized_input:
            return item
    
    # Orijinal değeri döndür
    return input_name

def get_horse_profile(horse_id, profiles_dir="E:/data/horse_profiles"):
    """Get horse profile from JSON file"""
    profile_path = Path(profiles_dir) / f"{horse_id}.json"
    if not profile_path.exists():
        return None
    
    with open(profile_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_horse_time_for_conditions(profile, distance, track_type, city):
    """Get horse's average time for specific distance/track/city"""
    if not profile:
        return None
    
    distance_stats = profile.get('distance_stats', {})
    distance_data = distance_stats.get(str(distance), {})
    track_data = distance_data.get(track_type, {})
    city_data = track_data.get(city, {})
    
    return city_data.get('avg_time')

def get_dream_horse_time(race_category, city, horse_type, track_type, distance, 
                         dream_dir="E:/data/stats/dream_horse"):
    """Get ideal time from dream horse JSON"""
    # Kategori adını normalize et
    normalized_category = normalize_category_name(race_category, dream_dir)
    
    # Şehir, at türü ve pist türünü de normalize et
    base_path = Path(dream_dir) / normalized_category
    normalized_city = find_matching_folder(city, base_path, "city") if base_path.exists() else city
    
    city_path = base_path / normalized_city
    normalized_horse_type = find_matching_folder(horse_type, city_path, "horse_type") if city_path.exists() else horse_type
    
    # Pist türü ve mesafe ile eşleşen dosyayı bul
    horse_type_path = city_path / normalized_horse_type
    dream_path = None
    
    if horse_type_path.exists():
        # Önce direkt dosya adıyla dene
        direct_path = horse_type_path / f"{track_type}_{distance}m.json"
        if direct_path.exists():
            dream_path = direct_path
        else:
            # Dosya bulunamazsa, tüm dosyaları tara ve normalize ederek eşleştir
            json_files = list(horse_type_path.glob("*.json"))
            normalized_track = normalize_text(track_type.upper())
            
            for f in json_files:
                parts = f.stem.split('_')
                if len(parts) == 2:
                    file_track = parts[0]
                    file_dist = parts[1].replace('m', '')
                    
                    # Mesafe ve pist türü eşleşmesi
                    if (str(distance) == file_dist and 
                        (file_track.upper() == track_type.upper() or 
                         normalize_text(file_track.upper()) == normalized_track)):
                        dream_path = f
                        break
    
    if dream_path is None or not dream_path.exists():
        # Alternatif şehir, pist, mesafe kombinasyonlarını kontrol et
        alternatives = {
            "cities": [],
            "track_types": [],
            "distances": []
        }
        
        base_path = Path(dream_dir) / normalized_category
        if base_path.exists():
            # Mevcut şehirleri bul
            alternatives["cities"] = [d.name for d in base_path.iterdir() if d.is_dir()]
            
            # Eğer şehir varsa, o şehirdeki at türlerini ve pist türlerini bul
            city_path = base_path / normalized_city
            if city_path.exists():
                horse_type_path = city_path / normalized_horse_type
                if horse_type_path.exists():
                    # Bu at türünde mevcut pist türü ve mesafeleri bul
                    json_files = list(horse_type_path.glob("*.json"))
                    for f in json_files:
                        # Dosya adı formatı: Kum_1400m.json
                        parts = f.stem.split('_')
                        if len(parts) == 2:
                            track = parts[0]
                            dist = parts[1].replace('m', '')
                            if track not in alternatives["track_types"]:
                                alternatives["track_types"].append(track)
                            if dist not in alternatives["distances"]:
                                alternatives["distances"].append(dist)
        
        return None, None, normalized_category, alternatives
    
    with open(dream_path, 'r', encoding='utf-8') as f:
        dream_data = json.load(f)
    
    time_str = dream_data.get('time', '')
    time_sec = time_to_seconds(time_str)
    
    return time_sec, dream_data, normalized_category, None

def main():
    print("="*80)
    print("AT PERFORMANS ANALİZİ - İDEAL ZAMAN KARŞILAŞTIRMASI")
    print("="*80)
    
    # 1. At ID'lerini al
    print("\n1️⃣ AT ID'LERİNİ GİRİN")
    print("Örnek: 107299,105393,104328")
    horse_ids_input = input("At ID'leri (virgülle ayırın): ").strip()
    horse_ids = [h.strip() for h in horse_ids_input.split(',')]
    
    # 2. Mesafe bilgisi
    distance = int(input("\n2️⃣ MESAFE (metre): ").strip())
    
    # 3. Pist türü
    print("\n3️⃣ PİST TÜRÜ")
    print("Örnek: Kum, Çim, Sentetik")
    track_type = input("Pist türü: ").strip()
    
    # 4. Şehir
    print("\n4️⃣ ŞEHİR")
    print("Örnek: Antalya, Istanbul, Izmir")
    city = input("Şehir: ").strip()
    
    # 5. Yarış kategorisi
    print("\n5️⃣ YARIŞ KATEGORİSİ")
    print("Örnek: Handikap 15, Şartlı 3, Maiden")
    race_category = input("Yarış kategorisi: ").strip()
    
    # 6. At türü
    print("\n6️⃣ AT TÜRÜ")
    print("Örnek: İngiliz, Arap")
    horse_type = input("At türü: ").strip()
    
    print("\n" + "="*80)
    print("VERİLER GETİRİLİYOR...")
    print("="*80)
    
    # Dream horse ideal zamanını al
    ideal_time_sec, dream_data, normalized_category, alternatives = get_dream_horse_time(
        race_category, city, horse_type, track_type, distance
    )
    
    if ideal_time_sec is None:
        print(f"\n❌ İdeal zaman bulunamadı!")
        print(f"Aranan kategori: '{race_category}' → Normalize edildi: '{normalized_category}'")
        print(f"Aranan dosya: E:/data/stats/dream_horse/{normalized_category}/{city}/{horse_type}/{track_type}_{distance}m.json")
        
        # Mevcut alternatifleri göster
        if alternatives:
            if alternatives["cities"]:
                print(f"\n📍 Bu kategoride mevcut şehirler:")
                for c in sorted(alternatives["cities"]):
                    print(f"   - {c}")
            
            if alternatives["track_types"]:
                print(f"\n🏁 '{city}/{horse_type}' için mevcut pist türleri:")
                for t in sorted(alternatives["track_types"]):
                    print(f"   - {t}")
            
            if alternatives["distances"]:
                print(f"\n📏 '{city}/{horse_type}' için mevcut mesafeler:")
                for d in sorted(alternatives["distances"], key=lambda x: int(x)):
                    print(f"   - {d}m")
        
        # Benzer kategorileri öner
        similar = find_similar_categories(race_category)
        if similar:
            print(f"\n💡 Benzer kategoriler:")
            for cat in similar:
                print(f"   - {cat}")
        
        return
    
    print(f"\n✅ İdeal Dream Horse Zamanı: {seconds_to_time(ideal_time_sec)} ({ideal_time_sec:.2f} saniye)")
    print(f"   Kategori: '{race_category}' → '{normalized_category}'")
    print(f"   Dosya: {normalized_category}/{city}/{horse_type}/{track_type}_{distance}m.json")
    
    # Her at için analiz
    results = {
        "analysis_info": {
            "race_category": race_category,
            "city": city,
            "horse_type": horse_type,
            "track_type": track_type,
            "distance": distance,
            "ideal_time_seconds": ideal_time_sec,
            "ideal_time_formatted": seconds_to_time(ideal_time_sec)
        },
        "horses": []
    }
    
    print("\n" + "="*80)
    print("AT ANALİZLERİ")
    print("="*80)
    
    for horse_id in horse_ids:
        print(f"\n🐎 At ID: {horse_id}")
        
        # Profile'ı al
        profile = get_horse_profile(horse_id)
        if not profile:
            print(f"   ❌ Profil bulunamadı!")
            results["horses"].append({
                "horse_id": horse_id,
                "error": "Profile not found"
            })
            continue
        
        horse_name = profile.get('horse_id', horse_id)
        total_races = profile.get('career_summary', {}).get('total_races', 0)
        avg_finish = profile.get('career_summary', {}).get('avg_finish_position', 0)
        
        print(f"   Toplam Yarış: {total_races}")
        print(f"   Ortalama Derece: {avg_finish}")
        
        # Bu koşullar için süreyi al
        horse_time_sec = get_horse_time_for_conditions(profile, distance, track_type, city)
        
        if horse_time_sec is None:
            print(f"   ❌ Bu koşullar için veri yok ({city} - {track_type} - {distance}m)")
            results["horses"].append({
                "horse_id": horse_id,
                "total_races": total_races,
                "avg_finish": avg_finish,
                "error": f"No data for {city}/{track_type}/{distance}m"
            })
            continue
        
        # Farkı hesapla (pozitif = ideal zamandan yavaş, negatif = ideal zamandan hızlı)
        time_diff = horse_time_sec - ideal_time_sec
        
        print(f"   ✅ Bu Koşullardaki Süresi: {seconds_to_time(horse_time_sec)} ({horse_time_sec:.2f} saniye)")
        
        if time_diff > 0:
            print(f"   📊 Fark: +{time_diff:.2f} saniye (İDEALDEN YAVAŞ)")
        elif time_diff < 0:
            print(f"   📊 Fark: {time_diff:.2f} saniye (İDEALDEN HIZLI) ⭐")
        else:
            print(f"   📊 Fark: 0.00 saniye (İDEAL ZAMAN)")
        
        # Distance stats detayını al
        distance_stats = profile.get('distance_stats', {}).get(str(distance), {}).get(track_type, {}).get(city, {})
        
        results["horses"].append({
            "horse_id": horse_id,
            "total_races": total_races,
            "avg_finish": avg_finish,
            "condition_stats": {
                "races": distance_stats.get('races', 0),
                "avg_finish": distance_stats.get('avg_finish'),
                "avg_time_seconds": horse_time_sec,
                "avg_time_formatted": seconds_to_time(horse_time_sec)
            },
            "comparison": {
                "time_difference_seconds": round(time_diff, 2),
                "time_difference_formatted": f"{'+' if time_diff > 0 else ''}{time_diff:.2f}s",
                "faster_than_ideal": time_diff < 0,
                "percentage_diff": round((time_diff / ideal_time_sec) * 100, 2)
            }
        })
    
    # JSON'a kaydet
    output_file = "horse_vs_ideal_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print(f"✅ ANALİZ TAMAMLANDI!")
    print(f"📄 Sonuçlar kaydedildi: {output_file}")
    print("="*80)
    
    # Özet tablo
    print("\n📊 ÖZET TABLO:")
    print("-"*80)
    print(f"{'At ID':<12} {'Yarış':<8} {'Ort.Derece':<12} {'Süre':<12} {'Fark':<15}")
    print("-"*80)
    
    for h in results["horses"]:
        if "error" in h:
            print(f"{h['horse_id']:<12} {h.get('total_races', 0):<8} {h.get('avg_finish', 0):<12.2f} {'N/A':<12} {'Veri Yok':<15}")
        else:
            horse_time = h['condition_stats']['avg_time_formatted']
            diff = h['comparison']['time_difference_formatted']
            marker = "⭐ HIZLI" if h['comparison']['faster_than_ideal'] else "YAVAŞ"
            print(f"{h['horse_id']:<12} {h['total_races']:<8} {h['avg_finish']:<12.2f} {horse_time:<12} {diff:<10} {marker}")
    
    print("-"*80)

if __name__ == "__main__":
    main()
