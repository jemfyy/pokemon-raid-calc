import requests
import os
import json
from datetime import datetime

def fetch_and_save_raid_moves():
    url = "https://raw.githubusercontent.com/PokeMiners/game_masters/master/latest/latest.json"
    res = requests.get(url)
    if res.status_code != 200:
        print("❌ 다운로드 실패:", res.status_code)
        return

    data = res.json()
    moves = []

    for entry in data:
        tid = entry.get("templateId", "")
        move_data = entry.get("data", {}).get("moveSettings")

        # 'V'로 시작하는 템플릿 중 moveSettings가 있는 것 필터링
        if tid.startswith("V") and move_data:
            moves.append({
                "id": tid,
                "name": move_data.get("movementId", ""),
                "type": move_data.get("pokemonType", "").capitalize(),
                "power": move_data.get("power", 0),
                "energyDelta": move_data.get("energyDelta", 0),
                "durationMs": move_data.get("durationMs", 1000)
            })

    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "raid_move_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(moves, f, indent=2, ensure_ascii=False)

    print(f"✅ 레이드용 기술 데이터 저장 완료! 총 {len(moves)}개 기술 ({datetime.now()})")

if __name__ == "__main__":
    fetch_and_save_raid_moves()
