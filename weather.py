import requests
import os
from datetime import datetime

KAKAO_ACCESS_TOKEN = os.environ.get("KAKAO_ACCESS_TOKEN")
KAKAO_REFRESH_TOKEN = os.environ.get("KAKAO_REFRESH_TOKEN")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
AIR_API_KEY = os.environ.get("AIR_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")

def refresh_kakao_token():
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": os.environ.get("KAKAO_REST_API_KEY"),
        "refresh_token": KAKAO_REFRESH_TOKEN
    }
    res = requests.post(url, data=data)
    result = res.json()
    print("토큰 갱신 결과:", result)
    new_access_token = result.get("access_token")
    new_refresh_token = result.get("refresh_token")
    if new_access_token:
        update_github_secret("KAKAO_ACCESS_TOKEN", new_access_token)
    if new_refresh_token:
        update_github_secret("KAKAO_REFRESH_TOKEN", new_refresh_token)
    return new_access_token

def update_github_secret(secret_name, secret_value):
    import base64
    from cryptography.hazmat.primitives.asymmetric.padding import OAEP
    from cryptography.hazmat.primitives.asymmetric.padding import MGF1
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
    import nacl.encoding
    import nacl.public
    headers = {
        "Authorization": "token " + GITHUB_TOKEN,
        "Accept": "application/vnd.github.v3+json"
    }
    key_url = "https://api.github.com/repos/" + GITHUB_REPO + "/actions/secrets/public-key"
    key_res = requests.get(key_url, headers=headers)
    key_data = key_res.json()
    public_key = key_data["key"]
    key_id = key_data["key_id"]
    public_key_bytes = nacl.encoding.Base64Encoder.decode(public_key)
    sealed_box = nacl.public.SealedBox(nacl.public.PublicKey(public_key_bytes))
    encrypted = sealed_box.encrypt(secret_value.encode())
    encrypted_b64 = nacl.encoding.Base64Encoder.encode(encrypted).decode()
    secret_url = "https://api.github.com/repos/" + GITHUB_REPO + "/actions/secrets/" + secret_name
    requests.put(secret_url, headers=headers, json={
        "encrypted_value": encrypted_b64,
        "key_id": key_id
    })

def get_weather():
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H00")
    params = {
        "serviceKey": WEATHER_API_KEY,
        "pageNo": 1,
        "numOfRows": 10,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": 60,
        "ny": 127
    }
    res = requests.get(url, params=params)
    items = res.json()["response"]["body"]["items"]["item"]
    temp = next(i["obsrValue"] for i in items if i["category"] == "T1H")
    rain = next(i["obsrValue"] for i in items if i["category"] == "RN1")
    sky = next(i["obsrValue"] for i in items if i["category"] == "PTY")
    sky_map = {"0": "맑음", "1": "비", "2": "비/눈", "3": "눈", "4": "소나기"}
    sky_text = sky_map.get(sky, "알수없음")
    result = "기온: " + str(temp) + "C\n"
    result += "날씨: " + sky_text + "\n"
    result += "강수량: " + str(rain) + "mm"
    return result

def get_air():
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    params = {
        "serviceKey": AIR_API_KEY,
        "returnType": "json",
        "numOfRows": 1,
        "pageNo": 1,
        "sidoName": "서울",
        "ver": "1.0"
    }
    res = requests.get(url, params=params)
    item = res.json()["response"]["body"]["items"][0]
    pm10 = item.get("pm10Value", "알수없음")
    pm25 = item.get("pm25Value", "알수없음")
    def grade(val):
        try:
            v = int(val)
            if v <= 30:
                return "좋음"
            elif v <= 80:
                return "보통"
            elif v <= 150:
                return "나쁨"
            else:
                return "매우나쁨"
        except Exception:
            return "알수없음"
    result = "미세먼지(PM10): " + str(pm10) + " " + grade(pm10) + "\n"
    result += "초미세먼지(PM2.5): " + str(pm25) + " " + grade(pm25)
    return result

def send_kakao(access_token, message):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": "Bearer " + str(access_token)}
    template = "{\"object_type\":\"text\",\"text\":\"" + message + "\",\"link\":{\"web_url\":\"https://weather.naver.com\"}}"
    data = {"template_object": template}
    res = requests.post(url, headers=headers, data=data)
    print("전송 결과: " + str(res.status_code))
    print(res.text)

if __name__ == "__main__":
    new_token = refresh_kakao_token()
    access_token = new_token if new_token else KAKAO_ACCESS_TOKEN
    now = datetime.now()
    msg = now.strftime("%Y년 %m월 %d일") + " 날씨 알림\n\n"
    msg += get_weather() + "\n\n"
    msg += get_air()
    send_kakao(access_token, msg)
    print(msg)
