from group_wins_by_category import load_idman_for_horse, get_last_idman_before_race

# Test 1: İdman yükleme
idman = load_idman_for_horse(55712)
print(f'Horse 55712 idman records: {len(idman)}')

if idman:
    print(f'First idman date: {idman[0].get("İ. Tarihi")}')
    
    # Test 2: Tarih kontrolü
    result = get_last_idman_before_race(idman, '29.01.2024')
    if result:
        print(f'Last idman before 29.01.2024: {result.get("İ. Tarihi")}')
        print(f'600m time: {result.get("600m")}')
    else:
        print('No idman found before 29.01.2024')
