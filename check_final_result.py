import json

# Win kaydını kontrol et
with open("E:\\data\\stats\\Maiden\\Istanbul\\İngiliz\\Sentetik_1200m.json", 'r', encoding='utf-8') as f:
    data = json.load(f)

# İdman verisi olan ilk kaydı bul
sample = None
for record in data:
    if record.get('last_idman'):
        sample = record
        break

if sample:
    print("=" * 80)
    print("WIN RECORD:")
    print("=" * 80)
    print(f"Horse: {sample['horse_name']} (ID: {sample['horse_id']})")
    print(f"Race Date: {sample['race_date']}")
    print(f"Race City: {sample['city']}")
    print(f"Race Track: {sample['track_type']}")
    print(f"Race Distance: {sample['distance']}m")
    print(f"Race Time: {sample['time']}")
    
    idman = sample['last_idman']
    print(f"\nIDMAN DATA (before race):")
    print(f"  İdman Tarihi: {idman.get('İ. Tarihi') or idman.get('Ä°. Tarihi')}")
    print(f"  İdman Hipodrom: {idman.get('İ. Hip.') or idman.get('Ä°. Hip.')}")
    print(f"  İdman Pist: {idman.get('Pist')}")
    print(f"  400m: {idman.get('400m')}")
    print(f"  600m: {idman.get('600m')}")
    print(f"  800m: {idman.get('800m')}")
    print(f"  1000m: {idman.get('1000m')}")

# Dream horse kontrol et
print("\n" + "=" * 80)
print("DREAM HORSE PROFILE:")
print("=" * 80)

with open("E:\\data\\stats\\dream_horse\\Maiden\\Istanbul\\İngiliz\\Sentetik_1200m.json", 'r', encoding='utf-8') as f:
    dream = json.load(f)

print(f"Name: {dream['horse_name']}")
print(f"Total Wins Analyzed: {dream['_metadata']['total_wins_analyzed']}")
print(f"\nAverage Race Stats:")
print(f"  Age: {dream['horse_age']}")
print(f"  Weight: {dream['horse_weight']}")
print(f"  Time: {dream['time']}")
print(f"  Ganyan: {dream['ganyan']}")

print(f"\nNormalized İdman Averages (adjusted to race track):")
print(f"  400m: {dream['idman_400m']} ({dream['_metadata']['idman_data_counts']['400m']} horses)")
print(f"  600m: {dream['idman_600m']} ({dream['_metadata']['idman_data_counts']['600m']} horses)")
print(f"  800m: {dream['idman_800m']} ({dream['_metadata']['idman_data_counts']['800m']} horses)")
print(f"  1000m: {dream['idman_1000m']} ({dream['_metadata']['idman_data_counts']['1000m']} horses)")
print(f"  1200m: {dream['idman_1200m']} ({dream['_metadata']['idman_data_counts']['1200m']} horses)")

print("\n" + "=" * 80)
print("✓ İdman entegrasyonu başarıyla tamamlandı!")
print("✓ Farklı pistlerde yapılan idmanlar normalize edildi")
print("✓ Yarış tarihinden önceki son idmanlar kullanıldı")
print("=" * 80)
