import json

with open("latest.json", encoding="utf-8") as f:
    data = json.load(f)

move_id_to_name = {}

for entry in data:
    tid = entry.get("templateId", "")
    if tid.startswith("COMBAT_V") and "MOVE_" in tid:
        move_id = tid.replace("COMBAT_", "")
        readable = tid.split("MOVE_")[-1].replace("_FAST", "").replace("_", " ").title()
        move_id_to_name[move_id] = readable

pokemon_data = {}

shadow_whitelist = set()

# 1차 패스: shadow 필드 보유 포켓몬 수집
def collect_shadow_eligible():
    for entry in data:
        if not entry.get("templateId", "").startswith("V"):
            continue
        settings = entry.get("data", {}).get("pokemonSettings")
        if not settings:
            continue
        pid = settings.get("pokemonId")
        if not pid:
            continue
        if settings.get("shadow") is not None or settings.get("isShadowPokemon", False):
            shadow_whitelist.add(pid.upper())

collect_shadow_eligible()

def get_regional(form, costume):
    for val in [form, costume]:
        if not val:
            continue
        v = str(val).upper()
        if "ALOLA" in v: return "Alolan"
        if "GALARIAN" in v: return "Galarian"
        if "HISUIAN" in v: return "Hisuian"
        if "PALDEAN" in v or "PALDEA" in v: return "Paldean"
    return None

def get_special(temp_evo_id):
    if not temp_evo_id:
        return None
    v = str(temp_evo_id).upper()
    if "MEGA_X" in v: return "Mega X"
    if "MEGA_Y" in v: return "Mega Y"
    if "MEGA" in v: return "Mega"
    if "PRIMAL" in v: return "Primal"
    if "ORIGIN" in v: return "Origin"
    return None

def get_form_name(form):
    if not form:
        return None
    v = str(form).upper()
    keywords = ["BLACK", "WHITE", "THERIAN", "ZEN", "SKY", "CROWNED", "UNBOUND", "PIROUETTE", "DAWN", "DUSK"]
    for k in keywords:
        if k in v:
            return k.title()
    return None

def is_shadow_eligible(pokemon_id, form):
    if str(pokemon_id).upper() not in shadow_whitelist:
        return False
    blocked_keywords = ["BLACK", "WHITE", "THERIAN", "ZEN", "SKY", "CROWNED", "UNBOUND", "PIROUETTE", "DAWN", "DUSK", "ORIGIN"]
    if form and any(k in str(form).upper() for k in blocked_keywords):
        return False
    return True

