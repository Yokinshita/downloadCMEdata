import requests
from datetime import datetime
import re
from tqdm import tqdm
import json
import os
import urllib.parse as parse
import threading

save_location = r'D:\Programming\CME_data'
year, month, day = 2013, 8, 1
# 记录所有CME的链接
CME_all_list_url = 'https://cdaw.gsfc.nasa.gov/CME_list/'
# 记录每月CME的链接
CME_month_list_url = 'https://cdaw.gsfc.nasa.gov/CME_list/UNIVERSAL/{0}_{1:0>2d}/univ{0}_{1:0>2d}.html'.format(
    year, month)
# 记录每日CME的图像的链接
CME_daily_pics_url = 'https://cdaw.gsfc.nasa.gov/images/soho/lasco/{0:}/{1:0>2d}/{2:0>2d}/'.format(
    year, month, day)
json_filename = os.path.join(
    save_location, 'CMElist\{}_{}_{}_CMEList.json'.format(year, month, day))


def read_CME_list_json(json_filename: str):
    # 从CME json文件夹中还原数据，重新生成一个包含一个月中CME事件的列表
    with open(json_filename, 'r') as f:
        CME_month_appear_datetime_list = json.load(f)
    for CME_month_appear_datetime in CME_month_appear_datetime_list:
        CME_month_appear_datetime['appear'] = datetime.strptime(
            CME_month_appear_datetime['appear'], '%Y%m%d %H%M%S')
        CME_month_appear_datetime['start'] = datetime.strptime(
            CME_month_appear_datetime['start'], '%Y%m%d %H%M%S')
        CME_month_appear_datetime['end'] = datetime.strptime(
            CME_month_appear_datetime['end'], '%Y%m%d %H%M%S')
    return CME_month_appear_datetime_list


def determine_CME(pic_time: datetime, CME_month_appear_datetime_list: list):
    remark = None
    is_CME = False
    for CME_incident in CME_month_appear_datetime_list:
        if pic_time > CME_incident['appear'] and pic_time < CME_incident['end']:
            is_CME = True
            remark = CME_incident['remark']
            # 发现该图片在哪一次CME事件期间，就可以停止继续遍历后面的事件
            break
    # 若图片的pictime不在任何一次CME事件的起止时间内，认为该图片不是CME，其remark和is_CME就是None和False
    return remark, is_CME


# 判断是否存在path文件夹，若无则创建
def create_file(path):
    if not os.path.exists(path):
        os.makedirs(path)


def download_sigle_pic(pic_url: str, save_location: str, remark: str, is_CME: bool):
    pic_filename = pic_url.split('/')[-1]
    if is_CME is True and len(remark) == 0:
        remark = 'No Remark'
    if is_CME:  # 若是CME
        # 创建\CME\remark文件夹
        create_file(os.path.join(save_location, 'CME\\'+remark))
        # 下载文件
        try:
            res = requests.get(pic_url)
        except Exception:  # 若下载出现错误，直接返回
            print('Error:download pic {} fail'.format(pic_filename))
            return None
        with open(os.path.join(save_location, 'CME\\'+remark, pic_filename), 'wb') as f:
            f.write(res.content)
            print('{} download complete'.format(pic_filename))
    else:  # 若不是CME
        create_file(os.path.join(save_location, 'No CME'))
        try:
            res = requests.get(pic_url)
        except Exception:
            print('Error:download pic {} fail'.format(pic_filename))
            return None
        with open(os.path.join(save_location, 'No CME', pic_filename), 'wb') as f:
            f.write(res.content)
            print('{} download complete'.format(pic_filename))


CME_month_appear_datetime_list = read_CME_list_json(json_filename)
daily_pic_list = []  # 包含该日所有图片的链接、remarks以及是否是CME事件
daily_pic_page = requests.get(CME_daily_pics_url)
pic_href_regex = re.compile(r'<a href="\d{8}_\d{6}_lasc2rdf_aia193rdf.png">')
hrefs = pic_href_regex.findall(daily_pic_page.text)
print('已经获取{0:}/{1:0>2d}/{2:0>2d}的图片地址共{3:}张'.format(year, month, day, len(hrefs)))
pic_datetime_regex = re.compile(
    'href="(\d{8})_(\d{6})_')  # 用来识别href中图片时间的正则表达式
pic_href_regex = re.compile('href="(.*)"')  # 用来识别href中图片文件名的正则表达式
for href in hrefs:
    # pic_time包含了该图片的拍摄时间
    pic_time = pic_datetime_regex.findall(
        href)[0][0]+' '+pic_datetime_regex.findall(href)[0][1]
    pic_time = datetime.strptime(pic_time, '%Y%m%d %H%M%S')

    pic_dict = {}  # 包含了该图片url、标记、是否是CME的字典
    # 一张图片的URL类似于
    # https://cdaw.gsfc.nasa.gov/images/soho/lasco/2013/08/01/20130801_004805_lasc2rdf.png
    pic_filename = pic_href_regex.findall(href)[0]
    url = parse.urljoin(CME_daily_pics_url, pic_filename)
    pic_dict['url'] = url
    remark, is_CME = determine_CME(pic_time, CME_month_appear_datetime_list)
    pic_dict['remark'] = remark
    pic_dict['is_CME'] = is_CME
    daily_pic_list.append(pic_dict)

while True:
    if daily_pic_list:
        pic = daily_pic_list.pop()
        url = pic['url']
        remark = pic['remark']
        is_CME = pic['is_CME']
        download_sigle_pic(url, save_location, remark, is_CME)
    else:
        break
