import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from os import path as os_path


def set_mail_sender():
    if os_path.exists("token.txt"):
        with open("token.txt", "r") as f:
            line = f.readline()
            user_info = line.split(':')
            usermail = user_info[0]
            token = user_info[1]
    else:
        print("push.txt NOT FOUND. Initialising for token")
        with open("token.txt", "w") as f:
            usermail = input("mail:")
            token = input("输入token:")
            mail_info_str = (usermail, token)
            f.writelines(':'.join(mail_info_str))
    return usermail, token


def mail(_sender, _token, _user, _tile, _text):
    ret = True
    try:
        msg = MIMEText(_text, 'plain', 'utf-8')
        msg['From'] = formataddr(["liuzunxiong", _sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To'] = formataddr(["receive", _user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject'] = _tile  # 邮件的主题，也可以说是标题

        server = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器，端口是465
        server.login(_sender, _token)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(_sender, [_user, ], msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
    except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        ret = False
    return ret
