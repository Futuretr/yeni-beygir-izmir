"""
At Kalitesi Sıralama Analizi - Average Handicap
Her koşu türü için tüm şehir ve mesafelerdeki average_handicap ortalamalarını hesaplar
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
import statistics

def find_all_json_files(race_type_path: Path) -> List[Path]:
    """Bir koşu türü klasöründeki tüm JSON dosyalarını bulur"""
    json_files = []
    for root, dirs, files in os.walk(race_type_path):
        for file in files:
            if file.endswith('.json'):
                json_files.append(Path(root) / file)
    return json_files

def extract_average_handicap(json_file: Path) -> float:
    """JSON dosyasından _metadata içindeki average_handicap değerini çıkarır"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            metadata = data.get('_metadata', {})
            avg_h = metadata.get('average_handicap', None)
            if avg_h is not None and avg_h != '':
                # String olabilir, float'a çevir
                return float(avg_h)
    except Exception as e:
        print(f"  ⚠ Hata ({json_file.name}): {e}")
    return None

def analyze_race_type(race_type_path: Path) -> Dict:
    """Bir koşu türünün tüm verilerini analiz eder"""
    race_type_name = race_type_path.name
    
    # Tüm JSON dosyalarını bul
    json_files = find_all_json_files(race_type_path)
    
    # Average handicap değerlerini topla
    average_handicaps = []
    files_processed = 0
    files_with_data = 0
    
    for json_file in json_files:
        files_processed += 1
        avg_h = extract_average_handicap(json_file)
        if avg_h is not None:
            average_handicaps.append(avg_h)
            files_with_data += 1
    
    # İstatistikleri hesapla
    result = {
        'race_type': race_type_name,
        'total_files': files_processed,
        'files_with_data': files_with_data,
        'average_handicaps': average_handicaps,
        'average': None,
        'median': None,
        'min': None,
        'max': None,
        'std_dev': None
    }
    
    if average_handicaps:
        result['average'] = statistics.mean(average_handicaps)
        result['median'] = statistics.median(average_handicaps)
        result['min'] = min(average_handicaps)
        result['max'] = max(average_handicaps)
        if len(average_handicaps) > 1:
            result['std_dev'] = statistics.stdev(average_handicaps)
    
    return result

def main():
    base_path = Path(r"E:\data\stats\dream_horse")
    
    if not base_path.exists():
        print(f"❌ Klasör bulunamadı: {base_path}")
        return
    
    print("="*80)
    print("AT KALİTESİ SIRALAMASI ANALİZİ - AVERAGE HANDICAP")
    print("Average Handicap Ortalamaları - Tüm Şehir ve Mesafeler")
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
            print(f"  📈 Ortalama: {result['average']:.2f}")
        else:
            print(f"  ⚠ Veri bulunamadı")
        print()
    
    # Sonuçları ortalamaya göre sırala (yüksekten düşüğe)
    sorted_results = sorted(
        [r for r in all_results if r['average'] is not None],
        key=lambda x: x['average'],
        reverse=True
    )
    
    print("\n" + "="*80)
    print("SIRALANMIŞ SONUÇLAR (Yüksek Kalite → Düşük Kalite)")
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
    report_path = Path("average_handicap_analysis_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("AT KALİTESİ SIRALAMASI - DETAYLI RAPOR (AVERAGE HANDICAP)\n")
        f.write("Average Handicap Analizi\n")
        f.write("="*80 + "\n\n")
        
        for rank, result in enumerate(sorted_results, 1):
            f.write(f"\n{'='*60}\n")
            f.write(f"Sıra #{rank}: {result['race_type']}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Toplam Dosya: {result['total_files']}\n")
            f.write(f"Veri İçeren Dosya: {result['files_with_data']}\n")
            f.write(f"\nİSTATİSTİKLER:\n")
            f.write(f"  Ortalama (Mean):     {result['average']:.2f} kg\n")
            f.write(f"  Ortanca (Median):    {result['median']:.2f} kg\n")
            f.write(f"  Minimum:             {result['min']:.2f} kg\n")
            f.write(f"  Maksimum:            {result['max']:.2f} kg\n")
            if result['std_dev'] is not None:
                f.write(f"  Std. Sapma:          {result['std_dev']:.2f} kg\n")
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
    json_report_path = Path("average_handicap_analysis_report.json")
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'sorted_results': sorted_results,
            'all_results': [
                {k: v for k, v in r.items() if k != 'average_handicaps'}
                for r in all_results
            ]
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON rapor kaydedildi: {json_report_path}")
    print()

if __name__ == "__main__":
    main()
