# 🏇 At Yarışı XGBoost Ranking Sistemi - Hızlı Başlangıç

## 🚀 Hızlı Başlangıç (3 Adım)

### 1️⃣ Sistemi Çalıştır
```bash
run_ml_system.bat
```
Bu komut:
- ✅ Tüm verileri yükler (sonuçlar, program, idman)
- ✅ Kazanan profilleri ve win rate'leri hesaplar
- ✅ XGBoost Ranker modelini eğitir
- ✅ Ocak 2025'i test eder

### 2️⃣ Tahmin Yap
```bash
predict_race.bat
```
Varsayılan olarak **Adana - 04 Ocak 2025 - 1. Yarış** için tahmin yapar.

### 3️⃣ Farklı Yarış İçin Tahmin

`E:\data\ml\predict_race.py` dosyasını düzenleyin (Satır 158-163):

```python
city = "Ankara"         # Şehri değiştir
year = 2025
month = 1
day = 15
race_number = 3         # Yarış numarasını değiştir
```

Sonra tekrar çalıştır:
```bash
predict_race.bat
```

## 📁 Dosya Yapısı

```
E:\data\
├── sonuclar\          # Yarış sonuçları (GİRDİ)
├── program\           # Yarış programları (GİRDİ)
├── idman\             # İdman verileri (GİRDİ)
└── ml\                # Model ve tahminler (ÇIKTI)
    ├── xgboost_ranker.json      # Eğitilmiş model
    ├── training_data.csv        # Eğitim verisi
    ├── prediction_*.csv         # Tahmin sonuçları
    └── README.md                # Detaylı dökümantasyon
```

## 🎯 Tahmin Çıktısı Örneği

```
🏆 YARIŞ TAHMİNİ VE SIRALAMASI
═══════════════════════════════════════════════════════════════════════

📍 Yarış Bilgileri:
   Şehir: Adana
   Kategori: Maiden
   Yaş Grubu: 4 Yaşlı Araplar
   Pist: Kum - 1200m

🏇 Atlar ve Tahminler:
───────────────────────────────────────────────────────────────────────
Sıra   At Adı                    Jokey                Win Rate     
───────────────────────────────────────────────────────────────────────
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

## 🔧 Manuel Çalıştırma

Python ile direkt çalıştırmak için:

```bash
# 1. Ortamı aktifleştir
.venv\Scripts\activate

# 2. Veri hazırla
python E:\data\ml\prepare_ranking_data.py

# 3. Model eğit
python E:\data\ml\train_xgboost_ranker.py

# 4. Tahmin yap
python E:\data\ml\predict_race.py
```

## 📊 Model Performansı

Model eğitimi sonunda şu metrikler gösterilir:

- **Top-1 Accuracy**: Birinci gelen atı doğru tahmin etme oranı
- **Top-3 Accuracy**: Kazanan atın ilk 3'te olma oranı

Örnek:
```
🎯 Sonuçlar:
  • Top-1 Accuracy: 28.5% (57/200)
  • Top-3 Accuracy: 64.0% (128/200)
```

## 🎓 Sistem Mantığı

1. **Kategorize Et**: Aynı şehir, pist, kategori, yaş grubundaki yarışları grupla
2. **Kazananları Analiz Et**: 1. gelen atların ortalama özelliklerini çıkar
3. **Win Rate Hesapla**: Jokey/trainer/owner'ların başarı oranlarını hesapla
4. **Ranking Yap**: XGBoost ile atları pairwise karşılaştır ve sırala
5. **Tahmin Yap**: Yeni yarışlarda atları sırala ve win rate sun

## ⚠️ Önemli Notlar

- ✅ Model, geçmiş verilere göre öğrenir (en az 100+ yarış gerekli)
- ✅ Test ayı (Ocak 2025) eğitimde kullanılmaz
- ✅ Win rate'ler model güven skorudur, gerçek olasılık değildir
- ⚠️ Eğitimde olmayan kategoriler için tahmin zayıf olabilir

## 📚 Detaylı Dökümantasyon

Tüm detaylar için:
```
E:\data\ml\README.md
```

## 🆘 Sorun Giderme

**Model bulunamadı hatası:**
```bash
# Önce modeli eğitin
run_ml_system.bat
```

**Veri yüklenemedi hatası:**
- E:\data\sonuclar klasörünü kontrol edin
- E:\data\program klasörünü kontrol edin
- JSON dosyalarının formatını kontrol edin

**XGBoost hatası:**
```bash
pip install xgboost pandas numpy scikit-learn joblib
```

---

**🏇 İyi Tahminler! 🎯**
