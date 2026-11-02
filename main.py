import random
from time import time, localtime
import cityinfo
from requests import get, post
from datetime import datetime, date 
import sys
import os
import http.client, urllib
import json
from zhdate import ZhDate  
global false, null, true
false = null = true = ''
def get_color():
    # 获取随机颜色 
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)


def get_access_token():
    # appId
    app_id = config["app_id"]
    # appSecret：优先读环境变量，本地调试回落到 config.json
    app_secret = os.getenv("APP_SECRET") or config["app_secret"]
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                .format(app_id, app_secret))
    try:
        access_token = get(post_url).json()['access_token']
    except KeyError:
        print("获取access_token失败，请检查app_id和app_secret是否正确")
        os.system("pause")
        sys.exit(1)
    # print(access_token)
    return access_token

def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    # 判断是否为农历生日
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        # 今年生日
        birthday = ZhDate(year, r_mouth, r_day).to_datetime().date()
        year_date = birthday


    else:
        # 获取国历生日的今年对应月和日
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        # 今年生日
        year_date = date(year, birthday_month, birthday_day)
    # 计算生日年份，如果还没过，按当年减，如果过了需要+1
    if today > year_date:
        if birthday_year[0] == "r":
            # 获取农历明年生日的月和日
            r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
            birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
        else:
            birth_date = date((year + 1), birthday_month, birthday_day)
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    return birth_day