for entry in data:
    if not entry.get("templateId", "").startswith("V"):
        continue
    settings = entry.get("data", {}).get("pokemonSettings")
    if not settings:
        continue

    pid_raw = settings.get("pokemonId")
    if not pid_raw:
        continue
    base_name = pid_raw.replace("_", " ").title()

    types = []
    if "type" in settings:
        types.append(settings["type"].replace("POKEMON_TYPE_", "").title())
    if "type2" in settings:
        types.append(settings["type2"].replace("POKEMON_TYPE_", "").title())

    quick_moves = [
        move_id_to_name.get(str(m), str(m).replace("_FAST", "").replace("_", " ").title())
        for m in settings.get("quickMoves", [])
    ]
    charged_moves = [
        move_id_to_name.get(str(m), str(m).replace("_", " ").title())
        for m in settings.get("cinematicMoves", [])
    ]
    stats = settings.get("stats", {})

    special_fast_moves = []
    for key in ["eliteQuickMove", "quickEliteMoves", "legacyMoves", "specialQuickMoves"]:
        if key in settings:
            special_fast_moves.extend([
                move_id_to_name.get(str(m), str(m).replace("_FAST", "").replace("_", " ").title())
                for m in settings.get(key, [])
            ])

    special_moves = []
    for key in ["eliteCinematicMove", "cinematicEliteMoves", "legacyMoves", "specialCinematicMoves"]:
        if key in settings:
            special_moves.extend([
                move_id_to_name.get(str(m), str(m).replace("_", " ").title())
                for m in settings.get(key, [])
            ])
    all_charged_moves = sorted(set(charged_moves + special_moves))
    all_quick_moves = sorted(set(quick_moves + special_fast_moves))

    poke_info = {
        "types": types,
        "baseAttack": stats.get("baseAttack", 0),
        "baseDefense": stats.get("baseDefense", 0),
        "baseStamina": stats.get("baseStamina", 0),
        "quickMoves": all_quick_moves,
        "chargedMoves": all_charged_moves
    }
    if special_fast_moves:
        poke_info["specialFastMoves"] = sorted(set(special_fast_moves))
    if special_moves:
        poke_info["specialChargedMoves"] = sorted(set(special_moves))

    form = settings.get("form", "")
    costume = settings.get("costume", "")
    regional = get_regional(form, costume)
    form_name = get_form_name(form)
    is_shadow = (settings.get("shadow") is not None or settings.get("isShadowPokemon", False))

    name = base_name
    if regional:
        name = f"{base_name} ({regional})"
    elif form_name:
        name = f"{base_name} ({form_name})"

    pokemon_data[name] = poke_info

    if is_shadow and is_shadow_eligible(pid_raw, form):
        name_shadow = f"{name}, Shadow" if '(' in name else f"{name} (Shadow)"
        pokemon_data[name_shadow] = poke_info

    if form and "ORIGIN" in str(form).upper():
        name_origin = f"{base_name} (Origin)"
        if name_origin not in pokemon_data:
            pokemon_data[name_origin] = poke_info

    temp_ev = settings.get("tempEvoOverrides", [])
    for evo in temp_ev:
        temp_evo_id = evo.get("tempEvoId", "")
        special = get_special(temp_evo_id)
        if not special:
            continue
        stats_evo = evo.get("stats", stats)
        types_evo = []
        if "typeOverride1" in evo:
            types_evo.append(evo["typeOverride1"].replace("POKEMON_TYPE_", "").title())
        if "typeOverride2" in evo:
            types_evo.append(evo["typeOverride2"].replace("POKEMON_TYPE_", "").title())
        if not types_evo:
            types_evo = types
        all_charged_moves_evo = sorted(set(charged_moves + special_moves))
        all_quick_moves_evo = sorted(set(quick_moves + special_fast_moves))

        poke_info_evo = {
            "types": types_evo,
            "baseAttack": stats_evo.get("baseAttack", 0),
            "baseDefense": stats_evo.get("baseDefense", 0),
            "baseStamina": stats_evo.get("baseStamina", 0),
            "quickMoves": all_quick_moves_evo,
            "chargedMoves": all_charged_moves_evo
        }
        if special_moves:
            poke_info_evo["specialChargedMoves"] = sorted(set(special_moves))
        if special_fast_moves:
            poke_info_evo["specialFastMoves"] = sorted(set(special_fast_moves))
        name_special = f"{base_name} ({special})"
        pokemon_data[name_special] = poke_info_evo

manual_special_moves = {
    "Regieleki": ["Thunder Cage"],  # 썬더 프리즌
    "Regidrago": ["Dragon Energy"], # 드래곤 에너지
    "Regigigas": ["Giga Impact"]    # 묵사발
}

for name, extra_moves in manual_special_moves.items():
    if name in pokemon_data:
        pokemon_data[name].setdefault("specialChargedMoves", [])
        pokemon_data[name]["specialChargedMoves"] += extra_moves
        pokemon_data[name]["chargedMoves"] += extra_moves

        
with open("data/pokemon_data.json", "w", encoding="utf-8") as f:
    json.dump(pokemon_data, f, indent=2, ensure_ascii=False)

print(f"✅ 포켓몬 종합 정보 저장 완료! 총 {len(pokemon_data)}마리 저장됨.")
