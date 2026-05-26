import requests
import os
from datetime import datetime

KAKAO_ACCESS_TOKEN = os.environ.get("KAKAO_ACCESS_TOKEN")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
AIR_API_KEY = os.environ.get("AIR_API_KEY")

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

def send_kakao(message):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": "Bearer " + str(KAKAO_ACCESS_TOKEN)}
    template = "{\"object_type\":\"text\",\"text\":\"" + message + "\",\"link\":{\"web_url\":\"https://weather.naver.com\"}}"
    data = {"template_object": template}
    res = requests.post(url, headers=headers, data=data)
    print("전송 결과: " + str(res.status_code))
    print(res.text)

if __name__ == "__main__":
    now = datetime.now()
    msg = now.strftime("%Y년 %m월 %d일") + " 날씨 알림\n\n"
    msg += get_weather() + "\n\n"
    msg += get_air()
    send_kakao(msg)
    print(msg)
