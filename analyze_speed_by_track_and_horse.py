"""
At Kalitesi Sıralama Analizi - Pist ve At Türüne Göre Hız Oranı
Her koşu türü için pist türü (Sentetik, Kum, Çim) ve at türüne (İngiliz, Arap) göre hız oranlarını hesaplar
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import statistics

def time_to_seconds(time_str: str) -> Optional[float]:
    """
    Time string'ini saniyeye çevirir
    Format: "1.18.19" → 1 dakika 18.19 saniye → 78.19 saniye
    """
    try:
        if not time_str or time_str == '':
            return None
        
        parts = time_str.split('.')
        if len(parts) != 3:
            return None
        
        minutes = int(parts[0])
        seconds = int(parts[1])
        centiseconds = int(parts[2])
        
        total_seconds = (minutes * 60) + seconds + (centiseconds / 100)
        return total_seconds
    except Exception as e:
        return None

def get_track_type_from_filename(filename: str) -> Optional[str]:
    """
    Dosya adından pist türünü çıkarır
    Örnek: "Sentetik_1300m.json" -> "Sentetik"
    """
    if filename.startswith('Sentetik_'):
        return 'Sentetik'
    elif filename.startswith('Kum_'):
        return 'Kum'
    elif filename.startswith('Çim_'):
        return 'Çim'
    return None

def get_horse_type_from_path(file_path: Path) -> Optional[str]:
    """
    Dosya yolundan at türünü çıkarır
    Örnek: "...\\Istanbul\\İngiliz\\Sentetik_1300m.json" -> "İngiliz"
    """
    parts = file_path.parts
    for part in parts:
        if part in ['İngiliz', 'Arap']:
            return part
    return None

def find_all_json_files(race_type_path: Path) -> List[Tuple[Path, str, str]]:
    """Bir koşu türü klasöründeki tüm JSON dosyalarını, pist türlerini ve at türlerini bulur"""
    json_files = []
    for root, dirs, files in os.walk(race_type_path):
        for file in files:
            if file.endswith('.json'):
                file_path = Path(root) / file
                track_type = get_track_type_from_filename(file)
                horse_type = get_horse_type_from_path(file_path)
                
                if track_type and horse_type:
                    json_files.append((file_path, track_type, horse_type))
    return json_files

def extract_speed_ratio(json_file: Path) -> Optional[float]:
    """JSON dosyasından distance / time oranını hesaplar"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            time_str = data.get('time', '')
            distance = data.get('distance', None)
            
            if not time_str or not distance:
                return None
            
            time_seconds = time_to_seconds(time_str)
            if time_seconds is None or time_seconds <= 0:
                return None
            
            speed_ratio = float(distance) / time_seconds
            return speed_ratio
            
    except Exception as e:
        return None

def analyze_race_type(race_type_path: Path) -> Dict:
    """Bir koşu türünün pist ve at türüne göre verilerini analiz eder"""
    race_type_name = race_type_path.name
    
    # Tüm JSON dosyalarını, pist türlerini ve at türlerini bul
    json_files = find_all_json_files(race_type_path)
    
    # Pist ve at türüne göre hız oranlarını topla
    combined_data = {}
    for track_type in ['Sentetik', 'Kum', 'Çim']:
        for horse_type in ['İngiliz', 'Arap']:
            key = f"{track_type}-{horse_type}"
            combined_data[key] = []
    
    for json_file, track_type, horse_type in json_files:
        ratio = extract_speed_ratio(json_file)
        if ratio is not None:
            key = f"{track_type}-{horse_type}"
            combined_data[key].append(ratio)
    
    # Her kombinasyon için istatistikleri hesapla
    result = {
        'race_type': race_type_name,
        'total_files': len(json_files),
        'combinations': {}
    }
    
    for key, speeds in combined_data.items():
        combo_result = {
            'count': len(speeds),
            'average': None,
            'median': None,
            'min': None,
            'max': None,
            'std_dev': None
        }
        
        if speeds:
            combo_result['average'] = statistics.mean(speeds)
            combo_result['median'] = statistics.median(speeds)
            combo_result['min'] = min(speeds)
            combo_result['max'] = max(speeds)
            if len(speeds) > 1:
                combo_result['std_dev'] = statistics.stdev(speeds)
        
        result['combinations'][key] = combo_result
    
    return result

