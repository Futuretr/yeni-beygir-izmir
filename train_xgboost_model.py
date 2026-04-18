"""
XGBoost Model Eğitimi ve Feature Importance Analizi
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, classification_report, confusion_matrix
)
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json


class HorseRacingXGBoostModel:
    """At yarışları için XGBoost modeli"""
    
    def __init__(self, task='regression'):
        """
        Parameters:
        -----------
        task : str
            'regression' - Derece tahmini (1, 2, 3, ...)
            'classification' - Top3 tahmini (0/1)
        """
        self.task = task
        self.model = None
        self.feature_names = None
        self.feature_importance = None
        
    def prepare_data(self, df, target_col='last_1_avg_finish', test_size=0.2):
        """Veriyi hazırla"""
        
        print(f"\n{'='*80}")
        print("VERİ HAZIRLAMA")
        print(f"{'='*80}\n")
        
        # Kategorik değişkenleri encode et
        categorical_cols = ['race_city', 'race_track_type', 'horse_name']
        df_processed = df.copy()
        
        for col in categorical_cols:
            if col in df_processed.columns:
                df_processed[col] = pd.Categorical(df_processed[col]).codes
        
        # Target variable oluştur
        if self.task == 'regression':
            # Derece tahmini için - son yarıştaki derecesini tahmin et
            y = df_processed[target_col].fillna(999)
            print(f"Target: {target_col} (Derece tahmini)")
            print(f"  Min: {y.min():.2f}, Max: {y.max():.2f}, Mean: {y.mean():.2f}")
            
        else:  # classification
            # Top 3'e girme tahmini
            y = (df_processed[target_col] <= 3).astype(int)
            print(f"Target: Top 3 Classification")
            print(f"  Top 3 oranı: {y.mean()*100:.2f}%")
            print(f"  Sınıf dağılımı: {y.value_counts().to_dict()}")
        
        # Feature'ları hazırla
        exclude_cols = [
            'horse_id', 'horse_name', 'race_id', 'race_date',
            'last_1_avg_finish', 'last_1_best_finish', 'last_1_worst_finish',
            'last_1_std_finish', 'last_1_avg_time', 'last_1_std_time',
            'last_1_win_rate', 'last_1_top3_rate',
        ]
        
        feature_cols = [col for col in df_processed.columns 
                       if col not in exclude_cols and col != target_col]
        
        X = df_processed[feature_cols]
        
        # Eksik değerleri doldur
        X = X.fillna(0)
        
        # Sonsuz değerleri temizle
        X = X.replace([np.inf, -np.inf], 0)
        
        print(f"\nFeature sayısı: {len(feature_cols)}")
        print(f"Veri sayısı: {len(X)}")
        print(f"Eksik değer: {X.isnull().sum().sum()}")
        
        # Train/Test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        print(f"\nTrain set: {len(X_train)} ({len(X_train)/len(X)*100:.1f}%)")
        print(f"Test set:  {len(X_test)} ({len(X_test)/len(X)*100:.1f}%)")
        
        self.feature_names = feature_cols
        
        return X_train, X_test, y_train, y_test
    
    def train(self, X_train, y_train, params=None):
        """Modeli eğit"""
        
        print(f"\n{'='*80}")
        print("MODEL EĞİTİMİ")
        print(f"{'='*80}\n")
        
        if params is None:
            if self.task == 'regression':
                params = {
                    'objective': 'reg:squarederror',
                    'max_depth': 6,
                    'learning_rate': 0.1,
                    'n_estimators': 200,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,
                    'random_state': 42,
                    'n_jobs': -1
                }
            else:  # classification
                params = {
                    'objective': 'binary:logistic',
                    'max_depth': 6,
                    'learning_rate': 0.1,
                    'n_estimators': 200,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,
                    'random_state': 42,
                    'n_jobs': -1
                }
        
        print("Parametreler:")
        for key, value in params.items():
            print(f"  {key}: {value}")
        
        print("\nEğitim başlıyor...")
        
        if self.task == 'regression':
            self.model = xgb.XGBRegressor(**params)
        else:
            self.model = xgb.XGBClassifier(**params)
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_train, y_train)],
            verbose=False
        )
        
        print("✓ Eğitim tamamlandı!")
        
        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
    
    def evaluate(self, X_test, y_test):
        """Modeli değerlendir"""
        
        print(f"\n{'='*80}")
        print("MODEL DEĞERLENDİRME")
        print(f"{'='*80}\n")
        
        y_pred = self.model.predict(X_test)
        
        if self.task == 'regression':
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_test, y_pred)
            
            print("Regression Metrikleri:")
            print(f"  MAE (Ortalama Mutlak Hata):  {mae:.3f}")
            print(f"  RMSE (Kök Ortalama Kare Hata): {rmse:.3f}")
            print(f"  R² Score: {r2:.3f}")
            
            # Tahmin dağılımı
            print(f"\nTahmin İstatistikleri:")
            print(f"  Min: {y_pred.min():.2f}, Max: {y_pred.max():.2f}")
            print(f"  Mean: {y_pred.mean():.2f}, Std: {y_pred.std():.2f}")
            
            metrics = {
                'mae': mae,
                'rmse': rmse,
                'r2': r2
            }
            
        else:  # classification
            y_pred_binary = (y_pred >= 0.5).astype(int)
            
            acc = accuracy_score(y_test, y_pred_binary)
            
            print("Classification Metrikleri:")
            print(f"  Accuracy: {acc:.3f}")
            print(f"\nClassification Report:")
            print(classification_report(y_test, y_pred_binary, 
                                       target_names=['Not Top3', 'Top3']))
            
            print("\nConfusion Matrix:")
            cm = confusion_matrix(y_test, y_pred_binary)
            print(cm)
            
            metrics = {
                'accuracy': acc,
                'confusion_matrix': cm.tolist()
            }
        
        return metrics, y_pred
    
    def plot_feature_importance(self, top_n=20, save_path=None):
        """Feature importance grafiği"""
        
        plt.figure(figsize=(12, 8))
        
        top_features = self.feature_importance.head(top_n)
        
        plt.barh(range(len(top_features)), top_features['importance'])
        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Importance Score', fontsize=12)
        plt.title(f'Top {top_n} Feature Importance', fontsize=14, fontweight='bold')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"\n✓ Feature importance grafiği kaydedildi: {save_path}")
        
        plt.close()
    
    def plot_predictions(self, y_test, y_pred, save_path=None):
        """Tahmin grafiği"""
        
        if self.task == 'regression':
            plt.figure(figsize=(10, 6))
            
            plt.scatter(y_test, y_pred, alpha=0.5)
            plt.plot([y_test.min(), y_test.max()], 
                    [y_test.min(), y_test.max()], 
                    'r--', lw=2)
            plt.xlabel('Gerçek Değer', fontsize=12)
            plt.ylabel('Tahmin', fontsize=12)
            plt.title('Gerçek vs Tahmin (Regression)', fontsize=14, fontweight='bold')
            plt.tight_layout()
            
        else:  # classification
            from sklearn.metrics import roc_curve, auc
            
            fpr, tpr, _ = roc_curve(y_test, y_pred)
            roc_auc = auc(fpr, tpr)
            
            plt.figure(figsize=(10, 6))
            plt.plot(fpr, tpr, label=f'ROC curve (AUC = {roc_auc:.2f})')
            plt.plot([0, 1], [0, 1], 'k--')
            plt.xlabel('False Positive Rate', fontsize=12)
            plt.ylabel('True Positive Rate', fontsize=12)
            plt.title('ROC Curve', fontsize=14, fontweight='bold')
            plt.legend(loc='lower right')
            plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ Tahmin grafiği kaydedildi: {save_path}")
        
        plt.close()
    
    def save_model(self, path):
        """Modeli kaydet"""
        self.model.save_model(path)
        print(f"\n✓ Model kaydedildi: {path}")
    
    def load_model(self, path):
        """Modeli yükle"""
        if self.task == 'regression':
            self.model = xgb.XGBRegressor()
        else:
            self.model = xgb.XGBClassifier()
        self.model.load_model(path)
        print(f"✓ Model yüklendi: {path}")


def analyze_feature_groups(feature_importance_df):
    """Feature'ları gruplara göre analiz et"""
    
    print(f"\n{'='*80}")
    print("FEATURE GRUP ANALİZİ")
    print(f"{'='*80}\n")
    
    # Feature grupları
    groups = {
        'Son Yarışlar': ['last_3_', 'last_5_', 'last_10_'],
        'Kariyer': ['career_'],
        'Pist/Mesafe': ['track_', 'distance_', 'city_'],
        'Form': ['form_'],
        'Bahis': ['ganyan', 'agf', 'kgs'],
        'Temel': ['horse_age', 'horse_weight', 'handicap', 'total_weight'],
        'İlişkisel': ['jockey_', 'trainer_', 'owner_'],
        'Genetik': ['father_', 'mother_'],
        'Zaman': ['races_last_', 'last_race_days'],
        'Trend': ['trend', 'performance_trend'],
    }
    
    group_importance = {}
    
    for group_name, patterns in groups.items():
        group_features = feature_importance_df[
            feature_importance_df['feature'].apply(
                lambda x: any(p in x for p in patterns)
            )
        ]
        
        if len(group_features) > 0:
            total_importance = group_features['importance'].sum()
            avg_importance = group_features['importance'].mean()
            count = len(group_features)
            
            group_importance[group_name] = {
                'total': total_importance,
                'avg': avg_importance,
                'count': count
            }
    
    # Sıralı göster
    sorted_groups = sorted(group_importance.items(), 
                          key=lambda x: x[1]['total'], 
                          reverse=True)
    
    print(f"{'Grup':<20} {'Feature Sayısı':<15} {'Toplam':<12} {'Ortalama':<12}")
    print("-" * 80)
    
    for group_name, stats in sorted_groups:
        print(f"{group_name:<20} {stats['count']:<15} "
              f"{stats['total']:<12.4f} {stats['avg']:<12.4f}")
    
    return dict(sorted_groups)


