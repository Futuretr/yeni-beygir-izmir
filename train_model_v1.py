"""
At Yarışı Tahmin Modeli - Profesyonel Yaklaşım
2021-2025 eğitim, 2026 Ocak test
XGBoost, Random Forest, LightGBM karşılaştırması
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("🏇 AT YARIŞI TAHMİN MODELİ - PROFESYONEL")
print("=" * 80)

# Veriyi yükle
print("\n📁 Veriler yükleniyor...")
program = pd.read_parquet(r"E:\data\ml_program.parquet")
sonuclar = pd.read_parquet(r"E:\data\ml_sonuclar.parquet")

print(f"Program: {len(program):,} kayıt")
print(f"Sonuç: {len(sonuclar):,} kayıt")

# Program ve sonuçları birleştir
print("\n🔗 Program ve sonuç birleştiriliyor...")
data = program.merge(
    sonuclar[['race_id', 'horse_id', 'is_winner', 'is_top3', 'finish_position_clean', 'ganyan_numeric']],
    on=['race_id', 'horse_id'],
    how='inner',
    suffixes=('', '_result')
)

print(f"Birleştirilmiş veri: {len(data):,} kayıt")

# Sadece tamamlanmış yarışları al
data_complete = data[data['finish_position_clean'].notna()].copy()
print(f"Tamamlanmış yarışlar: {len(data_complete):,} kayıt")

# Tarih sütununu datetime'a çevir
data_complete['race_date'] = pd.to_datetime(data_complete['race_date'])

# Feature Engineering
print("\n⚙️  Feature Engineering...")

# Yarış başına at sayısı
data_complete['horses_per_race'] = data_complete.groupby('race_id')['horse_id'].transform('count')

# Yaş kategorisi (horse_age string olabilir, numeric'e çevir)
data_complete['horse_age_numeric'] = pd.to_numeric(data_complete['horse_age'], errors='coerce').fillna(0)
data_complete['age_category_code'] = pd.cut(
    data_complete['horse_age_numeric'], 
    bins=[-1, 2, 4, 6, 100], 
    labels=[0, 1, 2, 3]
)
data_complete['age_category_code'] = data_complete['age_category_code'].cat.add_categories([999]).fillna(999).astype(int)

# Mesafe kategorisi (distance string olabilir, numeric'e çevir)
data_complete['distance_numeric'] = pd.to_numeric(data_complete['distance'], errors='coerce').fillna(0)
data_complete['distance_category_code'] = pd.cut(
    data_complete['distance_numeric'],
    bins=[-1, 1200, 1600, 2000, 10000],
    labels=[0, 1, 2, 3]
)
data_complete['distance_category_code'] = data_complete['distance_category_code'].cat.add_categories([999]).fillna(999).astype(int)

# TRAIN-TEST SPLIT (ZAMAN BAZLI)
print("\n" + "=" * 80)
print("✂️  TRAIN-TEST SPLIT (ZAMAN BAZLI)")
print("=" * 80)

# 2021-2025: Eğitim
# 2026 Ocak: Test
train_data = data_complete[data_complete['race_date'] < '2026-01-01'].copy()
test_data = data_complete[data_complete['race_date'] >= '2026-01-01'].copy()

print(f"📚 EĞİTİM SETİ (2021-2025):")
print(f"   Kayıt: {len(train_data):,}")
print(f"   Yarış: {train_data['race_id'].nunique():,}")
print(f"   Kazanan oran: {train_data['is_winner'].mean():.2%}")
print(f"   Tarih aralığı: {train_data['race_date'].min()} - {train_data['race_date'].max()}")

print(f"\n🧪 TEST SETİ (2026 Ocak):")
print(f"   Kayıt: {len(test_data):,}")
print(f"   Yarış: {test_data['race_id'].nunique():,}")
print(f"   Kazanan oran: {test_data['is_winner'].mean():.2%}")
print(f"   Tarih aralığı: {test_data['race_date'].min()} - {test_data['race_date'].max()}")

# Feature seçimi
print("\n📊 Feature seçimi...")

feature_columns = [
    'city_code',
    'track_code',
    'distance_numeric',
    'distance_category_code',
    'age_numeric',
    'age_category_code',
    'jockey_code',
    'trainer_code',
    'owner_code',
    'horse_weight_numeric',
    'handicap_weight_numeric',
    'horses_per_race',
    'prize_1_numeric',
    'race_category_code',
    'age_group_code'
]

# Sadece var olan sütunları kullan
available_features = [f for f in feature_columns if f in data_complete.columns]
print(f"Kullanılacak {len(available_features)} feature")

# X, y hazırlığı
X_train = train_data[available_features].fillna(0)
y_train = train_data['is_winner']

X_test = test_data[available_features].fillna(0)
y_test = test_data['is_winner']

print(f"\nX_train shape: {X_train.shape}")
print(f"X_test shape: {X_test.shape}")

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

print("\nTahmin ediliyor...")
y_pred_rf = rf_model.predict(X_test)
y_pred_proba_rf = rf_model.predict_proba(X_test)[:, 1]

# Metrікler
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

# Class weight hesapla
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

print("\nTahmin ediliyor...")
y_pred_xgb = xgb_model.predict(X_test)
y_pred_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]

# Metrikler
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

print("\nTahmin ediliyor...")
y_pred_lgb = lgb_model.predict(X_test)
y_pred_proba_lgb = lgb_model.predict_proba(X_test)[:, 1]

# Metrikler
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

# Test yarışları
test_races = test_data.copy()
test_races['pred_proba_rf'] = y_pred_proba_rf
test_races['pred_proba_xgb'] = y_pred_proba_xgb
test_races['pred_proba_lgb'] = y_pred_proba_lgb

def calculate_top3_accuracy(df, proba_col):
    """Her yarışta top-3 tahmin içinde kazanan var mı?"""
    results = []
    for race_id in df['race_id'].unique():
        race_data = df[df['race_id'] == race_id].copy()
        # En yüksek 3 tahmine göre sırala
        top3 = race_data.nlargest(3, proba_col)
        # Kazanan top-3'te mi?
        winner_in_top3 = top3['is_winner'].sum() > 0
        results.append(winner_in_top3)
    return np.mean(results)

top3_rf = calculate_top3_accuracy(test_races, 'pred_proba_rf')
top3_xgb = calculate_top3_accuracy(test_races, 'pred_proba_xgb')
top3_lgb = calculate_top3_accuracy(test_races, 'pred_proba_lgb')

print(f"Random Forest TOP-3 Accuracy:  {top3_rf:.4f} ({top3_rf*100:.2f}%)")
print(f"XGBoost TOP-3 Accuracy:        {top3_xgb:.4f} ({top3_xgb*100:.2f}%)")
print(f"LightGBM TOP-3 Accuracy:       {top3_lgb:.4f} ({top3_lgb*100:.2f}%)")

# KARŞILAŞTIRMA TABLOSU
print("\n" + "=" * 80)
print("📊 GENEL KARŞILAŞTIRMA")
print("=" * 80)

comparison = pd.DataFrame({
    'Model': ['Random Forest', 'XGBoost', 'LightGBM'],
    'Accuracy': [accuracy_rf, accuracy_xgb, accuracy_lgb],
    'Precision': [precision_rf, precision_xgb, precision_lgb],
    'Recall': [recall_rf, recall_xgb, recall_lgb],
    'F1': [f1_rf, f1_xgb, f1_lgb],
    'TOP-3 Acc': [top3_rf, top3_xgb, top3_lgb]
})

print(comparison.to_string(index=False))

# En iyi modeli belirle
best_model_idx = comparison['TOP-3 Acc'].idxmax()
best_model_name = comparison.loc[best_model_idx, 'Model']
best_top3 = comparison.loc[best_model_idx, 'TOP-3 Acc']

print(f"\n🏆 EN İYİ MODEL: {best_model_name} (TOP-3: {best_top3*100:.2f}%)")

# Feature Importance
print("\n" + "=" * 80)
print("⭐ EN ÖNEMLİ FEATURE'LAR (XGBoost)")
print("=" * 80)

feature_importance = pd.DataFrame({
    'feature': available_features,
    'importance': xgb_model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in feature_importance.head(15).iterrows():
    bar = '█' * int(row['importance'] * 50)
    print(f"  {row['feature']:<25} {bar} {row['importance']:.4f}")

# Modelleri kaydet
import joblib
print("\n💾 Modeller kaydediliyor...")
joblib.dump(rf_model, r"E:\data\rf_model_v1.pkl")
joblib.dump(xgb_model, r"E:\data\xgb_model_v1.pkl")
joblib.dump(lgb_model, r"E:\data\lgb_model_v1.pkl")
joblib.dump(available_features, r"E:\data\model_features.pkl")
comparison.to_csv(r"E:\data\model_comparison.csv", index=False)

print("✅ Kaydedildi: E:\\data\\")
print("\n" + "=" * 80)
print("✅ EĞİTİM TAMAMLANDI!")
print("=" * 80)

print(f"Birleştirilmiş veri: {len(data):,} kayıt")
print(f"Unique yarışlar: {data['race_id'].nunique():,}")

# Sadece tamamlanmış yarışları al (finish_position_clean boş olmayanlar)
data_complete = data[data['finish_position_clean'].notna()].copy()
print(f"Tamamlanmış yarışlar: {len(data_complete):,} kayıt")

# Feature Engineering
print("\n⚙️  Feature Engineering...")

# Yarış başına at sayısı
data_complete['horses_per_race'] = data_complete.groupby('race_id')['horse_id'].transform('count')

# At yaşı kategorisi
data_complete['age_category'] = pd.cut(
    data_complete['age_numeric'], 
    bins=[0, 2, 4, 6, 100], 
    labels=['genç', 'orta', 'tecrübeli', 'yaşlı']
).astype(str)

# Mesafe kategorisi
data_complete['distance_category'] = pd.cut(
    data_complete['distance_numeric'],
    bins=[0, 1200, 1600, 2000, 10000],
    labels=['kısa', 'orta', 'uzun', 'çok_uzun']
).astype(str)

# Label encode yeni kategorikler
from sklearn.preprocessing import LabelEncoder
le_age = LabelEncoder()
le_dist = LabelEncoder()

data_complete['age_category_code'] = le_age.fit_transform(data_complete['age_category'])
data_complete['distance_category_code'] = le_dist.fit_transform(data_complete['distance_category'])

# Feature seçimi
print("\n📊 Feature seçimi...")

feature_columns = [
    'city_code',
    'track_code',
    'distance_numeric',
    'distance_category_code',
    'age_numeric',
    'age_category_code',
    'jockey_code',
    'trainer_code',
    'owner_code',
    'horse_weight_numeric',
    'handicap_weight_numeric',
    'horses_per_race',
    'prize_1_numeric',
    'race_category_code',
    'age_group_code'
]

# Sadece var olan sütunları kullan
available_features = [f for f in feature_columns if f in data_complete.columns]
print(f"Kullanılacak feature'lar ({len(available_features)}):")
for f in available_features:
    print(f"  - {f}")

# NaN'ları doldur
X = data_complete[available_features].fillna(0)
y = data_complete['is_winner']  # 1 = kazanan, 0 = kaybeden

print(f"\nVeri boyutu: {X.shape}")
print(f"Kazanan at oranı: {y.mean():.2%}")

# Train/Test split
print("\n✂️  Train/Test split...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Train: {len(X_train):,} kayıt")
print(f"Test: {len(X_test):,} kayıt")

# Model 1: Random Forest
print("\n" + "=" * 80)
print("🌲 RANDOM FOREST MODELİ")
print("=" * 80)

rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=50,
    min_samples_leaf=20,
    random_state=42,
    n_jobs=-1,
    class_weight='balanced'
)

print("Eğitiliyor...")
rf_model.fit(X_train, y_train)

print("Tahmin ediliyor...")
y_pred_rf = rf_model.predict(X_test)
y_pred_proba_rf = rf_model.predict_proba(X_test)[:, 1]

accuracy_rf = accuracy_score(y_test, y_pred_rf)
print(f"\n✅ Test Accuracy: {accuracy_rf:.4f} ({accuracy_rf*100:.2f}%)")

print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred_rf, target_names=['Kaybeden', 'Kazanan']))

# Feature importance
print("\n⭐ En Önemli Feature'lar:")
feature_importance = pd.DataFrame({
    'feature': available_features,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in feature_importance.head(10).iterrows():
    print(f"  {row['feature']}: {row['importance']:.4f}")

# Model 2: Gradient Boosting
print("\n" + "=" * 80)
print("🚀 GRADIENT BOOSTING MODELİ")
print("=" * 80)

gb_model = GradientBoostingClassifier(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    min_samples_split=50,
    min_samples_leaf=20,
    random_state=42
)

print("Eğitiliyor...")
gb_model.fit(X_train, y_train)

print("Tahmin ediliyor...")
y_pred_gb = gb_model.predict(X_test)
y_pred_proba_gb = gb_model.predict_proba(X_test)[:, 1]

accuracy_gb = accuracy_score(y_test, y_pred_gb)
print(f"\n✅ Test Accuracy: {accuracy_gb:.4f} ({accuracy_gb*100:.2f}%)")

print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred_gb, target_names=['Kaybeden', 'Kazanan']))

# Yarış bazında değerlendirme
print("\n" + "=" * 80)
print("🏁 YARIŞ BAZINDA DEĞERLENDİRME")
print("=" * 80)

# Test setindeki yarışları al
test_races = data_complete.loc[X_test.index]
test_races['pred_proba_rf'] = y_pred_proba_rf
test_races['pred_proba_gb'] = y_pred_proba_gb

# Her yarış için en yüksek tahmin skorlu atı seç
race_predictions_rf = test_races.groupby('race_id').apply(
    lambda x: x.nlargest(1, 'pred_proba_rf')['is_winner'].iloc[0]
).reset_index(name='predicted_winner')

race_predictions_gb = test_races.groupby('race_id').apply(
    lambda x: x.nlargest(1, 'pred_proba_gb')['is_winner'].iloc[0]
).reset_index(name='predicted_winner')

race_accuracy_rf = race_predictions_rf['predicted_winner'].mean()
race_accuracy_gb = race_predictions_gb['predicted_winner'].mean()

print(f"Random Forest - Yarış bazında başarı: {race_accuracy_rf:.4f} ({race_accuracy_rf*100:.2f}%)")
print(f"Gradient Boosting - Yarış bazında başarı: {race_accuracy_gb:.4f} ({race_accuracy_gb*100:.2f}%)")

print("\n" + "=" * 80)
print("✅ MODEL EĞİTİMİ TAMAMLANDI")
print("=" * 80)

# Model kaydet
import joblib
print("\n💾 Modeller kaydediliyor...")
joblib.dump(rf_model, r"E:\data\rf_model_v1.pkl")
joblib.dump(gb_model, r"E:\data\gb_model_v1.pkl")
joblib.dump(available_features, r"E:\data\model_features.pkl")
print("✅ Modeller kaydedildi: E:\\data\\")
