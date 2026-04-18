import pandas as pd

df = pd.read_parquet(r'E:\data\ml_program.parquet')

print("STRING/OBJECT FEATURES:")
for col in ['jockey_id', 'trainer_id', 'owner_id', 'has_missing']:
    print(f"\n{col}:")
    print(f"  dtype: {df[col].dtype}")
    print(f"  Sample: {df[col].dropna().head(3).values}")
    print(f"  Unique: {df[col].nunique()}")
