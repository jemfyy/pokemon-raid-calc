# download_latest.py
import urllib.request

#URL = "https://raw.githubusercontent.com/PokeMiners/game_masters/master/latest/latest.json"
URL = "https://raw.githubusercontent.com/PokeMiners/game_masters/refs/heads/master/latest/latest.json"
FILENAME = "latest.json"

def download_latest_json():
    print("📥 latest.json 다운로드 중... (기존 파일도 덮어씁니다)")
    urllib.request.urlretrieve(URL, FILENAME)
    print("✅ 다운로드 완료! (항상 최신 파일로 덮어씁니다)")

if __name__ == "__main__":
    download_latest_json()
