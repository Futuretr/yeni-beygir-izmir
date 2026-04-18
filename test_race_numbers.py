from test_with_idman import load_race_from_program_with_idman

# Race 0 (gerçek 1. koşu)
print("=" * 50)
print("RACE NUMBER 0 (Gerçek 1. Koşu)")
print("=" * 50)
race_horses, race_info = load_race_from_program_with_idman('Istanbul', 2024, 1, 27, 0)
print(f"Kategori: {race_info['category']}")
print(f"At sayısı: {len(race_horses)}")
print(f"İlk at: {race_horses[0]['horse_name']}")

print("\n" + "=" * 50)
print("RACE NUMBER 1 (Gerçek 2. Koşu)")
print("=" * 50)
race_horses, race_info = load_race_from_program_with_idman('Istanbul', 2024, 1, 27, 1)
print(f"Kategori: {race_info['category']}")
print(f"At sayısı: {len(race_horses)}")
print(f"İlk at: {race_horses[0]['horse_name']}")
