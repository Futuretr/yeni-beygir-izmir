"""
Gelişmiş At Yarışı Veri Toplama Sistemi
========================================
Bu sistem tüm yarış verilerini, idman kayıtlarını ve at bilgilerini
profesyonel bir şekilde birleştirip kategorize eder.

Özellikler:
- İdman tarihlerinin yarış tarihinden önce olması kontrolü
- En son yapılan idmanı bulma
- Kategoriye göre klasörleme (race_category/city/age_group)
- Eksik veri kontrolü
- Detaylı hata raporlama
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import re

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

class AdvancedHorseRacingSystem:
    def __init__(self):
        self.base_path = Path("E:/data")
        self.horses_path = self.base_path / "horses"
        self.idman_path = self.base_path / "idman"
        self.sonuclar_path = self.base_path / "sonuclar"
        self.output_path = self.base_path / "stats"
        
        # İstatistikler
        self.stats = {
            'total_races': 0,
            'total_horses': 0,
            'races_with_idman': 0,
            'races_without_idman': 0,
            'invalid_idman_dates': 0,
            'errors': []
        }
    
    def clean_folder_name(self, name):
        """Klasör adı için geçersiz karakterleri temizle"""
        # Windows'ta geçersiz karakterleri kaldır
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Boşlukları alt çizgi ile değiştir
        name = name.strip().replace(' ', '_')
        
        # Birden fazla alt çizgiyi tekile indir
        name = re.sub(r'_+', '_', name)
        
        return name
    
    def parse_date(self, date_str):
        """Farklı tarih formatlarını parse et - timezone aware"""
        if not date_str:
            return None
        
        try:
            # ISO format: 2025-08-30T00:00:00Z
            if 'T' in str(date_str):
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                # Remove timezone info for comparison
                return dt.replace(tzinfo=None)
            
            # Turkish format: 27.01.2023
            if '.' in str(date_str):
                parts = date_str.split('.')
                if len(parts) == 3:
                    return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            
            # ISO simple: 2025-08-30
            if '-' in str(date_str) and len(str(date_str).split('-')) == 3:
                return datetime.fromisoformat(str(date_str))
                
        except Exception as e:
            # Silently ignore parsing errors
            return None
        
        return None
    
    def load_horse_data(self, horse_id):
        """At verilerini yükle"""
        horse_file = self.horses_path / str(horse_id) / f"{horse_id}.json"
        
        if not horse_file.exists():
            return None
        
        try:
            with open(horse_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            # Silently ignore errors
            return None
    
    def load_idman_data(self, horse_id):
        """İdman verilerini yükle"""
        # İdman klasörünü bul
        horse_id_str = str(horse_id)
        
        # İlk 5 haneli klasör yapısı (ör: 045300 için 45354)
        folder_prefix = horse_id_str[:3].zfill(3) + "00"
        
        # Olası idman dosya yolları
        possible_paths = [
            self.idman_path / folder_prefix / f"{horse_id}.json",
            self.idman_path / horse_id_str / f"{horse_id}.json",
        ]
        
        for idman_file in possible_paths:
            if idman_file.exists():
                try:
                    with open(idman_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    return None
        
        return None
    
    def find_latest_idman_before_race(self, idman_data, race_date):
        """Yarıştan önce yapılmış en son idmanı bul"""
        if not idman_data or 'idman_records' not in idman_data:
            return None
        
        race_dt = self.parse_date(race_date)
        if not race_dt:
            return None
        
        valid_idmans = []
        
        for idman in idman_data['idman_records']:
            idman_date_str = idman.get('İ. Tarihi') or idman.get('Ä°. Tarihi')
            if not idman_date_str:
                continue
            
            idman_dt = self.parse_date(idman_date_str)
            if not idman_dt:
                continue
            
            # İdman tarihi yarış tarihinden önce mi?
            if idman_dt < race_dt:
                valid_idmans.append({
                    'idman': idman,
                    'date': idman_dt
                })
        
        # En son yapılan idmanı döndür
        if valid_idmans:
            latest = max(valid_idmans, key=lambda x: x['date'])
            return latest['idman']
        
        return None
    
    def process_race(self, race_data):
        """Tek bir yarış kaydını işle"""
        horse_id = race_data.get('horse_id')
        if not horse_id:
            return None
        
        # At verilerini yükle
        horse_data = self.load_horse_data(horse_id)
        
        # İdman verilerini yükle
        idman_data = self.load_idman_data(horse_id)
        
        # Yarış tarihinden önce yapılan en son idmanı bul
        latest_idman = None
        if idman_data:
            latest_idman = self.find_latest_idman_before_race(
                idman_data, 
                race_data.get('race_date')
            )
        
        # İstatistik güncelle
        if latest_idman:
            self.stats['races_with_idman'] += 1
        else:
            self.stats['races_without_idman'] += 1
        
        # Birleştirilmiş veri yapısı
        combined_data = {
            # Yarış bilgileri
            "race_id": race_data.get('race_id'),
            "race_date": race_data.get('race_date'),
            "city": race_data.get('city'),
            "track_type": race_data.get('track_type'),
            "distance": race_data.get('distance'),
            "race_category": race_data.get('race_category'),
            "age_group": race_data.get('age_group'),
            "finish_position": race_data.get('finish_position'),
            
            # At bilgileri
            "horse_id": horse_id,
            "horse_name": race_data.get('horse_name'),
            "horse_weight": race_data.get('horse_weight'),
            "horse_age": race_data.get('horse_age'),
            "horse_equipment": race_data.get('horse_equipment'),
            
            # Performans metrikleri
            "ganyan": race_data.get('ganyan'),
            "agf_percent": race_data.get('agf', '').replace('%', '').strip() if race_data.get('agf') else None,
            "time": race_data.get('time'),
            "kgs": race_data.get('kgs'),
            
            # İdman bilgileri (varsa)
            "workout_time": None,
            "400m": None,
            "İ. Tarihi": None,
            "İ. Hip.": None,
            "Pist": None,
            "İ. Türü": None,
        }
        
        # İdman verilerini ekle
        if latest_idman:
            combined_data.update({
                "workout_time": latest_idman.get('1000m') or latest_idman.get('800m') or latest_idman.get('600m'),
                "400m": latest_idman.get('400m'),
                "İ. Tarihi": latest_idman.get('İ. Tarihi') or latest_idman.get('Ä°. Tarihi'),
                "İ. Hip.": latest_idman.get('İ. Hip.') or latest_idman.get('Ä°. Hip.'),
                "Pist": latest_idman.get('Pist'),
                "İ. Türü": latest_idman.get('İ. Türü') or latest_idman.get('Ä°. TÃ¼rÃ¼'),
            })
        
        # At profil verileri (varsa)
        if horse_data:
            combined_data['horse_profile'] = {
                'total_races': horse_data.get('total_races', 0),
                'wins': horse_data.get('stats', {}).get('wins', 0),
                'win_rate': horse_data.get('stats', {}).get('win_rate', 0),
                'avg_finish_position': horse_data.get('stats', {}).get('avg_finish_position', 0),
            }
        
        return combined_data
    
    def save_race_data(self, race_data, combined_data):
        """Veriyi kategorize edilmiş klasöre kaydet"""
        try:
            race_category = race_data.get('race_category', 'Unknown')
            city = race_data.get('city', 'Unknown')
            age_group = race_data.get('age_group', 'Unknown')
            horse_id = race_data.get('horse_id')
            race_id = race_data.get('race_id')
            
            # Klasör adlarını temizle
            category_clean = self.clean_folder_name(race_category)
            city_clean = self.clean_folder_name(city)
            age_clean = self.clean_folder_name(age_group)
            
            # Klasör yapısını oluştur: stats/race_category/city/age_group
            output_dir = self.output_path / category_clean / city_clean / age_clean
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Dosya adı: horse_id_race_id.json
            output_file = output_dir / f"{horse_id}_{race_id}.json"
            
            # Veriyi kaydet
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def process_all_results(self):
        """Tüm sonuç dosyalarını işle"""
        print("🚀 Gelişmiş Veri Toplama Sistemi Başlatılıyor...")
        print(f"📁 Sonuçlar: {self.sonuclar_path}")
        print(f"📁 Çıktı: {self.output_path}\n")
        
        # Tüm şehirleri tara
        for city_folder in self.sonuclar_path.iterdir():
            if not city_folder.is_dir():
                continue
            
            city_name = city_folder.name
            print(f"\n🏙️ {city_name} işleniyor...")
            
            # Yıl klasörlerini tara
            for year_folder in city_folder.iterdir():
                if not year_folder.is_dir():
                    continue
                
                year = year_folder.name
                print(f"  📅 {year}...")
                
                # Ay dosyalarını tara
                for month_file in year_folder.glob('*.json'):
                    month = month_file.stem
                    
                    try:
                        with open(month_file, 'r', encoding='utf-8') as f:
                            month_data = json.load(f)
                        
                        # Her yarış numarası için
                        races_processed = 0
                        for race_num, race_content in month_data.items():
                            # Array veya nested object olabilir
                            races = []
                            
                            if isinstance(race_content, list):
                                races = race_content
                            elif isinstance(race_content, dict):
                                # Nested object - içteki tüm listleri al
                                for inner_list in race_content.values():
                                    if isinstance(inner_list, list):
                                        races.extend(inner_list)
                            
                            # Her yarışçı için
                            for race_data in races:
                                if not isinstance(race_data, dict):
                                    continue
                                    
                                self.stats['total_races'] += 1
                                
                                # Veriyi işle
                                combined = self.process_race(race_data)
                                
                                if combined:
                                    # Kaydet
                                    if self.save_race_data(race_data, combined):
                                        races_processed += 1
                        
                        print(f"    ✅ {month}.json: {races_processed} yarış işlendi")
                        
                    except Exception as e:
                        self.stats['errors'].append(f"{month_file}: {e}")
                        print(f"    ❌ {month}.json: Hata - {e}")
        
        self.print_final_stats()
    
    def print_final_stats(self):
        """Final istatistikleri yazdır"""
        print("\n" + "="*70)
        print("📊 SİSTEM İSTATİSTİKLERİ")
        print("="*70)
        print(f"Toplam Yarış: {self.stats['total_races']:,}")
        print(f"İdman Bulunan: {self.stats['races_with_idman']:,} ({self.stats['races_with_idman']/max(self.stats['total_races'],1)*100:.1f}%)")
        print(f"İdman Bulunmayan: {self.stats['races_without_idman']:,} ({self.stats['races_without_idman']/max(self.stats['total_races'],1)*100:.1f}%)")
        
        if self.stats['errors']:
            print(f"\n⚠️ Toplam Hata: {len(self.stats['errors'])}")
            print("\nİlk 10 Hata:")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
        else:
            print("\n✅ Hata Yok!")
        
        print("\n" + "="*70)
        print(f"📁 Çıktı Klasörü: {self.output_path}")
        print("="*70)

def main():
    system = AdvancedHorseRacingSystem()
    system.process_all_results()

if __name__ == "__main__":
    main()
