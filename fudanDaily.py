import sys
import json
import time
import hashlib
import requests
import mail
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from os import path as os_path

fudan_daily_url = "https://zlapp.fudan.edu.cn/site/ncov/fudanDaily"
login_url = "https://uis.fudan.edu.cn/authserver/login?service=https%3A%2F%2Fzlapp.fudan.edu.cn%2Fa_fudanzlapp%2Fapi" \
            "%2Fsso%2Findex%3Fredirect%3Dhttps%253A%252F%252Fzlapp.fudan.edu.cn%252Fsite%252Fncov%252FfudanDaily" \
            "%26from%3Dwap "
get_info_url = "https://zlapp.fudan.edu.cn/ncov/wap/fudan/get-info"
save_log_url = "https://zlapp.fudan.edu.cn/wap/log/save-log"
save_url = "https://zlapp.fudan.edu.cn/ncov/wap/fudan/save"


def get_session(_login_info):
    _session = requests.Session()
    _session.headers[
        "User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.18(0x17001229) NetType/WIFI Language/zh_CN miniProgram"

    _response = _session.get(login_url)
    soup = BeautifulSoup(_response.text, "lxml")
    inputs = soup.find_all("input")
    for i in inputs:
        if i.get("name") and i.get("name") not in ["username", "password", "captchaResponse"]:
            _login_info[i.get("name")] = i.get("value")
    _session.post(login_url, data=_login_info)

    _session.headers["Origin"] = "https://zlapp.fudan.edu.cn"
    _session.headers["Referer"] = fudan_daily_url
    return _session


def get_historical_info(_session):
    response = session.get(get_info_url)
    return json.loads(response.text)["d"]


def get_today_date():
    _tz = timezone(+timedelta(hours=8))
    return datetime.now(_tz).strftime("%Y%m%d")


def save_log(_session):
    _data = {
        "appkey": "ncov",
        "url": fudan_daily_url,
        "timestamp": int(time.time())
    }
    _data["signature"] = hashlib.md5((_data["appkey"] + str(_data["timestamp"]) + _data["url"]).encode()).hexdigest()
    _session.post(save_log_url, data=_data)


def get_payload(_historical_info):
    _payload = _historical_info["info"]
    if "jrdqjcqk" in _payload:
        _payload.pop("jrdqjcqk")
    if "jrdqtlqk" in _payload:
        _payload.pop("jrdqtlqk")

    _payload.update({
        "ismoved": 0,
        "number": _historical_info["uinfo"]["role"]["number"],
        "realname": _historical_info["uinfo"]["realname"],
        "sfhbtl": 0,
        "sfjcgrq": 0
    })

    if not _payload["area"]:
        _payload.update({
            "area": _historical_info["oldInfo"]["area"],
            "city": _historical_info["oldInfo"]["city"],
            "province": _historical_info["oldInfo"]["province"]
        })

    return _payload


def get_payload_str(_payload):
    _ = _payload.copy()
    _["geo_api_info"] = json.loads(_["geo_api_info"])
    return json.dumps(_, ensure_ascii=False)


def save(_session, _payload):
    return _session.post(save_url, data=_payload)


def notify(SENDER, TOKEN, USERMAIL, _title, _message=None):
    if not TOKEN:
        print("未配置TOKEN！")
        return

    if not _message:
        _message = _title
    print(_title)
    print(_message)
    flag = mail.mail(SENDER, TOKEN, USERMAIL, _title, _message)
    if flag:
        print("邮件发送成功")
    else:
        print("邮件发送失败")



def set_user():
    users_info = []
    if os_path.exists("users.txt"):
        with open("users.txt", "r") as f:
            lines = f.readlines()
            for line in lines:
                if len(line) < 5:
                    continue
                line = line.strip()
                user_info = line.split(':')
                users_info.append(user_info)
    else:
        print("users.txt NOT FOUND. Initialising for user info")
        username = input("username:")
        password = input("password:")
        usermail = input("mail:")
        mail_info_str = (username, password)
        with open("users.txt", "w") as f:
            f.writelines(':'.join(mail_info_str))
            y = input("是否继续添加,是请输入y")
            while y == "y":
                print("继续添加用户")
                username = input("username:")
                password = input("password:")
                usermail = input("mail:")
                f.writelines(':'.join(mail_info_str))
                y = input("是否继续添加,是请输入y")
        users_info.append((username, password, usermail))
    return users_info


if __name__ == "__main__":
    users = set_user()
    SENDER, TOKEN = mail.set_mail_sender()
    for u in users:
        USERNAME = u[0]
        PASSWORD = u[1]
        USERMAIL = u[2]
        if not USERNAME or not PASSWORD or not USERMAIL:
            notify("请正确配置用户名和密码或未输入接收邮箱！")
            sys.exit()
        login_info = {
            "username": USERNAME,
            "password": PASSWORD,
            "usermail": USERMAIL
        }

        try:
            session = get_session(login_info)
            historical_info = get_historical_info(session)
            save_log(session)

            payload = get_payload(historical_info)
            payload_str = get_payload_str(payload)
            # print(payload_str)

            if payload.get("date") == get_today_date():
                notify(SENDER, TOKEN, USERMAIL, f"今日已打卡：{payload.get('area')}", f"今日已打卡：{payload_str}")
                sys.exit()

            time.sleep(5)
            response = save(session, payload)

            if response.status_code == 200 and response.text == '{"e":0,"m":"操作成功","d":{}}':
                notify(SENDER, TOKEN, USERMAIL, f"打卡成功：{payload.get('area')}", payload_str)
            else:
                notify(SENDER, TOKEN, USERMAIL, "打卡失败，请手动打卡", response.text)

        except Exception as e:
            notify(SENDER, TOKEN, USERMAIL, "打卡失败，请手动打卡", str(e))
