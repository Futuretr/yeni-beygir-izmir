import json
f = open(r'E:\data\idman\082100\82120.json', encoding='utf-8')
d = json.load(f)
print(f"Horse 82120: {d['idman_count']} idman")
print(f"\nAnahtar isimleri: {list(d['idman_records'][0].keys())}")
print("\nİlk 5 idman:")
for r in d['idman_records'][:5]:
    print(f"  {r}")
f.close()
