# Gelişmiş At Yarışı Veri Sistemi

## 📋 Genel Bakış

Bu sistem, TJK at yarışı verilerini profesyonel bir şekilde toplar, birleştirir ve organize eder. Her yarış için at profili, idman kayıtları ve performans metriklerini bir araya getirir.

## 🗂️ Klasör Yapısı

```
E:\data\stats\
├── [Yarış Kategorisi]/           # Örn: "Handikap 15", "Maiden", "KV-6"
│   ├── [Şehir]/                   # Örn: "Ankara", "Istanbul", "Izmir"
│   │   ├── [Yaş Grubu]/          # Örn: "4 ve Yukarı Araplar", "3 Yaşlı İngilizler"
│   │   │   ├── [horse_id]_[race_id].json
│   │   │   └── ...
```

### Örnek Klasör Yapısı
```
E:\data\stats\
├── Handikap 15\
│   ├── Ankara\
│   │   ├── Arap\
│   │   │   ├── 101329_210068.json
│   │   │   ├── 103149_212746.json
│   │   │   └── ...
│   │   └── İngiliz\
│   │       └── ...
│   ├── Istanbul\
│   └── ...
├── Maiden\
├── KV-6\
└── ...
```

## 📊 Veri Formatı

Her JSON dosyası aşağıdaki bilgileri içerir:

### Yarış Bilgileri
- `race_id`: Yarış ID'si
- `race_date`: Yarış tarihi
- `city`: Şehir
- `track_type`: Pist türü (Kum, Çim, Sentetik)
- `distance`: Mesafe (metre)
- `race_category`: Yarış kategorisi
- `age_group`: Yaş grubu
- `finish_position`: Bitiş sırası

### At Bilgileri
- `horse_id`: At ID'si
- `horse_name`: At adı
- `horse_weight`: At ağırlığı
- `horse_age`: At yaşı
- `horse_equipment`: Ekipman
- `horse_profile`: At profil istatistikleri
  - `total_races`: Toplam yarış sayısı
  - `wins`: Kazanılan yarışlar
  - `win_rate`: Kazanma oranı
  - `avg_finish_position`: Ortalama bitiş sırası

### Performans Metrikleri
- `ganyan`: Ganyan oranı
- `agf_percent`: AGF yüzdesi
- `time`: Yarış süresi
- `kgs`: KGS değeri

### İdman Bilgileri
- `last_idman`: Yarıştan önceki en son idman kaydı
  - `İ. Tarihi`: İdman tarihi
  - `İ. Hip.`: İdman hipodromu
  - `Pist`: Pist türü
  - `İ. Türü`: İdman türü (Galop, Sprint, Kenter)
  - `400m`, `600m`, `800m`, `1000m`: İdman süreleri

## 🔍 Özellikler

### 1. Akıllı İdman Seçimi
- ✅ İdman tarihi **yarış tarihinden önce** olmalı
- ✅ Yarıştan önceki **en son** idman otomatik seçilir
- ✅ Tarih kontrolü hassas datetime karşılaştırması ile yapılır

### 2. Veri Bütünlüğü
- ✅ Eksik veriler `null` olarak işaretlenir
- ✅ Hatalı kayıtlar atlanır
- ✅ Her veri validasyondan geçer

### 3. Performans
- ✅ Optimize edilmiş dosya okuma
- ✅ Hata toleranslı işlem
- ✅ İlerleme göstergesi

## 📈 İstatistikler

Sistem çalıştırıldığında şu istatistikler raporlanır:
- Toplam işlenen yarış sayısı
- İdman bulunan yarışlar
- İdman bulunmayan yarışlar
- Hata oranı

## 🚀 Kullanım

### Sistemi Çalıştırma

```bash
python build_advanced_system.py
```

### Örnek Çıktı

```
🚀 Gelişmiş Veri Toplama Sistemi Başlatılıyor...
📁 Sonuçlar: E:\data\sonuclar
📁 Çıktı: E:\data\stats

🏙️ Ankara işleniyor...
  📅 2025...
    ✅ 08.json: 1042 yarış işlendi

======================================================================
📊 SİSTEM İSTATİSTİKLERİ
======================================================================
Toplam Yarış: 125,482
İdman Bulunan: 45,234 (36.1%)
İdman Bulunmayan: 80,248 (63.9%)

✅ Hata Yok!
======================================================================
```

