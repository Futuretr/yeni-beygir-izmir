"""
At Yarışı Tahmin Modeli - Profesyonel
2021-2025 eğitim, 2026 Ocak test
XGBoost, Random Forest, LightGBM karşılaştırması
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("🏇 AT YARIŞI TAHMİN MODELİ - PROFESYONEL")
print("=" * 80)

# Veriyi yükle
print("\n📁 Veriler yükleniyor...")
program = pd.read_parquet(r"E:\data\ml_program.parquet")
sonuclar = pd.read_parquet(r"E:\data\ml_sonuclar.parquet")
time_data = pd.read_parquet(r"E:\data\ml_time.parquet")

print(f"Program: {len(program):,} kayıt")
print(f"Sonuç: {len(sonuclar):,} kayıt")
print(f"Time: {len(time_data):,} kayıt")

# Program ve sonuçları birleştir
print("\n🔗 Program ve sonuç birleştiriliyor...")
data = program.merge(
    sonuclar[['race_id', 'horse_id', 'is_winner', 'is_top3', 'finish_position_clean']],
    on=['race_id', 'horse_id'],
    how='inner',
    suffixes=('', '_result')
)

print(f"Birleştirilmiş veri: {len(data):,} kayıt")

# Time verilerini ekle
print("\n⏱️  Time verileri ekleniyor...")
time_features = time_data[['race_id', 'horse_id', 'did_finish', 
                           'horse_avg_time', 'horse_min_time', 'horse_max_time',
                           'horse_std_time', 'horse_race_count',
                           'horse_capacity_usage', 'horse_time_consistency', 
                           'horse_best_vs_avg_ratio', 'horse_time_zscore',
                           'horse_vs_race_avg', 'horse_vs_race_best', 'experience_level']]

data = data.merge(
    time_features,
    on=['race_id', 'horse_id'],
    how='left',
    suffixes=('', '_time')
)

print(f"Time eklenmiş veri: {len(data):,} kayıt")

# 🆕 HIZ HESAPLAMA (distance / horse_avg_time)
print("\n🚀 Hız hesaplanıyor...")
data['horse_avg_speed'] = data['distance'] / (data['horse_avg_time'] + 0.1)  # m/s
data['horse_best_speed'] = data['distance'] / (data['horse_min_time'] + 0.1)  # m/s

# 🆕 Mesafe bazında normalize edilmiş süre
data['time_per_km'] = (data['horse_avg_time'] / (data['distance'] / 1000.0)).fillna(0)  # saniye/km

# Sadece tamamlanmış yarışları al
data_complete = data[data['finish_position_clean'].notna()].copy()
print(f"Tamamlanmış yarışlar: {len(data_complete):,} kayıt")

# Tarih sütununu datetime'a çevir
data_complete['race_date'] = pd.to_datetime(data_complete['race_date'])

# Feature Engineering
print("\n⚙️  Feature Engineering...")

# Yarış başına at sayısı
data_complete['horses_per_race'] = data_complete.groupby('race_id')['horse_id'].transform('count')

# Last 6 races'den kazanma sayısı (eğer JSON ise parse et, değilse 0)
data_complete['last_6_wins'] = 0  # Basit versiyon - şimdilik 0

# TRAIN-TEST SPLIT (ZAMAN BAZLI)
print("\n" + "=" * 80)
print("✂️  TRAIN-TEST SPLIT (ZAMAN BAZLI)")
print("=" * 80)

# 2021-2025: Eğitim, 2026 Ocak: Test
train_data = data_complete[data_complete['race_date'] < '2026-01-01'].copy()
test_data = data_complete[data_complete['race_date'] >= '2026-01-01'].copy()

print(f"📚 EĞİTİM SETİ (2021-2025):")
print(f"   Kayıt: {len(train_data):,}")
print(f"   Yarış: {train_data['race_id'].nunique():,}")
print(f"   Kazanan oran: {train_data['is_winner'].mean():.2%}")
print(f"   Tarih: {train_data['race_date'].min().date()} - {train_data['race_date'].max().date()}")

print(f"\n🧪 TEST SETİ (2026 Ocak):")
print(f"   Kayıt: {len(test_data):,}")
print(f"   Yarış: {test_data['race_id'].nunique():,}")
print(f"   Kazanan oran: {test_data['is_winner'].mean():.2%}")
print(f"   Tarih: {test_data['race_date'].min().date()} - {test_data['race_date'].max().date()}")

# Feature seçimi - PROFESYONELTüm yeni özellikler!
feature_columns = [
    # Categorical (ID kodları)
    'city_code',
    'track_code',
    'category_code',      # DERECE!
    'age_code',
    # 'jockey_id',        # ID yerine win rate kullanacağız
    # 'trainer_id',       # ID yerine win rate kullanacağız
    # 'owner_id',         # ID yerine win rate kullanacağız
    
    # Numeric (Sayısal)
    'distance',           # Mesafe
    'horse_weight',       # At ağırlığı
    'horse_age',          # At yaşı
    'start_no',           # Start numarası
    'handicap_weight',    # Handikap ağırlığı
    'prize_1',            # Ödül miktarı
    'kgs',                # KGS puanı
    
    # 🆕 WIN RATES (ID'ler yerine!)
    'jockey_win_rate',    # Jokey başarı oranı
    'trainer_win_rate',   # Antrenör başarı oranı
    'owner_win_rate',     # Sahip başarı oranı
    'jockey_races',       # Jokey tecrübesi
    'trainer_races',      # Antrenör tecrübesi
    
    # TIME Features - PROFESYONEL NORMALIZASYON!
    'horse_avg_time',           # Atın geçmiş ortalama süresi
    'horse_min_time',           # Atın geçmiş en iyi süresi
    'horse_max_time',           # Atın geçmiş en kötü süresi
    'horse_std_time',           # Atın süre tutarlılığı (std)
    'horse_race_count',         # Atın toplam yarış sayısı
    'horse_capacity_usage',     # 🆕 Kapasite kullanımı (min/avg)
    'horse_time_consistency',   # 🆕 Tutarlılık skoru (0-1)
    'horse_best_vs_avg_ratio',  # 🆕 En iyi/Ortalama oranı
    'horse_time_zscore',        # 🆕 Z-Score (pist bazında normalize)
    'horse_vs_race_avg',        # 🆕 Bu yarıştaki rakiplere göre
    'horse_vs_race_best',       # 🆕 Bu yarışın en iyi atına göre
    'experience_level',         # 🆕 Tecrübe seviyesi (0-3)
    'horse_avg_speed',          # 🆕 HIZ (m/s) - MESAFE BAĞIMSIZ!
    'horse_best_speed',         # 🆕 En iyi hız (m/s)
    'time_per_km',              # 🆕 KM başına süre
    
    # Engineered
    'horses_per_race',    # Yarıştaki at sayısı
    'has_missing',        # Eksik veri var mı
    'missing_count',      # Eksik veri sayısı
    'last_6_wins'         # Son 6 yarış kazanma sayısı
]

# Sadece var olan sütunları kullan (ve duplicate'ları kaldır)
available_features = list(dict.fromkeys([f for f in feature_columns if f in data_complete.columns]))
print(f"\n📊 {len(available_features)} feature kullanılacak:")
for f in available_features:
    print(f"  - {f}")

# X, y hazırlığı - String/categorical kolonları numeric'e çevir
X_train = train_data[available_features].copy()
X_test = test_data[available_features].copy()

# String/categorical kolonları numeric'e çevir
for col in X_train.columns:
    dtype_str = str(X_train[col].dtype)
    
    # String veya categorical ise numeric'e çevir
    if dtype_str in ['object', 'str', 'string', 'category'] or 'string' in dtype_str.lower():
        # Önce kategori kodlarına çevir
        X_train[col] = pd.Categorical(X_train[col].fillna('MISSING')).codes
        X_test[col] = pd.Categorical(X_test[col].fillna('MISSING')).codes
    # Int64 tipindeki kolonları float'a çevir
    elif dtype_str == 'Int64':
        X_train[col] = X_train[col].fillna(0).astype(float)
        X_test[col] = X_test[col].fillna(0).astype(float)

# Tüm NaN'ları 0 yap ve float'a çevir
X_train = X_train.fillna(0).astype(float)
X_test = X_test.fillna(0).astype(float)

y_train = train_data['is_winner'].astype(int)
y_test = test_data['is_winner'].astype(int)

print(f"\nX_train: {X_train.shape}")
print(f"X_test: {X_test.shape}")

# MODEL 1: RANDOM FOREST
print("\n" + "=" * 80)
print("🌲 MODEL 1: RANDOM FOREST")
print("=" * 80)

rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=50,
    min_samples_leaf=20,
    random_state=42,
    n_jobs=-1,
    class_weight='balanced',
    verbose=1
)

print("Eğitiliyor...")
rf_model.fit(X_train, y_train)

print("Tahmin ediliyor...")
y_pred_rf = rf_model.predict(X_test)
y_pred_proba_rf = rf_model.predict_proba(X_test)[:, 1]

accuracy_rf = accuracy_score(y_test, y_pred_rf)
precision_rf = precision_score(y_test, y_pred_rf, zero_division=0)
recall_rf = recall_score(y_test, y_pred_rf, zero_division=0)
f1_rf = f1_score(y_test, y_pred_rf, zero_division=0)

print(f"\n📊 SONUÇLAR:")
print(f"  Accuracy:  {accuracy_rf:.4f} ({accuracy_rf*100:.2f}%)")
print(f"  Precision: {precision_rf:.4f} ({precision_rf*100:.2f}%) - 'Kazanır' dediğinin kaçı kazandı")
print(f"  Recall:    {recall_rf:.4f} ({recall_rf*100:.2f}%) - Kazananların kaçını bulduk")
print(f"  F1 Score:  {f1_rf:.4f}")

# MODEL 2: XGBOOST
print("\n" + "=" * 80)
print("🚀 MODEL 2: XGBOOST (Bill Benter'ın Modern Silahı)")
print("=" * 80)

scale_pos_weight = len(y_train[y_train == 0]) / len(y_train[y_train == 1])

xgb_model = XGBClassifier(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    min_child_weight=5,
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    n_jobs=-1,
    verbosity=1
)

print(f"Scale pos weight: {scale_pos_weight:.2f}")
print("Eğitiliyor...")
xgb_model.fit(X_train, y_train)

print("Tahmin ediliyor...")
y_pred_xgb = xgb_model.predict(X_test)
y_pred_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]

accuracy_xgb = accuracy_score(y_test, y_pred_xgb)
precision_xgb = precision_score(y_test, y_pred_xgb, zero_division=0)
recall_xgb = recall_score(y_test, y_pred_xgb, zero_division=0)
f1_xgb = f1_score(y_test, y_pred_xgb, zero_division=0)

print(f"\n📊 SONUÇLAR:")
print(f"  Accuracy:  {accuracy_xgb:.4f} ({accuracy_xgb*100:.2f}%)")
print(f"  Precision: {precision_xgb:.4f} ({precision_xgb*100:.2f}%)")
print(f"  Recall:    {recall_xgb:.4f} ({recall_xgb*100:.2f}%)")
print(f"  F1 Score:  {f1_xgb:.4f}")

# MODEL 3: LIGHTGBM
print("\n" + "=" * 80)
print("⚡ MODEL 3: LIGHTGBM (Hız Canavarı)")
print("=" * 80)

lgb_model = LGBMClassifier(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    num_leaves=31,
    min_child_samples=20,
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    n_jobs=-1,
    verbose=1
)

print("Eğitiliyor...")
lgb_model.fit(X_train, y_train)

print("Tahmin ediliyor...")
y_pred_lgb = lgb_model.predict(X_test)
y_pred_proba_lgb = lgb_model.predict_proba(X_test)[:, 1]

accuracy_lgb = accuracy_score(y_test, y_pred_lgb)
precision_lgb = precision_score(y_test, y_pred_lgb, zero_division=0)
recall_lgb = recall_score(y_test, y_pred_lgb, zero_division=0)
f1_lgb = f1_score(y_test, y_pred_lgb, zero_division=0)

print(f"\n📊 SONUÇLAR:")
print(f"  Accuracy:  {accuracy_lgb:.4f} ({accuracy_lgb*100:.2f}%)")
print(f"  Precision: {precision_lgb:.4f} ({precision_lgb*100:.2f}%)")
print(f"  Recall:    {recall_lgb:.4f} ({recall_lgb*100:.2f}%)")
print(f"  F1 Score:  {f1_lgb:.4f}")

# YARIŞ BAZINDA TOP-3 ACCURACY
print("\n" + "=" * 80)
print("🏁 YARIŞ BAZINDA TOP-3 ACCURACY (SENİN %70 HEDEFİN)")
print("=" * 80)

test_races = test_data.copy()
test_races['pred_proba_rf'] = y_pred_proba_rf
test_races['pred_proba_xgb'] = y_pred_proba_xgb
test_races['pred_proba_lgb'] = y_pred_proba_lgb

def calculate_top3_accuracy(df, proba_col):
    """Her yarışta top-3 tahmin içinde kazanan var mı?"""
    results = []
    for race_id in df['race_id'].unique():
        race_data = df[df['race_id'] == race_id].copy()
        top3 = race_data.nlargest(3, proba_col)
        winner_in_top3 = top3['is_winner'].sum() > 0
        results.append(winner_in_top3)
    return np.mean(results)

top3_rf = calculate_top3_accuracy(test_races, 'pred_proba_rf')
top3_xgb = calculate_top3_accuracy(test_races, 'pred_proba_xgb')
top3_lgb = calculate_top3_accuracy(test_races, 'pred_proba_lgb')

print(f"Random Forest TOP-3 Accuracy:  {top3_rf:.4f} ({top3_rf*100:.2f}%)")
print(f"XGBoost TOP-3 Accuracy:        {top3_xgb:.4f} ({top3_xgb*100:.2f}%)")
print(f"LightGBM TOP-3 Accuracy:       {top3_lgb:.4f} ({top3_lgb*100:.2f}%)")

# KARŞILAŞTIRMA
print("\n" + "=" * 80)
print("📊 GENEL KARŞILAŞTIRMA")
print("=" * 80)

comparison = pd.DataFrame({
    'Model': ['Random Forest', 'XGBoost', 'LightGBM'],
    'Accuracy': [f'{accuracy_rf:.4f}', f'{accuracy_xgb:.4f}', f'{accuracy_lgb:.4f}'],
    'Precision': [f'{precision_rf:.4f}', f'{precision_xgb:.4f}', f'{precision_lgb:.4f}'],
    'Recall': [f'{recall_rf:.4f}', f'{recall_xgb:.4f}', f'{recall_lgb:.4f}'],
    'F1': [f'{f1_rf:.4f}', f'{f1_xgb:.4f}', f'{f1_lgb:.4f}'],
    'TOP-3 Acc': [f'{top3_rf:.4f}', f'{top3_xgb:.4f}', f'{top3_lgb:.4f}']
})

print(comparison.to_string(index=False))

best_top3 = max(top3_rf, top3_xgb, top3_lgb)
best_model = ['Random Forest', 'XGBoost', 'LightGBM'][[top3_rf, top3_xgb, top3_lgb].index(best_top3)]
print(f"\n🏆 EN İYİ MODEL: {best_model} (TOP-3: {best_top3*100:.2f}%)")

# Feature Importance
print("\n" + "=" * 80)
print("⭐ EN ÖNEMLİ FEATURE'LAR (XGBoost)")
print("=" * 80)

feature_importance = pd.DataFrame({
    'feature': available_features,
    'importance': xgb_model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in feature_importance.head(10).iterrows():
    bar = '█' * int(row['importance'] * 50)
    print(f"  {row['feature']:<20} {bar} {row['importance']:.4f}")

# Modelleri kaydet
import joblib
print("\n💾 Modeller kaydediliyor...")
joblib.dump(rf_model, r"E:\data\rf_model_v1.pkl")
joblib.dump(xgb_model, r"E:\data\xgb_model_v1.pkl")
joblib.dump(lgb_model, r"E:\data\lgb_model_v1.pkl")
joblib.dump(available_features, r"E:\data\model_features.pkl")
comparison.to_csv(r"E:\data\model_comparison.csv", index=False)

print("✅ Kaydedildi!")
print("\n" + "=" * 80)
print("✅ EĞİTİM TAMAMLANDI!")
print("=" * 80)
