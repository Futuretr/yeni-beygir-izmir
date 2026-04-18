"""
At Kalitesi Sıralama Analizi - Pist Türüne Göre Hız Oranı
Her koşu türü için pist türlerine göre (Sentetik, Kum, Çim) ayrı ayrı hız oranlarını hesaplar
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
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

def find_all_json_files(race_type_path: Path) -> List[tuple]:
    """Bir koşu türü klasöründeki tüm JSON dosyalarını ve pist türlerini bulur"""
    json_files = []
    for root, dirs, files in os.walk(race_type_path):
        for file in files:
            if file.endswith('.json'):
                track_type = get_track_type_from_filename(file)
                if track_type:
                    json_files.append((Path(root) / file, track_type))
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
    """Bir koşu türünün pist türüne göre verilerini analiz eder"""
    race_type_name = race_type_path.name
    
    # Tüm JSON dosyalarını ve pist türlerini bul
    json_files = find_all_json_files(race_type_path)
    
    # Pist türüne göre hız oranlarını topla
    track_data = {
        'Sentetik': [],
        'Kum': [],
        'Çim': []
    }
    
    for json_file, track_type in json_files:
        ratio = extract_speed_ratio(json_file)
        if ratio is not None:
            track_data[track_type].append(ratio)
    
    # Her pist türü için istatistikleri hesapla
    result = {
        'race_type': race_type_name,
        'total_files': len(json_files),
        'tracks': {}
    }
    
    for track_type in ['Sentetik', 'Kum', 'Çim']:
        speeds = track_data[track_type]
        
        track_result = {
            'count': len(speeds),
            'average': None,
            'median': None,
            'min': None,
            'max': None,
            'std_dev': None
        }
        
        if speeds:
            track_result['average'] = statistics.mean(speeds)
            track_result['median'] = statistics.median(speeds)
            track_result['min'] = min(speeds)
            track_result['max'] = max(speeds)
            if len(speeds) > 1:
                track_result['std_dev'] = statistics.stdev(speeds)
        
        result['tracks'][track_type] = track_result
    
    return result

def main():
    base_path = Path(r"E:\data\stats\dream_horse")
    
    if not base_path.exists():
        print(f"❌ Klasör bulunamadı: {base_path}")
        return
    
    print("="*80)
    print("AT KALİTESİ SIRALAMASI ANALİZİ - PİST TÜRÜNE GÖRE HIZ ORANI")
    print("Distance / Time Ortalamaları - Pist Türlerine Göre Ayrılmış")
    print("="*80)
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
            track_info = result['tracks'][track_type]
            if track_info['count'] > 0:
                print(f"    {track_type:10} → {track_info['count']:3} dosya, Ort: {track_info['average']:.2f} m/s")
            else:
                print(f"    {track_type:10} → Veri yok")
        print()
    
    # Her pist türü için ayrı sıralamalar
    for track_type in ['Sentetik', 'Kum', 'Çim']:
        print("\n" + "="*80)
        print(f"SIRALI SONUÇLAR - {track_type.upper()} PİSTLER (Yüksek Hız → Düşük Hız)")
        print("="*80)
        print()
        
        # Bu pist türü için veri olan koşu türlerini filtrele ve sırala
        sorted_results = sorted(
            [(r['race_type'], r['tracks'][track_type]) for r in all_results 
             if r['tracks'][track_type]['average'] is not None],
            key=lambda x: x[1]['average'],
            reverse=True
        )
        
        if sorted_results:
            print(f"{'Sıra':<6} {'Koşu Türü':<25} {'Ort.':<10} {'Min':<10} {'Max':<10} {'Dosya':<10}")
            print("-"*80)
            
            for rank, (race_type_name, track_data) in enumerate(sorted_results, 1):
                print(f"{rank:<6} {race_type_name:<25} "
                      f"{track_data['average']:<10.2f} "
                      f"{track_data['min']:<10.2f} "
                      f"{track_data['max']:<10.2f} "
                      f"{track_data['count']:<10}")
        else:
            print(f"  ⚠ {track_type} pist için veri bulunamadı")
    
    # Detaylı rapor dosyası oluştur
    report_path = Path("speed_by_track_analysis_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("AT KALİTESİ SIRALAMASI - PİST TÜRÜNE GÖRE HIZ ORANI\n")
        f.write("Distance / Time Analizi (metre/saniye)\n")
        f.write("="*80 + "\n\n")
        
        for track_type in ['Sentetik', 'Kum', 'Çim']:
            f.write(f"\n{'='*80}\n")
            f.write(f"{track_type.upper()} PİSTLER - SIRALI SONUÇLAR\n")
            f.write(f"{'='*80}\n\n")
            
            sorted_results = sorted(
                [(r['race_type'], r['tracks'][track_type]) for r in all_results 
                 if r['tracks'][track_type]['average'] is not None],
                key=lambda x: x[1]['average'],
                reverse=True
            )
            
            for rank, (race_type_name, track_data) in enumerate(sorted_results, 1):
                f.write(f"\n{'-'*60}\n")
                f.write(f"Sıra #{rank}: {race_type_name}\n")
                f.write(f"{'-'*60}\n")
                f.write(f"Dosya Sayısı: {track_data['count']}\n")
                f.write(f"Ortalama (Mean):     {track_data['average']:.2f} m/s\n")
                f.write(f"Ortanca (Median):    {track_data['median']:.2f} m/s\n")
                f.write(f"Minimum:             {track_data['min']:.2f} m/s\n")
                f.write(f"Maksimum:            {track_data['max']:.2f} m/s\n")
                if track_data['std_dev'] is not None:
                    f.write(f"Std. Sapma:          {track_data['std_dev']:.2f} m/s\n")
    
    print("\n" + "="*80)
    print(f"✅ Detaylı rapor kaydedildi: {report_path}")
    print("="*80)
    
    # JSON formatında da kaydet
    json_report_path = Path("speed_by_track_analysis_report.json")
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'results': all_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON rapor kaydedildi: {json_report_path}")
    print()

if __name__ == "__main__":
    main()
