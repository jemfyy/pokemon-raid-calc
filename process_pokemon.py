import json
import os

def normalize_name(name):
    return name.lower().replace(" ", "").replace("-", "").replace("_", "")

def build_pokemon_data_fuzzy():
    with open("data/processed_moves.json", encoding="utf-8") as f:
        moves = json.load(f)

    # 기술 이름 정규화 매핑 생성
    move_dict = {normalize_name(m["name"]): m for m in moves}

    with open("data/pokemon_base.json", encoding="utf-8") as f:
        pokemons = json.load(f)

    result = []
    for p in pokemons:
        fast_name_raw = p["fast_moves"][0] if p.get("fast_moves") else None
        charged_name_raw = p["charged_moves"][0] if p.get("charged_moves") else None

        fast_move = None
        charged_move = None

        if fast_name_raw:
            fast_move = move_dict.get(normalize_name(fast_name_raw))
            if not fast_move:
                print(f"⚠️ 빠른 기술 '{fast_name_raw}' 매칭 실패: 유사 매칭도 없음")

        if charged_name_raw:
            charged_move = move_dict.get(normalize_name(charged_name_raw))
            if not charged_move:
                print(f"⚠️ 차지 기술 '{charged_name_raw}' 매칭 실패: 유사 매칭도 없음")

        result.append({
            "id": p["id"],
            "types": p["types"],
            "fast_move": fast_move,
            "charged_move": charged_move
        })

    os.makedirs("data", exist_ok=True)
    with open("data/processed_pokemon.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ 유연 매칭 후처리 완료! 총 {len(result)}개 포켓몬 저장됨.")

if __name__ == "__main__":
    build_pokemon_data_fuzzy()
