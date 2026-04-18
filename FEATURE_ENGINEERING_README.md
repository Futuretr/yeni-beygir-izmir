# Yarış Analiz ve Feature Engineering Sistemi

## 📁 Dosya Yolları

- **Yarış JSONları**: `E:\data\race_jsons\{Şehir}\{Yıl}\{race_id}.json`
- **At Profilleri**: `E:\data\horse_profiles\{horse_id}.json`
- **Analiz Sonuçları**: `C:\Users\emir\Desktop\HorseRacingAPI-master\analysis_results`
- **ML Dataset**: `C:\Users\emir\Desktop\HorseRacingAPI-master\ml_data`

## 🚀 Ana Scriptler

### 1. `analyze_race_features.py`
**Tek bir yarışı detaylı analiz eder**

```bash
python analyze_race_features.py
```

**Özellikler:**
- Yarış bilgilerini görüntüler
- Her at için feature'ları çıkarır
- Basit tahmin skoru hesaplar
- Top 10 tahmini gösterir
- CSV olarak kaydeder

**Çıktı:**
- `race_analysis_output.csv` - Detaylı analiz sonuçları

---

### 2. `batch_race_analysis.py`
**Birden fazla yarışı toplu olarak analiz eder**

```bash
python batch_race_analysis.py
```

**Özellikler:**
- Filtrelemeye göre yarışları seçer
- Toplu analiz yapar
- En iyi performans gösteren atları bulur
- Jokey karşılaştırması yapar
- Her yarıştaki favorileri gösterir

**Çıktılar:**
- `batch_race_analysis.csv` - Tüm yarışların detaylı verileri
- `analysis_summary.txt` - Özet rapor

---

### 3. `create_ml_features.py`
**Makine öğrenmesi için kapsamlı feature'lar oluşturur**

```bash
python create_ml_features.py
```

**Özellikler:**
- 77 farklı feature çıkarır
- Gelişmiş performans analizi
- Form analizi
- Trend hesaplamaları
- Pist/mesafe uyumu
- Genetik bilgiler
- Zaman bazlı feature'lar

**Çıktı:**
- `ml_features_dataset.csv` - ML için hazır dataset (77 sütun)

---

## 📊 Feature Kategorileri

### 1. Temel Bilgiler (6)
- `horse_age` - At yaşı
- `horse_weight` - At ağırlığı
- `handicap_weight` - Handikap ağırlığı
- `total_weight` - Toplam taşınan ağırlık
- `start_position` - Start pozisyonu
- `race_distance` - Yarış mesafesi

### 2. Kariyer İstatistikleri (4)
- `career_total_races` - Toplam yarış sayısı
- `career_avg_finish` - Kariyer ortalama derece
- `career_avg_time` - Kariyer ortalama süre
- `last_race_days_ago` - Son yarıştan beri geçen gün

### 3. Son N Yarış Performansı (32)
Her biri için (N = 1, 3, 5, 10):
- `last_N_avg_finish` - Ortalama derece
- `last_N_best_finish` - En iyi derece
- `last_N_worst_finish` - En kötü derece
- `last_N_std_finish` - Derece standart sapma
- `last_N_avg_time` - Ortalama süre
- `last_N_std_time` - Süre standart sapma
- `last_N_win_rate` - Kazanma oranı
- `last_N_top3_rate` - Top 3 oranı

### 4. Trend Analizi (1)
- `performance_trend` - Performans trendi

### 5. Pist ve Mesafe Uyumu (9)
- `track_type_races` - Bu pistte kaç yarış
- `track_type_avg_time` - Bu pistte ortalama süre
- `distance_races` - Bu mesafede kaç yarış
- `distance_avg_finish` - Bu mesafede ortalama derece
- `distance_avg_time` - Bu mesafede ortalama süre
- `city_races` - Bu şehirde kaç yarış
- `city_avg_finish` - Bu şehirde ortalama derece
- `total_track_experience` - Toplam pist deneyimi
- `distance_variety` - Mesafe çeşitliliği

### 6. Form Analizi (6)
- `form_length` - Form string uzunluğu
- `form_avg` - Form ortalaması
- `form_best` - Form en iyi
- `form_worst` - Form en kötü
- `form_consistency` - Form tutarlılığı
- `recent_form_trend` - Son form trendi

### 7. Bahis Verileri (5)
- `ganyan` - Ganyan oranı
- `agf` - AGF yüzdesi
- `kgs` - Koşu galibiyet sayısı
- `ganyan_log` - Log transformlu ganyan
- `is_favorite` - Favori mi (ganyan < 5)

### 8. İlişkisel Bilgiler (3)
- `jockey_id` - Jokey ID
- `trainer_id` - Antrenör ID
- `owner_id` - Sahip ID

### 9. Genetik Bilgiler (2)
- `father_id` - Baba ID
- `mother_id` - Anne ID

### 10. Zaman Bazlı (3)
- `races_last_30_days` - Son 30 gündeki yarış sayısı
- `races_last_60_days` - Son 60 gündeki yarış sayısı
- `races_last_90_days` - Son 90 gündeki yarış sayısı

