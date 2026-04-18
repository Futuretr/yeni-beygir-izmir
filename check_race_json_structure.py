import json
import os

# İzmir 2026'dan birkaç dosya kontrol edelim
json_dir = "E:/data/race_jsons/Izmir/2026"

files = [f for f in os.listdir(json_dir) if f.endswith('.json')][:3]

for fname in files:
    fpath = os.path.join(json_dir, fname)
    print(f"\n{'='*80}")
    print(f"Dosya: {fname}")
    print('='*80)
    
    with open(fpath, encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Tip: {type(data)}")
    
    if isinstance(data, list):
        print(f"Liste uzunluğu: {len(data)}")
        if len(data) > 0:
            print(f"İlk eleman: {data[0].keys() if isinstance(data[0], dict) else type(data[0])}")
            if isinstance(data[0], dict):
                for key, val in list(data[0].items())[:5]:
                    print(f"  {key}: {val}")
    elif isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        for key, val in list(data.items())[:10]:
            if key == 'horses' and isinstance(val, list):
                print(f"  {key}: {len(val)} at")
            else:
                print(f"  {key}: {val}")
