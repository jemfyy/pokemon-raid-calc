from flask import Flask, render_template, jsonify, request
import json
import os

app = Flask(__name__)

DATA_DIR = "data"

# --- 데이터 불러오기 ---
with open(os.path.join(DATA_DIR, "boss_data.json"), encoding="utf-8") as f:
    boss_data = json.load(f)
with open(os.path.join(DATA_DIR, "pokemon_data.json"), encoding="utf-8") as f:
    pokemon_data = json.load(f)
with open(os.path.join(DATA_DIR, "processed_moves.json"), encoding="utf-8") as f:
    move_data = json.load(f)
with open(os.path.join(DATA_DIR, "type_chart.json"), encoding="utf-8") as f:
    type_chart = json.load(f)

def get_type_multiplier(move_type, defender_types):
    mtype = move_type.title()
    multiplier = 1.0
    for t in defender_types:
        dtype = t.title()
        multiplier *= type_chart.get(mtype, {}).get(dtype, 1.0)
    return multiplier

def get_stab(pokemon_types, move_type):
    return 1.2 if move_type in pokemon_types else 1.0

def get_raid_damage(attacker_atk, defender_def, move_power, multiplier):
    return int(0.5 * attacker_atk / defender_def * move_power * multiplier) + 1

def get_incoming_damage(boss_atk, my_def, boss_move, my_types):
    multiplier = get_type_multiplier(boss_move['type'], my_types)
    # 보스의 기술로 내가 맞을 때 한 번에 입는 데미지
    return get_raid_damage(boss_atk, my_def, boss_move['power'], multiplier)

def get_survival_time(my_hp, incoming_dps):
    if incoming_dps <= 0:
        return 9999.0
    return my_hp / incoming_dps


def combo_dps(fast_move, charged_move, atk, def_, fast_mult, charged_mult):
    fast_power = fast_move["power"]
    fast_energy = fast_move.get("energyDelta", 0)
    fast_duration = fast_move["duration"]
    charged_power = charged_move["power"]
    charged_energy = charged_move.get("energyDelta", 0)
    charged_duration = charged_move["duration"]

    # zero-division 방어
    if not fast_energy:
        print("경고! fast_move energyDelta 비정상:", fast_move)
        return 0

    needed_energy = abs(charged_energy)
    n_fast = (needed_energy + fast_energy - 1) // fast_energy

    total_power = fast_power * n_fast * fast_mult + charged_power * charged_mult
    total_time = fast_duration * n_fast + charged_duration

    # duration이 ms 단위라면 아래처럼 변환!
    # total_time = (fast_duration * n_fast + charged_duration) / 1000

    # 보정치 적용
    atk_ = atk * 0.84
    def__ = def_ * 0.79

    dps = total_power / total_time * atk_ / def__
    return dps

def get_incoming_damage(boss_atk, my_def, boss_move, my_types):
    multiplier = get_type_multiplier(boss_move['type'], my_types)
    return get_raid_damage(boss_atk, my_def, boss_move['power'], multiplier)

def get_survival_time(my_hp, incoming_dps):
    if incoming_dps <= 0:
        return 9999.0
    return my_hp / incoming_dps

# 프론트 HTML 렌더링
@app.route("/recommend")
def recommend_page():
    return render_template("recommend.html")

# API: 보스 목록 제공
@app.route("/api/bosses")
def get_bosses():
    # 프론트에서 쓰는 필드만
    result = {}
    for name, info in boss_data.items():
        result[name] = {
            "types": info['types'],
            "moves": info['moves']
        }
    return jsonify(result)

def get_move_by_name(name):
    if not isinstance(name, str):
        print(f"[기술명 형식 오류] name={name}")
        return None
    for move in move_data:
        if move.get('name', '').strip().lower() == name.strip().lower():
            return move
    return None


