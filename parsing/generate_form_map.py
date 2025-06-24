import json
import re
from collections import Counter

with open("latest.json", encoding="utf-8") as f:
    data = json.load(f)

form_counter = Counter()
example_pokemon = {}
clean_form_map = {}

def is_skip_form(form, pid):
    form_upper = str(form).upper()
    # Normal, Default, Costume, Fashion, Anniversary 등
    if "NORMAL" in form_upper or "DEFAULT" in form_upper or "COSTUME" in form_upper or "FASHION" in form_upper or "ANNIVERSARY" in form_upper:
        return True
    # 연도(YYYY), 피카츄, 안농, 유니크/잡탕
    if re.fullmatch(r"\d{4}", form_upper):
        return True
    if pid.startswith("PIKACHU") or pid.startswith("UNOWN") or pid.startswith("ANNIV") or pid.startswith("UNIQUE"):
        return True
    # 기타: 알파벳 한글자 등
    if re.fullmatch(r"[A-Z]$", form_upper):
        return True
    return False

for entry in data:
    settings = entry.get("data", {}).get("pokemonSettings")
    if not settings:
        continue
    form = settings.get("form")
    pid = settings.get("pokemonId", "")
    if form and not is_skip_form(form, pid):
        form_str = str(form).upper()
        form_only = re.sub(r'^.*?_', '', form_str)
        form_counter[form_only] += 1
        if form_only not in example_pokemon:
            example_pokemon[form_only] = pid
        readable = form_only.title().replace("_", " ")
        clean_form_map[form_str] = readable

with open("data/form_map.json", "w", encoding="utf-8") as f:
    json.dump(clean_form_map, f, ensure_ascii=False, indent=2)

print("✅ data/form_map.json 저장 완료!")
for form, count in form_counter.most_common(20):
    print(f"{form:20s} | {count:4d} | 예시: {example_pokemon[form]}")
