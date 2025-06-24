import json
import os

def clean_type_name(raw_type):
    prefix = "Pokemon_type_"
    if raw_type and raw_type.startswith(prefix):
        return raw_type[len(prefix):].capitalize()
    elif raw_type:
        return raw_type.capitalize()
    else:
        return ""
manual_overrides = {
    "Thunder Cage": {
        "power": 220,
        "duration": 3.5,
        "energyDelta": -50,
        "type": "Electric"
    },
    "Dragon Energy": {
        "power": 155,
        "duration": 3.5,
        "energyDelta": -100,
        "type": "Dragon"
    },
    "Giga Impact": {
        "power": 200,
        "duration": 4.7,
        "energyDelta": -100,
        "type": "Normal"
    }
}
def process_moves():
    with open("data/raid_move_data.json", encoding="utf-8") as f:
        raw_moves = json.load(f)

    processed_moves = []
    for m in raw_moves:
        name = m.get("name")
        if not isinstance(name, str):
            name = ""

        pretty_name = name.replace("_FAST", "").replace("_", " ").title()
        category = "Fast" if "FAST" in name else "Charged"

        if pretty_name in manual_overrides:
            o = manual_overrides[pretty_name]
            power = o["power"]
            duration_sec = o["duration"]
            energy_delta = o["energyDelta"]
            cleaned_type = o["type"]
        else:
            duration_ms = m.get("durationMs") or m.get("duration") or 1000
            duration_sec = duration_ms / 1000
            power = m.get("power", 0)
            energy_delta = m.get("energyDelta", 0)
            raw_type = m.get("type", "")
            cleaned_type = clean_type_name(raw_type)
            
     
        dps = power / duration_sec if duration_sec > 0 else 0

        processed_moves.append({
            "id": m.get("id", ""),
            "name": pretty_name,
            "type": cleaned_type,
            "power": power,
            "energyDelta": m.get("energyDelta", 0),
            "duration": round(duration_sec, 2),
            "category": category,
            "dps": round(dps, 2)
        })

    os.makedirs("data", exist_ok=True)
    output_path = "data/processed_moves.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_moves, f, indent=2, ensure_ascii=False)

    print(f"✅ 기술 데이터 후처리 완료! 총 {len(processed_moves)}개 기술 저장됨.")
    print(f"👉 저장 위치: {output_path}")

if __name__ == "__main__":
    process_moves()
