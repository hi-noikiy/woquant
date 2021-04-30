# @Time : 2021/3/30 19:37
# @Author : LiuBin
# @File : 电影因子.py
# @Description : 
# @Software: PyCharm
import re
import requests
from bs4 import BeautifulSoup


url = "https://maoyan.com/films?showType=2&sortId=1"
html_doc = requests.get(url,headers="Cookie:__mta=250968761.1618065217924.1618068509686.1618068543731.30; _lxsdk_cuid=178bc0f084bc8-0b9a1b74bc139-5c3f1e49-240000-178bc0f084bc8; theme=moviepro; uuid_n_v=v1; uuid=AEAE65209A0911EBB42F254FB366F3A85F62C98D08BB4585915FDB8352380FB3; _csrf=97467a17cd1177f8ccc0aa2b7061629b79bd3d60f987102c4970a151b91560d2; Hm_lvt_703e94591e87be68cc8da0da7cbd0be2=1618065197; _lxsdk=AEAE65209A0911EBB42F254FB366F3A85F62C98D08BB4585915FDB8352380FB3; _lx_utm=utm_source%3DBaidu%26utm_medium%3Dorganic; Hm_lpvt_703e94591e87be68cc8da0da7cbd0be2=1618068887; __mta=250968761.1618065217924.1618068543731.1618068886763.31; _lxsdk_s=178bc0f084c-f91-32d-9e6%7C%7C296").content
soup = BeautifulSoup(html_doc, 'html.parser')
print(soup.prettify())
print(soup.find_all('dd'))