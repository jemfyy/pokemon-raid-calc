import json

# 파일 로드
with open("latest.json", encoding="utf-8") as f:
    data = json.load(f)

# 기술 ID → 사람이 읽을 수 있는 이름 맵 생성
move_id_to_name = {}
for entry in data:
    tid = entry["templateId"]
    if tid.startswith("COMBAT_V") and "MOVE_" in tid:
        move_id = tid.replace("COMBAT_", "")
        move_name = tid.split("MOVE_")[-1].replace("_FAST", "").replace("_", " ").title()
        move_id_to_name[move_id] = move_name

# 티어별 HP 매핑
tier_hp_map = {
    "RAID_BOSS_TIER_1": 6000,
    "RAID_BOSS_TIER_3": 9000,
    "RAID_BOSS_TIER_5": 15000,
    "RAID_BOSS_MEGA": 18000,
    "RAID_BOSS_ELITE": 20000
}

boss_data = {}

for entry in data:
    if not entry["templateId"].startswith("V"):
        continue
    if "pokemonSettings" not in entry.get("data", {}):
        continue
    
    settings = entry["data"]["pokemonSettings"]
    stats = settings.get("stats", {})
    pokemon_id = settings.get("pokemonId", "")
    name_raw = pokemon_id  # 💡 여기서 먼저 정의해줘야 함
    force_include = {"REGIELEKI", "REGIDRAGO"}

    # 보스 필터 (느슨하게)
    is_boss = (
        "LEGENDARY" in settings.get("tags", []) or
        "MYTHICAL" in settings.get("tags", []) or
        stats.get("baseStamina", 0) >= 200 or
        name_raw in force_include
    )
    if not is_boss:
        continue

    # 이름 추출
    name_raw = settings.get("pokemonId", "UNKNOWN")
    pokemon_name = name_raw.replace("_", " ").title()

    # 타입
    types = []
    if "type" in settings:
        types.append(settings["type"].replace("POKEMON_TYPE_", "").title())
    if "type2" in settings:
        types.append(settings["type2"].replace("POKEMON_TYPE_", "").title())

    # 기술 이름 변환
    fast_moves = [
        move_id_to_name.get(m, m.replace("_FAST", "").replace("_", " ").title())
        for m in settings.get("quickMoves", [])
    ]
    charged_moves = [
        move_id_to_name.get(m, m.replace("_", " ").title())
        for m in settings.get("cinematicMoves", [])
    ]

    # 보스 HP 설정
    hp = 15000  # 기본값
    for tag in settings.get("tags", []):
        if tag in tier_hp_map:
            hp = tier_hp_map[tag]
            break

    # 최종 데이터 저장
    boss_data[pokemon_name] = {
        "types": types,
        "baseAttack": stats.get("baseAttack", 0),
        "baseDefense": stats.get("baseDefense", 0),
        "baseStamina": stats.get("baseStamina", 0),
        "hp": hp,
        "moves": {
            "fast": fast_moves,
            "charged": charged_moves
        }
    }

# 저장
with open("data/boss_data.json", "w", encoding="utf-8") as f:
    json.dump(boss_data, f, indent=2)

print(f"✅ 보스 데이터 저장 완료! 총 {len(boss_data)}마리 저장됨.")