def main():
    base_path = Path(r"E:\data\stats\dream_horse")
    
    if not base_path.exists():
        print(f"❌ Klasör bulunamadı: {base_path}")
        return
    
    print("="*90)
    print("AT KALİTESİ SIRALAMASI ANALİZİ - PİST VE AT TÜRÜNE GÖRE HIZ ORANI")
    print("Distance / Time Ortalamaları - Pist ve At Türlerine Göre Ayrılmış")
    print("="*90)
    print()
    
    # Tüm koşu türlerini bul
    race_types = [d for d in base_path.iterdir() if d.is_dir()]
    race_types.sort()
    
    print(f"📊 Toplam {len(race_types)} koşu türü bulundu\n")
    
    all_results = []
    
    # Her koşu türünü analiz et
    for i, race_type_path in enumerate(race_types, 1):
        print(f"[{i}/{len(race_types)}] Analiz ediliyor: {race_type_path.name}")
        result = analyze_race_type(race_type_path)
        all_results.append(result)
        
        print(f"  📁 Toplam {result['total_files']} dosya")
        
        for track_type in ['Sentetik', 'Kum', 'Çim']:
            for horse_type in ['İngiliz', 'Arap']:
                key = f"{track_type}-{horse_type}"
                combo_info = result['combinations'][key]
                
                if combo_info['count'] > 0:
                    print(f"    {key:20} → {combo_info['count']:3} dosya, Ort: {combo_info['average']:.2f} m/s")
        print()
    
    # Her kombinasyon için ayrı sıralamalar
    for track_type in ['Sentetik', 'Kum', 'Çim']:
        for horse_type in ['İngiliz', 'Arap']:
            key = f"{track_type}-{horse_type}"
            
            print("\n" + "="*90)
            print(f"SIRALI SONUÇLAR - {track_type.upper()} PİSTLER / {horse_type.upper()} (Yüksek Hız → Düşük Hız)")
            print("="*90)
            print()
            
            # Bu kombinasyon için veri olan koşu türlerini filtrele ve sırala
            sorted_results = sorted(
                [(r['race_type'], r['combinations'][key]) for r in all_results 
                 if r['combinations'][key]['average'] is not None],
                key=lambda x: x[1]['average'],
                reverse=True
            )
            
            if sorted_results:
                print(f"{'Sıra':<6} {'Koşu Türü':<25} {'Ort.':<10} {'Min':<10} {'Max':<10} {'Dosya':<10}")
                print("-"*90)
                
                for rank, (race_type_name, combo_data) in enumerate(sorted_results, 1):
                    print(f"{rank:<6} {race_type_name:<25} "
                          f"{combo_data['average']:<10.2f} "
                          f"{combo_data['min']:<10.2f} "
                          f"{combo_data['max']:<10.2f} "
                          f"{combo_data['count']:<10}")
            else:
                print(f"  ⚠ {key} kombinasyonu için veri bulunamadı")
    
    # Detaylı rapor dosyası oluştur
    report_path = Path("speed_by_track_and_horse_analysis_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*90 + "\n")
        f.write("AT KALİTESİ SIRALAMASI - PİST VE AT TÜRÜNE GÖRE HIZ ORANI\n")
        f.write("Distance / Time Analizi (metre/saniye)\n")
        f.write("="*90 + "\n\n")
        
        for track_type in ['Sentetik', 'Kum', 'Çim']:
            for horse_type in ['İngiliz', 'Arap']:
                key = f"{track_type}-{horse_type}"
                
                f.write(f"\n{'='*90}\n")
                f.write(f"{track_type.upper()} PİSTLER / {horse_type.upper()} - SIRALI SONUÇLAR\n")
                f.write(f"{'='*90}\n\n")
                
                sorted_results = sorted(
                    [(r['race_type'], r['combinations'][key]) for r in all_results 
                     if r['combinations'][key]['average'] is not None],
                    key=lambda x: x[1]['average'],
                    reverse=True
                )
                
                for rank, (race_type_name, combo_data) in enumerate(sorted_results, 1):
                    f.write(f"\n{'-'*60}\n")
                    f.write(f"Sıra #{rank}: {race_type_name}\n")
                    f.write(f"{'-'*60}\n")
                    f.write(f"Dosya Sayısı: {combo_data['count']}\n")
                    f.write(f"Ortalama (Mean):     {combo_data['average']:.2f} m/s\n")
                    f.write(f"Ortanca (Median):    {combo_data['median']:.2f} m/s\n")
                    f.write(f"Minimum:             {combo_data['min']:.2f} m/s\n")
                    f.write(f"Maksimum:            {combo_data['max']:.2f} m/s\n")
                    if combo_data['std_dev'] is not None:
                        f.write(f"Std. Sapma:          {combo_data['std_dev']:.2f} m/s\n")
    
    print("\n" + "="*90)
    print(f"✅ Detaylı rapor kaydedildi: {report_path}")
    print("="*90)
    
    # JSON formatında da kaydet
    json_report_path = Path("speed_by_track_and_horse_analysis_report.json")
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'results': all_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON rapor kaydedildi: {json_report_path}")
    print()

if __name__ == "__main__":
    main()
