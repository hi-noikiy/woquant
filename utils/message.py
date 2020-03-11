from configparser import ConfigParser
from config import PROJECT_DIR
import os
import requests

# 配置文件
conf = ConfigParser()
conf.read(os.path.join(PROJECT_DIR, "config/base.conf"), encoding="utf-8")

# 整理发送消息
static_url = conf.get("Flask", "url")
report_message = ["[{0}]({1})".format(k.split(".")[0], os.path.join(static_url, k)) for k, v in conf.items("Message")
                  if
                  v == 'report']

# 发送人
for user, sckey in conf.items('WX'):
    url = "https://sc.ftqq.com/{sckey}.send?text={title}&desp={content}"
    requests.get(url.format(sckey=sckey, title="每日复盘", content=" ".join(report_message)))
