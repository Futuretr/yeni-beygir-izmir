# 🏇 AT YARIŞI XGBOOST RANKING SİSTEMİ

## ✅ SİSTEM HAZIR!

Tüm dosyalar oluşturuldu ve sistem çalışmaya hazır.

---

## 📦 OLUŞTURULAN DOSYALAR

### E:\data\ml\ (ML Sistemi)
```
prepare_ranking_data.py     # Veri hazırlama scripti
train_xgboost_ranker.py     # Model eğitim scripti  
predict_race.py             # Tahmin scripti
run_all.py                  # Tüm süreci otomatik çalıştırır
test_system.py              # Sistem test scripti
README.md                   # Detaylı dokümantasyon
```

### C:\Users\emir\Desktop\HorseRacingAPI-master\
```
run_ml_system.bat           # Sistemi çalıştırır (KOLAY)
predict_race.bat            # Tahmin yapar (KOLAY)
ML_QUICK_START.md           # Hızlı başlangıç kılavuzu
```

---

## 🚀 KULLANIM

### YÖNTEM 1: Kolay Yol (Önerilen)

#### 1️⃣ Sistemi Eğit
```
run_ml_system.bat
```
Çift tıkla veya PowerShell'de çalıştır. Bu:
- Tüm verileri yükler
- Kazanan profilleri çıkarır
- Win rate'leri hesaplar
- XGBoost modelini eğitir
- Ocak 2025'i test eder

**Süre:** ~2-10 dakika (veri boyutuna göre)

#### 2️⃣ Tahmin Yap
```
predict_race.bat
```
Varsayılan: Adana - 04 Ocak 2025 - 1. Yarış

**Farklı yarış için:**
1. `E:\data\ml\predict_race.py` dosyasını aç
2. Satır 158-163'ü düzenle:
   ```python
   city = "Ankara"      # Şehir
   year = 2025
   month = 1
   day = 15
   race_number = 3      # Yarış no
   ```
3. Tekrar `predict_race.bat` çalıştır

### YÖNTEM 2: Manuel

```powershell
# Ortamı aktifleştir
.venv\Scripts\activate

# Hızlı test
python E:\data\ml\test_system.py

# Veri hazırla
python E:\data\ml\prepare_ranking_data.py

# Model eğit
python E:\data\ml\train_xgboost_ranker.py

# Tahmin yap
python E:\data\ml\predict_race.py
```

---

## 📊 SİSTEM AKIŞI

```
┌─────────────────────────┐
│  VERİ KAYNAKLARI        │
├─────────────────────────┤
│ E:\data\sonuclar\       │ ──┐
│ E:\data\program\        │ ──┤
│ E:\data\idman\          │ ──┤
└─────────────────────────┘   │
                              │
                              ▼
┌─────────────────────────────────────────┐
│  PREPARE_RANKING_DATA.PY                │
├─────────────────────────────────────────┤
│ ✓ Sonuçları yükle                       │
│ ✓ Kazanan profilleri çıkar             │
│ ✓ Win rate'leri hesapla                │
│ ✓ Feature engineering                   │
│ ✓ Verileri birleştir                    │
└─────────────────────────────────────────┘
                              │
                              ▼
                     training_data.csv
                     winner_profiles.csv
                     jockey_stats.csv
                     trainer_stats.csv
                     owner_stats.csv
                              │
                              ▼
┌─────────────────────────────────────────┐
│  TRAIN_XGBOOST_RANKER.PY                │
├─────────────────────────────────────────┤
│ ✓ Feature encoding                      │
│ ✓ Ranking grupları oluştur             │
│ ✓ Train/Test split (Ocak 2025)        │
│ ✓ XGBoost Ranker eğit                  │
│ ✓ Modeli değerlendir                   │
│ ✓ Kaydet                                │
└─────────────────────────────────────────┘
                              │
                              ▼
                     xgboost_ranker.json
                     feature_list.pkl
                     label_encoders.pkl
                     model_metadata.pkl
                              │
                              ▼
┌─────────────────────────────────────────┐
│  PREDICT_RACE.PY                        │
├─────────────────────────────────────────┤
│ ✓ Modeli yükle                          │
│ ✓ Yarış verisini yükle                  │
│ ✓ Feature'ları hazırla                  │
│ ✓ Tahmin yap                            │
│ ✓ Win rate hesapla                      │
│ ✓ Sırala ve göster                      │
└─────────────────────────────────────────┘
                              │
                              ▼
                      🏆 TAHMIN SONUÇLARI
```

---

## 🎯 ÖRNEK ÇIKTI

