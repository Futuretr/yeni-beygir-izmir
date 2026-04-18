import pandas as pd

df = pd.read_parquet(r'E:\data\ml_program.parquet')

print("TÜM FEATURE DTYPES:")
features = [
    'city_code', 'track_code', 'category_code', 'age_code',
    'jockey_id', 'trainer_id', 'owner_id',
    'distance', 'horse_weight', 'horse_age', 'start_no', 
    'handicap_weight', 'prize_1', 'kgs', 'ganyan', 'agf',
    'horses_per_race', 'has_missing', 'missing_count', 'last_6_wins'
]

for feat in features:
    if feat in df.columns:
        dtype = df[feat].dtype
        print(f"{feat:20s} {str(dtype):15s}", end="")
        if dtype == 'object' or 'string' in str(dtype).lower():
            print(f"  PROBLEM! Sample: {df[feat].dropna().head(1).values}")
        else:
            print()
    else:
        print(f"{feat:20s} KOLONDA YOK!")