def to_bool(value) -> bool:
    """把 config.json 里五花八门的开关写法统一转成 bool。

    config.json 里 "false" / "False" 都是非空字符串，直接 `!= False` 判断永远为真，
    导致想关闭的功能关不掉，所以必须显式转换。

    Args:
        value: config.json 里的原始值（可能是 bool / str / None）

    Returns:
        对应的布尔值
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "y", "on")
    return bool(value)


def get_weather(location_id, qw_key, qw_host):
    """调用和风天气 v7 三日预报接口，获取今日天气。

    Args:
        location_id: 和风天气 LocationID（如合肥 101220101）
        qw_key: 和风天气 API Key，从环境变量 QW_KEY 读取
        qw_host: 和风天气控制台分配的专属 API Host

    Returns:
        (天气状况, 最高温, 最低温) 三元组；失败时返回占位文案
    """
    fallback = ("天气接口异常", "0", "0")

    # 关键：Key 为 None 时 requests 会静默丢弃这个请求头（2.28.1 与 2.34 实测均是），
    # 服务端返回 401，响应体是 {"error": {...}} 而不是业务结构，
    # 于是 res_json["code"] 抛 KeyError 被 except 吞掉，只留下"天气接口异常"。提前拦掉。
    if not qw_key:
        print("和风天气请求失败：未取到 API Key。"
              "GitHub Actions 请在仓库 Settings → Secrets 添加 QW_KEY，"
              "并在 workflow 的 step 里用 env 注入。")
        return fallback

    url = f"https://{qw_host}/v7/weather/3d"
    params = {"location": location_id, "lang": "zh"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
        "X-QW-Api-Key": qw_key,  # V7 必须放请求头，不能拼在 URL 里
    }

    try:
        r = get(url, headers=headers, params=params, timeout=10)
    except Exception as e:
        print("和风天气网络请求异常：", e)
        return fallback

    # 401/403/404 时响应体是 {"error": {...}}，不是业务结构，先按 HTTP 状态拦一道
    if r.status_code != 200:
        print(f"和风天气 HTTP {r.status_code}：{r.text[:300]}")
        return fallback

    try:
        res_json = r.json()
    except Exception as e:
        print("和风天气响应不是合法 JSON：", e, r.text[:300])
        return fallback

    code = str(res_json.get("code", ""))
    if code != "200":
        detail = res_json.get("error", {}).get("detail") or res_json.get("message") or res_json
        print(f"和风天气错误码 {code}：{detail}")
        return fallback

    daily = res_json.get("daily") or []
    if not daily:
        print("和风天气返回 daily 为空：", res_json)
        return fallback

    today = daily[0]
    weather = today.get("textDay") or "未知"
    temp = today.get("tempMax") or "0"
    tempn = today.get("tempMin") or "0"
    return weather, temp, tempn





#词霸每日一句
def get_ciba():
    if (Whether_Eng!=False):
        try:
            url = "http://open.iciba.com/dsapi/"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
            }
            r = get(url, headers=headers, timeout=10)  # 加上timeout，防止卡死
            note_en = r.json()["content"]
            note_ch = r.json()["note"]
            return (note_en,note_ch)
        except Exception as e:
            print("词霸接口异常：", e)
            # 失败固定返回两个字符串，不会解包报错
            return ("词霸API调取错误", "")
    else:
        # 如果关闭词霸功能，也要返回2个值
        return ("", "")



#彩虹屁
def caihongpi():
    if (Whether_caihongpi!=False):
        try:
            conn = http.client.HTTPSConnection('api.tianapi.com')  #接口域名
            params = urllib.parse.urlencode({'key':tianxing_API})
            headers = {'Content-type':'application/x-www-form-urlencoded'}
            conn.request('POST','/caihongpi/index',params,headers)
            res = conn.getresponse()
            data = res.read()
            data = json.loads(data)
            data = data["newslist"][0]["content"]
            if("XXX" in data):
                 data = data.replace("XXX","宝贝")
            return data
        except:
            return ("彩虹屁API调取错误，请检查API是否正确申请或是否填写正确")

#健康小提示API
def health():
    if (Whether_health!=False):
        try:
            conn = http.client.HTTPSConnection('api.tianapi.com')  #接口域名
            params = urllib.parse.urlencode({'key':tianxing_API})
            headers = {'Content-type':'application/x-www-form-urlencoded'}
            conn.request('POST','/healthtip/index',params,headers)
            res = conn.getresponse()
            data = res.read()
            data = json.loads(data)
            data = data["newslist"][0]["content"]
            return data
        except:
             return ("健康小提示API调取错误，请检查API是否正确申请或是否填写正确")

#星座运势
def lucky():
    if ( Whether_lucky!=False):
        try:
            conn = http.client.HTTPSConnection('api.tianapi.com')  #接口域名
            params = urllib.parse.urlencode({'key':tianxing_API,'astro':astro})
            headers = {'Content-type':'application/x-www-form-urlencoded'}
            conn.request('POST','/star/index',params,headers)
            res = conn.getresponse()
            data = res.read()
            data = json.loads(data)
            data = "爱情指数："+str(data["newslist"][1]["content"])+"   工作指数："+str(data["newslist"][2]["content"])+"\n今日概述："+str(data["newslist"][8]["content"])
            return data
        except:
            return ("星座运势API调取错误，请检查API是否正确申请或是否填写正确")

# #励志名言
def lizhi():
    if (Whether_lizhi!=False):
        try:
            conn = http.client.HTTPSConnection('api.tianapi.com')  #接口域名
            params = urllib.parse.urlencode({'key':tianxing_API})
            headers = {'Content-type':'application/x-www-form-urlencoded'}
            conn.request('POST','/lzmy/index',params,headers)
            res = conn.getresponse()
            data = res.read()
            data = json.loads(data)
            return data["newslist"][0]["saying"]
        except:
            return ("励志古言API调取错误，请检查API是否正确申请或是否填写正确")
        

# #下雨概率和建议
# def tip():
#     if (Whether_tip!=False):
#         try:
#             conn = http.client.HTTPSConnection('api.tianapi.com')  #接口域名
#             params = urllib.parse.urlencode({'key':tianxing_API,'city':city})
#             headers = {'Content-type':'application/x-www-form-urlencoded'}
#             conn.request('POST','/tianqi/index',params,headers)
#             res = conn.getresponse()
#             data = res.read()
#             data = json.loads(data)
#             tips = data["newslist"][0]["tips"]
#             return tips
#         except Exception as e:
#             print("tip接口异常：", e)
#             return "天气预报API调取错误，请检查API是否正确申请或是否填写正确"
#     else:
#         return ""

# #下雨降雨量（毫米）
# def tip_pop():
#     if (Whether_tip!=False):
#         try:
#             conn = http.client.HTTPSConnection('api.tianapi.com')  #接口域名
#             params = urllib.parse.urlencode({'key':tianxing_API,'city':city})
#             headers = {'Content-type':'application/x-www-form-urlencoded'}
#             conn.request('POST','/tianqi/index',params,headers)
#             res = conn.getresponse()
#             data = res.read()
#             data = json.loads(data)
#             pop = data["newslist"][0]["pcpn"]
#             return int(float(pop))
#         except Exception as e:
#             print("tip_pop接口异常：", e)
#             return 0
#     else:
#         return 0



#推送信息
def send_message(to_user, access_token, city_name, weather, max_temperature, min_temperature, pipi, lizhi, pop, tips, note_en, note_ch, health_tip, lucky_):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]
    # 获取在一起的日子的日期格式
    love_year = int(config["love_date"].split("-")[0])
    love_month = int(config["love_date"].split("-")[1])
    love_day = int(config["love_date"].split("-")[2])
    love_date = date(love_year, love_month, love_day)
    # 获取在一起的日期差
    love_days = str(today.__sub__(love_date)).split(" ")[0]
    # 获取所有生日数据
    birthdays = {}
    for k, v in config.items():
        if k[0:5] == "birth":
            birthdays[k] = v
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {
                "value": "{} {}".format(today, week),
                "color": get_color()
            },
            "city": {
                "value": city_name,
                "color": get_color()
            },
            "weather": {
                "value": weather,
                "color": get_color()
            },
            "min_temperature": {
                "value": min_temperature,
                "color": get_color()
            },
            "max_temperature": {
                "value": max_temperature,
                "color": get_color()
            },
            "love_day": {
                "value": love_days,
                "color": get_color()
            },
            "note_en": {
                "value": note_en,
                "color": get_color()
            },
            "note_ch": {
                "value": note_ch,
                "color": get_color()
            },

            "pipi": {
                "value": pipi,
                "color": get_color()
            },

            "lucky": {
                "value": lucky_,
                "color": get_color()
            },

            "lizhi": {
                "value": lizhi,
                "color": get_color()
            },

            "pop": {
                "value": pop,
                "color": get_color()
            },

            "health": {
                "value": health_tip,
                "color": get_color()
            },

            "tips": {
                "value": tips,
                "color": get_color()
            }
        }
    }
    for key, value in birthdays.items():
        # 获取距离下次生日的时间
        birth_day = get_birthday(value, year, today)
        # 将生日数据插入data
        data["data"][key] = {"value": birth_day, "color": get_color()}
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    response = post(url, headers=headers, json=data).json()
    if response["errcode"] == 40037:
        print("推送消息失败，请检查模板id是否正确")
    elif response["errcode"] == 40036:
        print("推送消息失败，请检查模板id是否为空")
    elif response["errcode"] == 40003:
        print("推送消息失败，请检查微信号是否正确")
    elif response["errcode"] == 0:
        print("推送消息成功")
    else:
        print(response)


if __name__ == "__main__":
    try:
        with open("./config.json", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("推送消息失败，请检查config.json文件是否与程序位于同一路径")
        os.system("pause")
        sys.exit(1)
    except json.JSONDecodeError:
        print("推送消息失败，请检查config.json格式是否正确")
        os.system("pause")
        sys.exit(1)

    # 和风天气参数：Key 优先走环境变量（GitHub Secrets），本地调试可回落到 config.json
    qw_key = os.getenv("QW_KEY") or config.get("qw_key", "")
    qw_host = config["qw_host"]
    qw_location = config["qw_location"]

    # 获取accessToken
    accessToken = get_access_token()
    # 接收的用户
    users = config["user"]
    # 传入省份和市获取天气信息
    province, city = config["province"], config["city"]
    weather, max_temperature, min_temperature = get_weather(qw_location, qw_key, qw_host)
    #获取天行API：优先读环境变量，本地调试回落到 config.json
    tianxing_API = os.getenv("TIANXING_API") or config["tianxing_API"]
    #是否开启天气预报API
    Whether_tip = to_bool(config["Whether_tip"])
    #是否启用词霸每日一句
    Whether_Eng = to_bool(config["Whether_Eng"])
    #是否启用星座API
    Whether_lucky = to_bool(config["Whether_lucky"])
    #是否启用励志古言API
    Whether_lizhi = to_bool(config["Whether_lizhi"])
    #是否启用彩虹屁API
    Whether_caihongpi = to_bool(config["Whether_caihongpi"])
    #是否启用健康小提示API
    Whether_health = to_bool(config["Whether_health"])
    #获取星座
    astro = config["astro"]
    # 获取词霸每日金句（注意顺序：函数返回 (英文, 中文)）
    note_en, note_ch = get_ciba()
    #彩虹屁
    pipi = caihongpi()
    #健康小提示
    health_tip = health()
# #下雨概率和建议
# tips = tip()
# pop  = tip_pop()

    #励志名言
    lizhi = lizhi()
    #星座运势
    lucky_ = lucky()
    # 公众号推送消息
    for user in users:
        send_message(user, accessToken, city, weather, max_temperature, min_temperature, pipi, lizhi, "", "", note_en, note_ch, health_tip, lucky_)
    import time
    time_duration = 3.5
    time.sleep(time_duration)
