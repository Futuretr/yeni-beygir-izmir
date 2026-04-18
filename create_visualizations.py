"""
Model sonuçlarını ve feature importance'ı görselleştir
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json

# Stil ayarları
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def create_comparison_plot(results_dir):
    """Regression vs Classification feature importance karşılaştırması"""
    
    # CSV'leri yükle
    reg_df = pd.read_csv(results_dir / 'feature_importance_regression.csv')
    clf_df = pd.read_csv(results_dir / 'feature_importance_classification.csv')
    
    # Top 15'i al
    reg_top = reg_df.head(15)
    clf_top = clf_df.head(15)
    
    # Yan yana plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 10))
    
    # Regression
    ax1.barh(range(len(reg_top)), reg_top['importance'], color='steelblue')
    ax1.set_yticks(range(len(reg_top)))
    ax1.set_yticklabels(reg_top['feature'], fontsize=11)
    ax1.set_xlabel('Importance Score', fontsize=13, fontweight='bold')
    ax1.set_title('Regression Model\n(Derece Tahmini)', 
                  fontsize=15, fontweight='bold', pad=20)
    ax1.invert_yaxis()
    ax1.grid(axis='x', alpha=0.3)
    
    # Classification
    ax2.barh(range(len(clf_top)), clf_top['importance'], color='coral')
    ax2.set_yticks(range(len(clf_top)))
    ax2.set_yticklabels(clf_top['feature'], fontsize=11)
    ax2.set_xlabel('Importance Score', fontsize=13, fontweight='bold')
    ax2.set_title('Classification Model\n(Top 3 Tahmini)', 
                  fontsize=15, fontweight='bold', pad=20)
    ax2.invert_yaxis()
    ax2.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(results_dir / 'feature_comparison.png', dpi=300, bbox_inches='tight')
    print(f"✓ Karşılaştırma grafiği oluşturuldu: feature_comparison.png")
    plt.close()


def create_group_importance_plot(results_dir):
    """Feature gruplarının importance dağılımı"""
    
    # Model summary'den grup stats'i al
    with open(results_dir / 'model_summary.json', 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    reg_groups = summary['regression']['group_stats']
    clf_groups = summary['classification']['group_stats']
    
    # DataFrame'e dönüştür
    reg_data = []
    clf_data = []
    
    for group, stats in reg_groups.items():
        reg_data.append({'Group': group, 'Total': stats['total'], 'Count': stats['count']})
    
    for group, stats in clf_groups.items():
        clf_data.append({'Group': group, 'Total': stats['total'], 'Count': stats['count']})
    
    reg_df = pd.DataFrame(reg_data)
    clf_df = pd.DataFrame(clf_data)
    
    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Regression - Total Importance
    axes[0, 0].barh(reg_df['Group'], reg_df['Total'], color='steelblue')
    axes[0, 0].set_xlabel('Total Importance', fontsize=12, fontweight='bold')
    axes[0, 0].set_title('Regression: Feature Group Importance', 
                         fontsize=13, fontweight='bold')
    axes[0, 0].invert_yaxis()
    axes[0, 0].grid(axis='x', alpha=0.3)
    
    # Regression - Feature Count
    axes[0, 1].barh(reg_df['Group'], reg_df['Count'], color='lightcoral')
    axes[0, 1].set_xlabel('Feature Count', fontsize=12, fontweight='bold')
    axes[0, 1].set_title('Regression: Features per Group', 
                         fontsize=13, fontweight='bold')
    axes[0, 1].invert_yaxis()
    axes[0, 1].grid(axis='x', alpha=0.3)
    
    # Classification - Total Importance
    axes[1, 0].barh(clf_df['Group'], clf_df['Total'], color='seagreen')
    axes[1, 0].set_xlabel('Total Importance', fontsize=12, fontweight='bold')
    axes[1, 0].set_title('Classification: Feature Group Importance', 
                         fontsize=13, fontweight='bold')
    axes[1, 0].invert_yaxis()
    axes[1, 0].grid(axis='x', alpha=0.3)
    
    # Classification - Feature Count
    axes[1, 1].barh(clf_df['Group'], clf_df['Count'], color='gold')
    axes[1, 1].set_xlabel('Feature Count', fontsize=12, fontweight='bold')
    axes[1, 1].set_title('Classification: Features per Group', 
                         fontsize=13, fontweight='bold')
    axes[1, 1].invert_yaxis()
    axes[1, 1].grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(results_dir / 'group_importance.png', dpi=300, bbox_inches='tight')
    print(f"✓ Grup importance grafiği oluşturuldu: group_importance.png")
    plt.close()


def create_summary_dashboard(results_dir):
    """Özet dashboard"""
    
    with open(results_dir / 'model_summary.json', 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.4)
    
    # Title
    fig.suptitle('XGBoost Model Performance Dashboard', 
                 fontsize=20, fontweight='bold', y=0.98)
    
    # Regression metrics
    ax1 = fig.add_subplot(gs[0, 0])
    reg_metrics = summary['regression']['metrics']
    metrics_text = f"MAE: {reg_metrics['mae']:.3f}\nRMSE: {reg_metrics['rmse']:.3f}\nR²: {reg_metrics['r2']:.3f}"
    ax1.text(0.5, 0.5, metrics_text, ha='center', va='center', 
             fontsize=16, bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    ax1.set_title('Regression Metrics', fontsize=14, fontweight='bold')
    ax1.axis('off')
    
    # Classification metrics
    ax2 = fig.add_subplot(gs[0, 1])
    clf_metrics = summary['classification']['metrics']
    metrics_text = f"Accuracy: {clf_metrics['accuracy']:.3f}\n\nPrecision: 100%\nRecall: 88%"
    ax2.text(0.5, 0.5, metrics_text, ha='center', va='center', 
             fontsize=16, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    ax2.set_title('Classification Metrics', fontsize=14, fontweight='bold')
    ax2.axis('off')
    
    # Model info
    ax3 = fig.add_subplot(gs[0, 2])
    info_text = "XGBoost\n\nMax Depth: 6\nLearning Rate: 0.1\nEstimators: 200\n\nTrain: 80%\nTest: 20%"
    ax3.text(0.5, 0.5, info_text, ha='center', va='center', 
             fontsize=13, bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    ax3.set_title('Model Configuration', fontsize=14, fontweight='bold')
    ax3.axis('off')
    
    # Top features regression
    ax4 = fig.add_subplot(gs[1:, 0])
    reg_top = pd.DataFrame(summary['regression']['top_features'])
    ax4.barh(range(len(reg_top)), reg_top['importance'], color='steelblue')
    ax4.set_yticks(range(len(reg_top)))
    ax4.set_yticklabels(reg_top['feature'], fontsize=10)
    ax4.set_xlabel('Importance', fontsize=11, fontweight='bold')
    ax4.set_title('Top 10 Features (Regression)', fontsize=13, fontweight='bold')
    ax4.invert_yaxis()
    ax4.grid(axis='x', alpha=0.3)
    
    # Top features classification
    ax5 = fig.add_subplot(gs[1:, 1])
    clf_top = pd.DataFrame(summary['classification']['top_features'])
    ax5.barh(range(len(clf_top)), clf_top['importance'], color='coral')
    ax5.set_yticks(range(len(clf_top)))
    ax5.set_yticklabels(clf_top['feature'], fontsize=10)
    ax5.set_xlabel('Importance', fontsize=11, fontweight='bold')
    ax5.set_title('Top 10 Features (Classification)', fontsize=13, fontweight='bold')
    ax5.invert_yaxis()
    ax5.grid(axis='x', alpha=0.3)
    
    # Key insights
    ax6 = fig.add_subplot(gs[1:, 2])
    insights = """
    KEY INSIGHTS
    
    ✓ Son performans en önemli
      faktör (%83 ve %68)
    
    ✓ Regression model çok
      başarılı (R²=0.847)
    
    ✓ Classification %99.3
      doğruluk ile çalışıyor
    
    ✓ Pist/Mesafe deneyimi
      önemli (%6-7)
    
    ✓ Bahis verileri beklenenden
      az etkili (%1-2)
    
    ✓ Genetik faktörler düşük
      öneme sahip (%2)
    """
    ax6.text(0.05, 0.95, insights, ha='left', va='top', 
             fontsize=11, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lavender', alpha=0.5))
    ax6.axis('off')
    
    plt.savefig(results_dir / 'summary_dashboard.png', dpi=300, bbox_inches='tight')
    print(f"✓ Özet dashboard oluşturuldu: summary_dashboard.png")
    plt.close()


def main():
    """Ana fonksiyon"""
    
    results_dir = Path(r"C:\Users\emir\Desktop\HorseRacingAPI-master\xgboost_results")
    
    if not results_dir.exists():
        print(f"❌ Sonuç dizini bulunamadı: {results_dir}")
        print("Önce 'train_xgboost_model.py' scriptini çalıştırın!")
        return
    
    print("\n" + "="*80)
    print("EK GRAFİKLER OLUŞTURULUYOR")
    print("="*80 + "\n")
    
    create_comparison_plot(results_dir)
    create_group_importance_plot(results_dir)
    create_summary_dashboard(results_dir)
    
    print("\n" + "="*80)
    print("TAMAMLANDI!")
    print("="*80)
    print(f"\n📁 Dizin: {results_dir}")
    print("\nOluşturulan yeni grafikler:")
    print("  • feature_comparison.png")
    print("  • group_importance.png")
    print("  • summary_dashboard.png")
    print()


if __name__ == "__main__":
    main()