```
🏆 YARIŞ TAHMİNİ VE SIRALAMASI
══════════════════════════════════════════════════════════════

📍 Yarış Bilgileri:
   Şehir: Adana
   Tarih: 2025-01-04
   Yarış No: 1
   Kategori: Maiden
   Yaş Grubu: 4 Yaşlı Araplar
   Pist: Kum - 1200m
   Ödül: 390.000

🏇 Atlar ve Tahminler:
──────────────────────────────────────────────────────────────
Sıra   At Adı                    Jokey                Win Rate
──────────────────────────────────────────────────────────────
🥇     KAYIHAN BEY              H.ÇİZİK              32.5% ████████
🥈     ŞANLI YILDIZ             M.KAYA               24.1% ██████
🥉     HIZLI OK                 A.YILMAZ             18.3% ████
4.     DENİZ ATAŞ               S.DEMİR              12.7% ███
5.     SARI DÜNYA               K.ÖZ                  8.9% ██

⭐ Önerilen Bahis:
   1. KAYIHAN BEY (Win Rate: 32.5%)
   2. ŞANLI YILDIZ (Win Rate: 24.1%)
   3. HIZLI OK (Win Rate: 18.3%)
```

---

## 🎓 MODEL DETAYLARI

### Algoritma
- **XGBoost Ranker** (Pairwise ranking)
- Objective: `rank:pairwise`
- Metric: `NDCG` (Normalized Discounted Cumulative Gain)

### Feature'lar (20+)
**Kategorik:**
- Şehir, pist türü, yarış kategorisi, yaş grubu

**At Özellikleri:**
- Ağırlık, handikap, KGS, start no, mesafe

**Başarı Oranları:**
- Jokey/trainer/owner win rate ve tecrübe

**Kazanan Profil Benzerliği:**
- Kazananların ortalama/sapma değerleri

### Eğitim
- **Train:** 2021-2024 + Şubat 2025 ve sonrası
- **Test:** Ocak 2025 (değerlendirme için)
- **Relevance:** 1. = 10 puan, 2. = 9 puan, ...

### Win Rate Hesaplama
```python
win_rate = softmax(predicted_score) * 100
```

---

## 📈 PERFORMANS

Model performansı eğitim sonunda gösterilir:

```
🎯 Sonuçlar:
  • Top-1 Accuracy: 28.5% (57/200)
  • Top-3 Accuracy: 64.0% (128/200)
```

- **Top-1:** Birinci gelen atı doğru tahmin etme
- **Top-3:** Kazanan atın ilk 3'te olma

---

## 📁 ÇIKTI DOSYALARI

| Dosya | Açıklama | Boyut |
|-------|----------|-------|
| `training_data.csv` | Birleştirilmiş eğitim verisi | ~10-50 MB |
| `xgboost_ranker.json` | Eğitilmiş model | ~500 KB |
| `feature_list.pkl` | Feature listesi | ~1 KB |
| `label_encoders.pkl` | Kategorik encoders | ~10 KB |
| `model_metadata.pkl` | Performans metrikleri | ~1 KB |
| `sample_predictions.csv` | Test tahminleri | ~100 KB |
| `prediction_*.csv` | Yarış tahminleri | ~10 KB |

---

## ⚠️ NOTLAR

✅ **Yapılması Gerekenler:**
- İlk çalıştırmada `run_ml_system.bat` çalıştır
- Model eğitildikten sonra tahmin yapabilirsin
- Her yeni veri eklediğinde modeli yeniden eğit

❌ **Yaygın Hatalar:**
- Model eğitilmeden tahmin yapmaya çalışmak
- Veri klasörlerinin yanlış yolu
- Eğitimde olmayan kategori için tahmin

💡 **İpuçları:**
- Model 100+ yarış ile iyi çalışır
- Daha fazla veri = daha iyi tahmin
- Win rate mutlak değil, göreceli sıralamadır
- Test ayını değiştirerek farklı ayları test edebilirsin

---

## 🆘 SORUN GİDERME

### "Model bulunamadı" hatası
```bash
# Çözüm: Önce eğit
run_ml_system.bat
```

### "Veri yüklenemedi" hatası
```bash
# Çözüm: Klasörleri kontrol et
python E:\data\ml\test_system.py
```

### "XGBoost kurulu değil" hatası
```bash
# Çözüm: Kütüphaneyi kur
pip install xgboost
```

### Tahmin çok uzun sürüyor
```bash
# Veri miktarını azalt veya CPU sayısını artır
# train_xgboost_ranker.py içinde:
# params['nthread'] = 4  # CPU sayısı
```

---

## 📚 DAHA FAZLA BİLGİ

- **Detaylı Dokümantasyon:** `E:\data\ml\README.md`
- **Hızlı Başlangıç:** `ML_QUICK_START.md`
- **Kod:** `E:\data\ml\*.py`

---

## 🎉 BAŞARILAR!

Artık XGBoost ile at yarışı tahminleri yapabilirsiniz!

**İlk adım:**
```
run_ml_system.bat
```

**🏇 İyi Tahminler! 🎯**
