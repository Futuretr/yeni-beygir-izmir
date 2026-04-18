import pandas as pd

df = pd.read_parquet(r'E:\data\ml_sonuclar.parquet')

print("=" * 80)
print("SONUÇLAR TABLOSU - DERECE BİLGİLERİ")
print("=" * 80)

print("\n📋 TÜÜM SÜTUNLAR:")
for i, col in enumerate(df.columns, 1):
    print(f"{i:2d}. {col}")

print("\n🏁 DERECE BİLGİLERİ:")
print(f"finish_position: {df['finish_position'].dtype}")
print(f"  Sample: {df['finish_position'].dropna().head(10).tolist()}")
print(f"  NaN count: {df['finish_position'].isna().sum()}")

print(f"\nfinish_position_clean: {df['finish_position_clean'].dtype}")
print(f"  Sample: {df['finish_position_clean'].dropna().head(10).tolist()}")
print(f"  NaN count: {df['finish_position_clean'].isna().sum()}")

print("\n📊 DERECE DAĞILIMI:")
print(df['finish_position_clean'].value_counts().sort_index().head(15))

print("\n🎯 İLGİLİ FEATURE'LAR:")
for col in ['is_winner', 'is_top3', 'did_finish', 'ganyan', 'agf']:
    if col in df.columns:
        print(f"{col:20s} {str(df[col].dtype):15s} Sample: {df[col].dropna().head(3).tolist()}")