def main():
    """Ana fonksiyon"""
    
    print("\n" + "="*80)
    print("XGBOOST MODEL EĞİTİMİ VE FEATURE IMPORTANCE ANALİZİ")
    print("="*80)
    
    # Veriyi yükle
    data_path = Path(r"C:\Users\emir\Desktop\HorseRacingAPI-master\ml_data\ml_features_dataset.csv")
    
    if not data_path.exists():
        print(f"\n❌ Veri dosyası bulunamadı: {data_path}")
        print("Önce 'create_ml_features.py' scriptini çalıştırın!")
        return
    
    print(f"\n📂 Veri yükleniyor: {data_path.name}")
    df = pd.read_csv(data_path)
    print(f"✓ {len(df)} kayıt yüklendi")
    
    # Output dizini
    output_dir = Path(r"C:\Users\emir\Desktop\HorseRacingAPI-master\xgboost_results")
    output_dir.mkdir(exist_ok=True)
    
    # ========================
    # REGRESSION MODEL
    # ========================
    print("\n" + "="*80)
    print("1. REGRESSION MODEL (Derece Tahmini)")
    print("="*80)
    
    model_reg = HorseRacingXGBoostModel(task='regression')
    X_train, X_test, y_train, y_test = model_reg.prepare_data(df)
    model_reg.train(X_train, y_train)
    metrics_reg, y_pred_reg = model_reg.evaluate(X_test, y_test)
    
    # Feature importance
    print(f"\n{'='*80}")
    print("TOP 30 ÖNEMLİ FEATURE'LAR (REGRESSION)")
    print(f"{'='*80}\n")
    print(model_reg.feature_importance.head(30).to_string(index=False))
    
    # Grafik
    model_reg.plot_feature_importance(
        top_n=30,
        save_path=output_dir / 'feature_importance_regression.png'
    )
    
    model_reg.plot_predictions(
        y_test, y_pred_reg,
        save_path=output_dir / 'predictions_regression.png'
    )
    
    # Grup analizi
    group_stats_reg = analyze_feature_groups(model_reg.feature_importance)
    
    # Model kaydet
    model_reg.save_model(output_dir / 'xgboost_regression.json')
    
    # Feature importance CSV
    model_reg.feature_importance.to_csv(
        output_dir / 'feature_importance_regression.csv',
        index=False
    )
    
    # ========================
    # CLASSIFICATION MODEL
    # ========================
    print("\n" + "="*80)
    print("2. CLASSIFICATION MODEL (Top 3 Tahmini)")
    print("="*80)
    
    model_clf = HorseRacingXGBoostModel(task='classification')
    X_train, X_test, y_train, y_test = model_clf.prepare_data(df)
    model_clf.train(X_train, y_train)
    metrics_clf, y_pred_clf = model_clf.evaluate(X_test, y_test)
    
    # Feature importance
    print(f"\n{'='*80}")
    print("TOP 30 ÖNEMLİ FEATURE'LAR (CLASSIFICATION)")
    print(f"{'='*80}\n")
    print(model_clf.feature_importance.head(30).to_string(index=False))
    
    # Grafik
    model_clf.plot_feature_importance(
        top_n=30,
        save_path=output_dir / 'feature_importance_classification.png'
    )
    
    model_clf.plot_predictions(
        y_test, y_pred_clf,
        save_path=output_dir / 'roc_curve_classification.png'
    )
    
    # Grup analizi
    group_stats_clf = analyze_feature_groups(model_clf.feature_importance)
    
    # Model kaydet
    model_clf.save_model(output_dir / 'xgboost_classification.json')
    
    # Feature importance CSV
    model_clf.feature_importance.to_csv(
        output_dir / 'feature_importance_classification.csv',
        index=False
    )
    
    # ========================
    # ÖZET RAPOR
    # ========================
    
    # Convert numpy types to Python types
    def convert_to_json_serializable(obj):
        """Numpy tiplerini Python tiplerine dönüştür"""
        if isinstance(obj, dict):
            return {k: convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    summary = {
        'regression': {
            'metrics': convert_to_json_serializable(metrics_reg),
            'top_features': convert_to_json_serializable(
                model_reg.feature_importance.head(10).to_dict('records')
            ),
            'group_stats': convert_to_json_serializable(group_stats_reg)
        },
        'classification': {
            'metrics': convert_to_json_serializable(metrics_clf),
            'top_features': convert_to_json_serializable(
                model_clf.feature_importance.head(10).to_dict('records')
            ),
            'group_stats': convert_to_json_serializable(group_stats_clf)
        }
    }
    
    # JSON olarak kaydet
    with open(output_dir / 'model_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("TÜM SONUÇLAR")
    print("="*80)
    print(f"\n📁 Sonuçlar kaydedildi: {output_dir}")
    print("\nOluşturulan dosyalar:")
    print("  • feature_importance_regression.png")
    print("  • feature_importance_classification.png")
    print("  • predictions_regression.png")
    print("  • roc_curve_classification.png")
    print("  • feature_importance_regression.csv")
    print("  • feature_importance_classification.csv")
    print("  • xgboost_regression.json (model)")
    print("  • xgboost_classification.json (model)")
    print("  • model_summary.json (özet)")
    
    print(f"\n{'='*80}\n")
    
    return model_reg, model_clf


if __name__ == "__main__":
    model_reg, model_clf = main()