# API: 추천 계산
@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    boss = data.get("boss")
    fast_moves = data.get("fastMoves") or [data.get("fastMove")]
    charged_moves = list(set(
        (data.get("chargedMoves") or []) +
        (data.get("specialChargedMoves") or []) +
        ([data.get("chargedMove")] if data.get("chargedMove") else [])
    ))
    sort_by = data.get("sortBy", "tdo")  # 추가

    print("boss:", boss)
    print("fast_moves:", fast_moves)
    print("charged_moves:", charged_moves)

    if not boss or not fast_moves or not charged_moves:
        print("입력값 누락")
        return jsonify([])

    boss_info = boss_data[boss]
    boss_types = boss_info['types']
    boss_atk = boss_info['baseAttack']
    boss_def = boss_info['baseDefense']
    boss_hp = boss_info['hp']

    results = []
    for poke_name, poke in pokemon_data.items():
        poke_types = poke['types']
        base_atk = poke['baseAttack']
        base_def = poke['baseDefense']
        base_hp = poke['baseStamina']

        # Shadow 보정
        if "(Shadow)" in poke_name:
            my_atk = base_atk * 1.2
            my_def = base_def * 0.833
        else:
            my_atk = base_atk
            my_def = base_def
        my_hp = base_hp

        for fast_name in poke.get('quickMoves', []):
            fast_move = get_move_by_name(fast_name)
            if fast_move is None:
                print(f"[fast_move 매칭 실패] {poke_name}: {fast_name}")
                continue

            for charged_name in poke.get('chargedMoves', []):
                charged_move = get_move_by_name(charged_name)
                if charged_move is None:
                    print(f"[charged_move 매칭 실패] {poke_name}: {charged_name}")
                    continue
               
                fast_mult = get_type_multiplier(fast_move['type'], boss_types) * get_stab(poke_types, fast_move['type'])
                charged_mult = get_type_multiplier(charged_move['type'], boss_types) * get_stab(poke_types, charged_move['type'])
                my_dps = combo_dps(fast_move, charged_move, my_atk, boss_def, fast_mult, charged_mult)
              
                if my_dps <= 0:
                    print(f"[dps=0] {poke_name}: {fast_name} / {charged_name}")
                    continue

                # 여기에 생존/tdo 계산 추가
                incoming_dps = 0
                cnt = 0
                for boss_fast_name in fast_moves:
                    boss_fast_move = get_move_by_name(boss_fast_name)
                    if boss_fast_move:
                        incoming_dps += get_incoming_damage(boss_atk, my_def, boss_fast_move, poke_types)
                        cnt += 1
                for boss_charged_name in charged_moves:
                    boss_charged_move = get_move_by_name(boss_charged_name)
                    if boss_charged_move:
                        incoming_dps += get_incoming_damage(boss_atk, my_def, boss_charged_move, poke_types)
                        cnt += 1
                if cnt > 0:
                    incoming_dps /= cnt
                else:
                    incoming_dps = 1

                survival = get_survival_time(my_hp, incoming_dps)
                tdo = my_dps * survival
                er = (my_dps ** 3 * tdo) ** 0.25 if my_dps > 0 and tdo > 0 else 0

                results.append({
                    "name": poke_name,
                    "fastMove": fast_name,
                    "chargedMove": charged_name,
                    "dps": my_dps,
                    "survival": survival,
                    "tdo": tdo,
                    "er": er,
                    "specialChargedMoves": poke.get("specialChargedMoves", []),
                    "specialFastMoves": poke.get("specialFastMoves", [])
                })

    print("최종 추천 개수:", len(results))

    # tdo 기준 상위 50개

    if sort_by == "dps":
        results.sort(key=lambda x: x["dps"], reverse=True)
    elif sort_by == "tdo":
        results.sort(key=lambda x: x["tdo"], reverse=True)
    elif sort_by == "name":
        results.sort(key=lambda x: x["name"])
    else:  # 기본 ER
        results.sort(key=lambda x: x["er"], reverse=True)

    return jsonify(results[:200])


if __name__ == "__main__":
    app.run(debug=True)
