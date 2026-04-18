# XGBoost Model ve Feature Importance Analizi Sonuçları

## 📊 Model Performansı

### 🎯 Regression Model (Derece Tahmini)

**Performans Metrikleri:**
- **MAE**: 0.783 (ortalama 0.78 derece hata)
- **RMSE**: 1.357
- **R² Score**: 0.847 (Model varyansın %84.7'sini açıklıyor)

**Yorum:** Model çok başarılı! Ortalama 0.78 derecelik bir hatayla atın hangi derecede geleceğini tahmin edebiliyor.

---

### 🏆 Classification Model (Top 3 Tahmini)

**Performans Metrikleri:**
- **Accuracy**: 99.3%
- **Top 3 Precision**: 100%
- **Top 3 Recall**: 88%
- **F1-Score**: 94%

**Confusion Matrix:**
```
Gerçek\Tahmin    Not Top3    Top3
Not Top3           258         0
Top3                 2        15
```

**Yorum:** Model çok yüksek doğrulukla Top 3'e girecek atları tespit edebiliyor!

---

## 🔥 En Önemli Feature'lar

### Regression (Derece Tahmini) - Top 10

| Sıra | Feature | Importance | Açıklama |
|------|---------|------------|----------|
| 1 | last_3_worst_finish | 31.4% | Son 3 yarıştaki en kötü derece |
| 2 | last_5_worst_finish | 15.9% | Son 5 yarıştaki en kötü derece |
| 3 | last_3_avg_finish | 9.4% | Son 3 yarış ortalama derece |
| 4 | last_3_win_rate | 3.3% | Son 3 yarışta kazanma oranı |
| 5 | last_3_best_finish | 3.2% | Son 3 yarıştaki en iyi derece |
| 6 | last_10_std_finish | 2.4% | Son 10 yarış derece std sapması |
| 7 | last_5_win_rate | 2.3% | Son 5 yarışta kazanma oranı |
| 8 | last_3_std_finish | 1.6% | Son 3 yarış derece std sapması |
| 9 | last_5_avg_finish | 1.5% | Son 5 yarış ortalama derece |
| 10 | last_10_avg_time | 1.4% | Son 10 yarış ortalama süre |

---

### Classification (Top 3 Tahmini) - Top 10

| Sıra | Feature | Importance | Açıklama |
|------|---------|------------|----------|
| 1 | last_3_best_finish | 24.4% | Son 3 yarıştaki en iyi derece |
| 2 | last_5_std_finish | 10.4% | Son 5 yarış derece std sapması |
| 3 | last_10_worst_finish | 6.0% | Son 10 yarıştaki en kötü derece |
| 4 | last_3_avg_time | 2.9% | Son 3 yarış ortalama süre |
| 5 | form_length | 2.8% | Form string uzunluğu |
| 6 | last_10_avg_time | 2.5% | Son 10 yarış ortalama süre |
| 7 | career_avg_time | 2.2% | Kariyer ortalama süre |
| 8 | last_5_avg_finish | 2.0% | Son 5 yarış ortalama derece |
| 9 | last_5_top3_rate | 2.0% | Son 5 yarışta top3 oranı |
| 10 | last_3_worst_finish | 2.0% | Son 3 yarıştaki en kötü derece |

---

## 📈 Feature Grup Analizi

### Regression Model

| Grup | Feature Sayısı | Toplam Importance | Ortalama | Yorum |
|------|---------------|-------------------|----------|-------|
| **Son Yarışlar** | 24 | 82.83% | 3.45% | 🔥 En önemli grup! |
| **Pist/Mesafe** | 10 | 6.11% | 0.61% | Önemli |
| **Genetik** | 2 | 1.95% | 0.98% | Orta |
| **Form** | 6 | 1.84% | 0.31% | Orta |
| **İlişkisel** | 3 | 1.71% | 0.57% | Orta |
| Kariyer | 3 | 1.42% | 0.47% | Düşük |
| Temel | 4 | 1.42% | 0.35% | Düşük |
| Bahis | 4 | 0.98% | 0.25% | Düşük |
| Zaman | 4 | 0.85% | 0.21% | Düşük |
| Trend | 2 | 0.80% | 0.40% | Düşük |

---

### Classification Model

| Grup | Feature Sayısı | Toplam Importance | Ortalama | Yorum |
|------|---------------|-------------------|----------|-------|
| **Son Yarışlar** | 24 | 67.81% | 2.83% | 🔥 En önemli grup! |
| **Pist/Mesafe** | 10 | 7.69% | 0.77% | Önemli |
| **Form** | 6 | 6.83% | 1.14% | Önemli |
| **Kariyer** | 3 | 4.37% | 1.46% | Orta |
| **İlişkisel** | 3 | 3.60% | 1.20% | Orta |
| Temel | 4 | 2.48% | 0.62% | Düşük |
| Genetik | 2 | 2.21% | 1.10% | Düşük |
| Bahis | 4 | 2.00% | 0.50% | Düşük |
| Zaman | 4 | 1.74% | 0.44% | Düşük |
| Trend | 2 | 1.33% | 0.67% | Düşük |

---

## 💡 Önemli Bulgular

### 1. Son Performans En Önemli Faktör
- **%82.8** (regression) ve **%67.8** (classification) importance değeri
- Özellikle son 3-5 yarış kritik
- En kötü derece bile önemli bir gösterge

### 2. Pist ve Mesafe Deneyimi Önemli
- Atın bu pistte/mesafede daha önce koşup koşmadığı önemli
- **%6-7** civarında importance

### 3. Form ve Tutarlılık
- Form string (son 6 yarış) özellikle classification'da önemli
- Standart sapma (tutarlılık) değerli bir metrik

### 4. Sürpriz Bulgular
- **Genetik** (baba/anne) düşünüldüğünden daha az önemli (%2)
- **Bahis verileri** (ganyan, AGF) beklenenden az etkili (%1-2)
- **Jokey/Antrenör** orta düzeyde önemli (%1.7-3.6)

### 5. Zayıf Feature'lar
- Temel bilgiler (yaş, ağırlık) çok etkili değil
- Zaman bazlı feature'lar (son 30/60/90 gün) az önemli

---

## 🎯 Model Kullanım Önerileri

### Regression Model Kullan:
- Tam derece tahmini istiyorsan
- Sıralama yapmak için
- Detaylı analiz için

### Classification Model Kullan:
- Top 3'e girme ihtimalini öğrenmek için
- Kesin tahmin istiyorsan (99.3% doğruluk!)
- Risk yönetimi için

---

## 📁 Oluşturulan Dosyalar

### Grafikler
- `feature_importance_regression.png` - Regression için en önemli 30 feature
- `feature_importance_classification.png` - Classification için en önemli 30 feature
- `predictions_regression.png` - Gerçek vs Tahmin scatter plot
- `roc_curve_classification.png` - ROC curve (AUC score)

### Veri Dosyaları
- `feature_importance_regression.csv` - Tüm feature'ların importance değerleri
- `feature_importance_classification.csv` - Tüm feature'ların importance değerleri
- `model_summary.json` - Özet metrikler ve top features

### Model Dosyaları
- `xgboost_regression.json` - Eğitilmiş regression modeli
- `xgboost_classification.json` - Eğitilmiş classification modeli

---

## 🚀 Sonraki Adımlar

### ✅ Tamamlananlar
- XGBoost model eğitimi
- Feature importance analizi
- Model değerlendirmesi
- Görselleştirmeler

### ⬜ Yapılabilecekler
1. **Hiperparametre Optimizasyonu**
   - GridSearch/RandomSearch
   - Bayesian Optimization

2. **Ensemble Modeller**
   - Random Forest ile karşılaştırma
   - Model stacking

3. **Backtesting**
   - Geçmiş yarışlarda test
   - ROI analizi

4. **Production Deployment**
   - API endpoint
   - Real-time tahmin

5. **Feature Engineering v2**
   - Interaction features
   - Polynomial features
   - Daha fazla domain knowledge

---

## 📊 Örnek Kullanım

```python
import xgboost as xgb
import pandas as pd

# Model yükle
model = xgb.XGBRegressor()
model.load_model('xgboost_regression.json')

# Yeni veri hazırla
new_data = pd.read_csv('new_race_data.csv')

# Tahmin yap
predictions = model.predict(new_data)

# En iyi 3 atı bul
top_3_indices = predictions.argsort()[:3]
print(f"Top 3 tahmin: {new_data.iloc[top_3_indices]['horse_name'].values}")
```

---

**Son Güncelleme**: 2026-02-03  
**Model Versiyonu**: 1.0  
**Test Accuracy**: 99.3% (Classification), R²=0.847 (Regression)
