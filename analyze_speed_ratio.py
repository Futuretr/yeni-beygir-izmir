"""
At Kalitesi Sıralama Analizi - Hız Oranı (Distance / Time)
Her koşu türü için tüm şehir ve mesafelerdeki hız oranlarının ortalamalarını hesaplar
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
    Format: "0.24.15" → 0 dakika 24.15 saniye → 24.15 saniye
    Format: "2.06.48" → 2 dakika 6.48 saniye → 126.48 saniye
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
        
        # Toplam saniye
        total_seconds = (minutes * 60) + seconds + (centiseconds / 100)
        return total_seconds
    except Exception as e:
        return None

def find_all_json_files(race_type_path: Path) -> List[Path]:
    """Bir koşu türü klasöründeki tüm JSON dosyalarını bulur"""
    json_files = []
    for root, dirs, files in os.walk(race_type_path):
        for file in files:
            if file.endswith('.json'):
                json_files.append(Path(root) / file)
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
            
            # Time'ı saniyeye çevir
            time_seconds = time_to_seconds(time_str)
            if time_seconds is None or time_seconds <= 0:
                return None
            
            # Distance / Time = Hız (metre/saniye)
            speed_ratio = float(distance) / time_seconds
            return speed_ratio
            
    except Exception as e:
        print(f"  ⚠ Hata ({json_file.name}): {e}")
    return None

def analyze_race_type(race_type_path: Path) -> Dict:
    """Bir koşu türünün tüm verilerini analiz eder"""
    race_type_name = race_type_path.name
    
    # Tüm JSON dosyalarını bul
    json_files = find_all_json_files(race_type_path)
    
    # Speed ratio değerlerini topla
    speed_ratios = []
    files_processed = 0
    files_with_data = 0
    
    for json_file in json_files:
        files_processed += 1
        ratio = extract_speed_ratio(json_file)
        if ratio is not None:
            speed_ratios.append(ratio)
            files_with_data += 1
    
    # İstatistikleri hesapla
    result = {
        'race_type': race_type_name,
        'total_files': files_processed,
        'files_with_data': files_with_data,
        'speed_ratios': speed_ratios,
        'average': None,
        'median': None,
        'min': None,
        'max': None,
        'std_dev': None
    }
    
    if speed_ratios:
        result['average'] = statistics.mean(speed_ratios)
        result['median'] = statistics.median(speed_ratios)
        result['min'] = min(speed_ratios)
        result['max'] = max(speed_ratios)
        if len(speed_ratios) > 1:
            result['std_dev'] = statistics.stdev(speed_ratios)
    
    return result

def main():
    base_path = Path(r"E:\data\stats\dream_horse")
    
    if not base_path.exists():
        print(f"❌ Klasör bulunamadı: {base_path}")
        return
    
    print("="*80)
    print("AT KALİTESİ SIRALAMASI ANALİZİ - HIZ ORANI")
    print("Distance / Time Ortalamaları - Tüm Şehir ve Mesafeler")
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
        
        if result['files_with_data'] > 0:
            print(f"  ✓ {result['files_with_data']}/{result['total_files']} dosya analiz edildi")
            print(f"  📈 Ortalama: {result['average']:.2f} m/s")
        else:
            print(f"  ⚠ Veri bulunamadı")
        print()
    
    # Sonuçları ortalamaya göre sırala (yüksekten düşüğe - daha hızlı at = daha kaliteli)
    sorted_results = sorted(
        [r for r in all_results if r['average'] is not None],
        key=lambda x: x['average'],
        reverse=True
    )
    
    print("\n" + "="*80)
    print("SIRALANMIŞ SONUÇLAR (Yüksek Hız → Düşük Hız)")
    print("="*80)
    print()
    print(f"{'Sıra':<6} {'Koşu Türü':<25} {'Ort.':<10} {'Min':<10} {'Max':<10} {'Dosya':<10}")
    print("-"*80)
    
    for rank, result in enumerate(sorted_results, 1):
        print(f"{rank:<6} {result['race_type']:<25} "
              f"{result['average']:<10.2f} "
              f"{result['min']:<10.2f} "
              f"{result['max']:<10.2f} "
              f"{result['files_with_data']:<10}")
    
    # Detaylı rapor dosyası oluştur
    report_path = Path("speed_ratio_analysis_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("AT KALİTESİ SIRALAMASI - DETAYLI RAPOR (HIZ ORANI)\n")
        f.write("Distance / Time Analizi (metre/saniye)\n")
        f.write("="*80 + "\n\n")
        
        for rank, result in enumerate(sorted_results, 1):
            f.write(f"\n{'='*60}\n")
            f.write(f"Sıra #{rank}: {result['race_type']}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Toplam Dosya: {result['total_files']}\n")
            f.write(f"Veri İçeren Dosya: {result['files_with_data']}\n")
            f.write(f"\nİSTATİSTİKLER:\n")
            f.write(f"  Ortalama (Mean):     {result['average']:.2f} m/s\n")
            f.write(f"  Ortanca (Median):    {result['median']:.2f} m/s\n")
            f.write(f"  Minimum:             {result['min']:.2f} m/s\n")
            f.write(f"  Maksimum:            {result['max']:.2f} m/s\n")
            if result['std_dev'] is not None:
                f.write(f"  Std. Sapma:          {result['std_dev']:.2f} m/s\n")
            f.write(f"\n")
        
        # Veri olmayan koşu türleri
        no_data_types = [r for r in all_results if r['average'] is None]
        if no_data_types:
            f.write(f"\n{'='*60}\n")
            f.write("VERİ BULUNMAYAN KOŞU TÜRLERİ:\n")
            f.write(f"{'='*60}\n")
            for result in no_data_types:
                f.write(f"  - {result['race_type']} ({result['total_files']} dosya tarandı)\n")
    
    print("\n" + "="*80)
    print(f"✅ Detaylı rapor kaydedildi: {report_path}")
    print("="*80)
    
    # JSON formatında da kaydet
    json_report_path = Path("speed_ratio_analysis_report.json")
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'sorted_results': sorted_results,
            'all_results': [
                {k: v for k, v in r.items() if k != 'speed_ratios'}
                for r in all_results
            ]
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON rapor kaydedildi: {json_report_path}")
    print()

if __name__ == "__main__":
    main()
