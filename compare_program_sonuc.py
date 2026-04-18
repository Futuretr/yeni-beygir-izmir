import pandas as pd

program = pd.read_parquet(r'E:\data\ml_program.parquet')
sonuclar = pd.read_parquet(r'E:\data\ml_sonuclar.parquet')

print("=" * 80)
print("PROGRAM vs SONUÇLAR - FEATURE KARŞILAŞTIRMASI")
print("=" * 80)

program_cols = set(program.columns)
sonuc_cols = set(sonuclar.columns)

# Sadece sonuçlarda olan
only_in_sonuc = sonuc_cols - program_cols
print("\n✅ SADECE SONUÇLARDA OLAN (EKLENEBİLİR):")
for col in sorted(only_in_sonuc):
    if col not in ['is_winner', 'is_top3', 'did_finish', 'finish_position', 'finish_position_clean']:
        sample = sonuclar[col].dropna().head(3).tolist() if len(sonuclar[col].dropna()) > 0 else []
        print(f"  {col:30s} {str(sonuclar[col].dtype):15s} Sample: {sample}")

print("\n❌ TARGET DEĞİŞKENLER (EKLENEMEZ - Data Leakage):")
for col in ['is_winner', 'is_top3', 'did_finish', 'finish_position', 'finish_position_clean']:
    if col in sonuc_cols:
        print(f"  {col:30s} - YARIŞ SONUCU!")

print("\n📊 HER İKİSİNDE DE OLAN:")
both = program_cols & sonuc_cols
print(f"  Toplam {len(both)} ortak sütun")
print(f"  Örnekler: {list(sorted(both))[:10]}")