### 11. Yarış Bilgileri (5)
- `race_id` - Yarış ID
- `race_date` - Yarış tarihi
- `race_city` - Yarış şehri
- `race_track_type` - Pist tipi
- `horse_id` - At ID
- `horse_name` - At adı

**TOPLAM: 77 Feature**

---

## 🎯 Tahmin Skoru Hesaplama

Basit tahmin skoru şu faktörleri dikkate alır:

```python
skor = (
    (15 - last_3_avg_finish) * 10 +      # Son 3 yarış performansı
    (15 - career_avg_finish) * 5 +       # Kariyer ortalaması
    (100 - agf) * 0.5 +                  # AGF etkisi
    track_type_races * 2 +               # Pist deneyimi
    distance_races * 3 +                 # Mesafe deneyimi
    (15 - distance_avg_finish) * 8 +     # Mesafe performansı
    kgs * 5 +                            # Kazanma sayısı
    güncellik_bonusu                     # Son yarıştan beri geçen süre
)
```

---

## 📈 Kullanım Örnekleri

### Örnek 1: Tek Yarış Analizi

```python
from analyze_race_features import analyze_race, display_predictions

race_file = "E:/data/race_jsons/Antalya/2026/222832.json"
race_info, df = analyze_race(race_file)
display_predictions(df, top_n=10)
```

### Örnek 2: Filtrelenmiş Yarışlar

```python
from batch_race_analysis import filter_races_by_criteria, analyze_multiple_races

# İstanbul, Çim pist, 1600m
races = filter_races_by_criteria(
    "E:/data/race_jsons",
    city="Istanbul",
    track_type="Çim",
    distance=1600,
    limit=50
)

df = analyze_multiple_races(races, output_dir="./results")
```

### Örnek 3: ML Dataset Oluşturma

```python
from create_ml_features import create_ml_dataset
from pathlib import Path

race_files = list(Path("E:/data/race_jsons").glob("**/*.json"))[:1000]
df = create_ml_dataset(race_files, output_file="ml_dataset.csv")

print(f"Feature sayısı: {len(df.columns)}")
print(f"Veri sayısı: {len(df)}")
```

---

## 🔧 Geliştirme İpuçları

### Yeni Feature Ekleme

`create_ml_features.py` içindeki `RaceFeatureExtractor` sınıfına yeni metod ekleyin:

```python
def _extract_new_features(self, horse):
    """Yeni feature'lar"""
    return {
        'new_feature_1': calculation1,
        'new_feature_2': calculation2,
    }

# extract_all_features metoduna ekleyin:
features.update(self._extract_new_features(horse))
```

### Tahmin Skoru Özelleştirme

`analyze_race_features.py` içindeki `calculate_prediction_score` fonksiyonunu düzenleyin:

```python
def calculate_prediction_score(row):
    score = 0
    
    # Kendi skorlama mantığınızı ekleyin
    if row['yeni_feature'] > threshold:
        score += bonus
    
    return score
```

---

## 📊 Analiz Sonuçları Örnekleri

### En İyi 3 At (Antalya, Sentetik, 2000m)

1. **GRİNGO** (#5)
   - Skor: 400.3
   - Son 3 yarış ort: 2.67
   - Bu mesafede ort: 3.00
   - Ganyan: 4.5, AGF: %14
   - KGS: 12

2. **ÖZGÜNALP** (#8)
   - Skor: 389.5
   - Son 3 yarış ort: 2.33
   - Bu mesafede ort: 1.00
   - Ganyan: 2.35, AGF: %29
   - KGS: 6

3. **ARAM SAMSAM** (#11)
   - Skor: 384.1
   - Son 3 yarış ort: 6.00
   - Bu mesafede ort: 3.00
   - Ganyan: 5.5, AGF: %13
   - KGS: 16

---

## 🎓 Sonraki Adımlar

1. **Model Eğitimi**: ML dataset ile tahmin modeli eğitin
2. **Feature Seçimi**: En önemli feature'ları belirleyin
3. **Hiperparametre Optimizasyonu**: Model parametrelerini ayarlayın
4. **Backtesting**: Geçmiş yarışlarda tahmin performansını test edin
5. **Ensemble Modeller**: Birden fazla modeli birleştirin

---

## 📝 Notlar

- Tüm feature'lar eksik veri kontrolü yapılarak oluşturulmuştur
- NaN değerler için uygun default değerler atanmıştır
- Kategorik değişkenler encode edilmeye hazırdır
- Zaman serisi analizi için tarih sütunları mevcuttur

---

## 🐛 Hata Ayıklama

**Sık Karşılaşılan Hatalar:**

1. **FileNotFoundError**: Dosya yollarını kontrol edin
2. **JSON Decode Error**: JSON dosyası bozuk olabilir, try-except ile atlayın
3. **Memory Error**: Daha az sayıda yarış ile başlayın
4. **Division by Zero**: Feature hesaplamalarında kontroller mevcut

---

## 📞 Yardım

Sorunlar için script başındaki dokümantasyonu kontrol edin veya:
- Feature açıklamalarına bakın
- Örnek kullanımları inceleyin
- Debug modda çalıştırın

---

**Son Güncelleme**: 2026-02-03
**Versiyon**: 1.0
**Toplam JSON Yarış**: 32,415
**Toplam Feature**: 77