## 📝 Veri Örneği

```json
{
  "race_id": 210068,
  "race_date": "2024-05-30T00:00:00Z",
  "city": "Ankara",
  "track_type": "Kum",
  "distance": 1300,
  "race_category": "Handikap 15/DHÖW/Dişi /H1",
  "age_group": "4 ve Yukarı Araplar",
  "finish_position": "1",
  "horse_id": 101329,
  "horse_name": "AYŞIN HANIM",
  "horse_weight": "54",
  "ganyan": "3,20",
  "agf_percent": "13",
  "time": "1.31.19",
  "kgs": "34",
  "last_idman": {
    "İ. Tarihi": "18.09.2022",
    "İ. Hip.": "Bursa",
    "Pist": "Kum",
    "İ. Türü": "Galop",
    "800m": "0.55.40",
    "400m": "0.28.00"
  },
  "horse_profile": {
    "total_races": 15,
    "wins": 3,
    "win_rate": 0.20,
    "avg_finish_position": 4.5
  }
}
```

## ⚙️ Teknik Detaylar

### Tarih Formatları
Sistem şu tarih formatlarını destekler:
- ISO 8601: `2024-05-30T00:00:00Z`
- Türkçe: `18.09.2022`
- Basit ISO: `2024-05-30`

### Encoding
- Tüm dosyalar UTF-8 encoding ile kaydedilir
- Türkçe karakterler desteklenir
- JSON formatı pretty-print (indent=2)

### Klasör Adı Temizleme
Geçersiz karakterler otomatik temizlenir:
- `<>:"/\|?*` karakterleri `_` ile değiştirilir
- Boşluklar `_` olur
- Örnek: `Handikap 15/DHÖW` → `Handikap_15_DHÖW`

## 🔧 Gereksinimler

```
Python 3.8+
```

Standart kütüphaneler kullanılır, ek paket gerekmez.

## 📚 Veri Kaynakları

Sistem şu klasörleri kullanır:
- `E:\data\horses` - At profil verileri
- `E:\data\idman` - İdman kayıtları
- `E:\data\sonuclar` - Yarış sonuçları
- `E:\data\stats` - Çıktı klasörü (oluşturulur)

## 🎯 Kullanım Senaryoları

### 1. Machine Learning Model Eğitimi
Organize edilmiş veriler ML modelleri için hazır:
```python
import json
from pathlib import Path

# Belirli bir kategorideki tüm yarışları yükle
category_path = Path("E:/data/stats/Handikap 15/Ankara/Arap")
races = []
for race_file in category_path.glob("*.json"):
    with open(race_file) as f:
        races.append(json.load(f))

# Model eğitimi için features çıkar
features = [
    [r['distance'], r['horse_weight'], r['kgs']] 
    for r in races if r.get('kgs')
]
```

### 2. İstatistiksel Analiz
```python
import pandas as pd

# Kategori bazlı analiz
df = pd.DataFrame(races)
win_rate_by_age = df.groupby('horse_age')['finish_position'].apply(
    lambda x: (x == '1').sum() / len(x)
)
```

### 3. Veri Keşfi
```python
# En başarılı atları bul
top_horses = df[df['finish_position'] == '1']['horse_name'].value_counts()

# İdman süreleri ile performans korelasyonu
idman_times = [r['last_idman']['400m'] for r in races if r.get('last_idman')]
```

## 🛡️ Veri Kalitesi

- ✅ Her yarış için benzersiz dosya
- ✅ Tutarlı veri formatı
- ✅ Null değerler açıkça belirtilir
- ✅ Tarihlerde timezone tutarlılığı
- ✅ Duplicate kontrolü

## 📞 Destek

Sorular için: 
- Script: `build_advanced_system.py`
- Log dosyası: Terminal çıktısı

---

**Not:** Bu sistem profesyonel veri bilimi standartlarında tasarlanmıştır. Verileriniz analiz ve ML için hazırdır!
