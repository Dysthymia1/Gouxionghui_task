import csv
import math

import requests
import pandas as pd
import time

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局参数
TIME_OUT_TIMES = 5
RETRY_TIMES = 5
MODE = 3  # 按时间=2, 按热度=3,
SLEEP_TIME = random.uniform(0.3, 0.4)
START = 1
END = 9999

# 动态 ID（从 URL 提取的）
DYNAMIC_ID = '1040427588061757445'
custom_filename = f"{DYNAMIC_ID}_{MODE}.csv"



with open('../resources/cookie/bilibili.txt', 'rt', encoding='utf-8') as f:
    COOKIE = f.read().strip()
cookie_dic = dict([l.split("=", 1) for l in COOKIE.split("; ")])
bili_jct = cookie_dic['bili_jct']

# 自定义请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Cookie': COOKIE,
    'csrf': bili_jct,
}


def create_session():
    session = requests.Session()
    retry = Retry(total=RETRY_TIMES,
                  backoff_factor=0.1,
                  status_forcelist=[500, 502, 503, 504],
                  allowed_methods=["HEAD", "GET", "OPTIONS"],
                  connect=True,
                  read=True)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session


def make_request_with_retry(session, url, params=None):
    attempts = 0
    while attempts < RETRY_TIMES:
        try:
            response = session.get(url,
                                   params=params,
                                   headers=headers,
                                   timeout=TIME_OUT_TIMES,
                                   allow_redirects=False,
                                   verify=True)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"请求失败，重试第 {attempts + 1} 次: {e}")
            attempts += 1
            time.sleep(SLEEP_TIME+10)
            continue
    return None


# ==================== 【获取真实 oid】 ====================
def get_real_oid(session):
    url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?id={DYNAMIC_ID}'
    response = make_request_with_retry(session, url)
    data = response.json()
    if data['code'] != 0:
        raise Exception(f"获取动态详情失败: {data['message']}")
    # 定位动态类型
    major = data['data']['item']['modules']['module_dynamic']['major']
    # 视频动态
    if major['type'] == 'MAJOR_TYPE_ARCHIVE':
        oid = major['archive']['aid']
        type_id = 1
        print(f"解析成功！类型: 视频 | oid: {oid}, type_id: {type_id}")
    # 图片动态
    elif major['type'] == 'MAJOR_TYPE_DRAW':
        oid = major['draw']['id']
        type_id = 11
        print(f"解析成功！类型: 图片 | oid: {oid}, type_id: {type_id}")
    # 专栏动态
    elif major['type'] == 'MAJOR_TYPE_ARTICLE':
        oid = major['article']['id']
        type_id = 12
        print(f"解析成功！类型: 专栏 | oid: {oid}, type_id: {type_id}")
    else:
        raise Exception(f"不支持的动态类型: {major['type']}")
    return oid, type_id


def get_fans_count(session, mid):
    """
    根据给定 mid，返回用户的粉丝数
    支持失败时重试，最多重试 max_retries 次
    """
    fans_url = f"https://api.bilibili.com/x/relation/stat?vmid={mid}&jsonp=jsonp"
    fans_resp = make_request_with_retry(session, fans_url)
    if fans_resp.status_code == 200:
        fans_data = fans_resp.json()
        fans_count = fans_data["data"]["follower"]
        return fans_count


def extract_comment_fields(session, comment, is_child=False):
    ID = str(comment['rpid'])
    nickname = comment['member']['uname']
    gender = comment['member']['sex']
    level = comment['member']['level_info']['current_level']
    followers = get_fans_count(session, comment['member']['mid'])
    address = comment['reply_control'].get('location', '未知').replace('IP属地：', '')
    content = comment['content']['message'].replace('\n', '，').replace('\r', '').replace('"', '“').replace(',', '，').strip()
    likes = comment['like']
    ftime = pd.to_datetime(comment['ctime'], unit='s').strftime("%Y-%m-%d %H:%M:%S")
    hierarchy = '子评论' if is_child else '根评论'
    rootID = str(comment['root']) if is_child else str(comment['rpid'])
    return [ID, nickname, gender, level, followers, address, content, likes, ftime, hierarchy, rootID]


def write_to_csv(path, rows, is_title=False):
    try:
        with open(path, mode='w' if is_title else 'a', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            if is_title:
                writer.writerow(['ID',
                                 'nickname',
                                 'gender',
                                 'level',
                                 'followers',
                                 'address',
                                 'content',
                                 'likes',
                                 'time',
                                 'hierarchy',
                                 'rootID'])
            else:
                writer.writerows(rows)
    except Exception as e:
        print(f"写入文件时出现错误: {e}")


def fetch_secondary_comments(session, oid, type_id, root_rpid):
    url = 'https://api.bilibili.com/x/v2/reply/reply'
    params = {
        'oid': oid,
        'type': type_id,
        'ps': 20,
        'root': root_rpid
    }
    first_response = make_request_with_retry(session, url, params)
    if first_response.status_code != 200:
        print("访问异常")
        return
    json_data = first_response.json()
    count = json_data['data'].get('page', {}).get('count', 0)
    total_pages = math.ceil(count / 20)

    for page in range(1, total_pages + 1):
        try:
            all_comments = []
            params['pn'] = page
            response = make_request_with_retry(session, url, params)
            if response.status_code == 200 or not response["data"].get("replies"):
                json_data = response.json()
                replies = json_data['data'].get('replies', [])
                for reply in replies:
                    row = extract_comment_fields(session, reply, is_child=True)
                    all_comments.append(row)
                write_to_csv(custom_filename, all_comments)
                print(f"写入根id为 {root_rpid} 的 {len(all_comments)} 条子评论（第 {page} 页）")
            else:
                print(f"获取根id为 {root_rpid} 的第 {page} 页二级评论失败")
            time.sleep(SLEEP_TIME)
        except requests.exceptions.ReadTimeout:
            print(f"读取超时！尝试重新连接...")
            time.sleep(SLEEP_TIME)
        except requests.exceptions.ConnectionError:
            print(f"连接错误！尝试重新连接...")
            time.sleep(SLEEP_TIME)
        except Exception as e:
            print(f"[异常] {e}")
            break


def fetch_main_comments(session, oid, type_id):
    url = 'https://api.bilibili.com/x/v2/reply/main'
    if MODE == 2:
        page = 0
    else:
        page = 1
    while True:
        all_comments = []
        try:
            params = {'next': str(page),
                      'oid': oid,
                      'type': type_id,
                      'ps': 20,
                      'mode': MODE}
            response = make_request_with_retry(session, url, params)
            json_data = response.json()
            replies = json_data['data'].get('replies', [])
            if not replies:
                print(f"第 {page} 页无评论")
                break
            if MODE == 2:
                if page == 0:
                    page = json_data['data'].get("cursor",[]).get("prev")
                else:
                    page = json_data['data'].get("cursor",[]).get("next")
            else:
                page += 1
            for reply in replies:
                row = extract_comment_fields(session, reply, is_child=False)
                all_comments.append(row)
                if reply['replies']:
                    # for secondary_reply in reply['replies']:
                    #     secondary_row = extract_comment_fields(session, secondary_reply, is_child=True)
                    #     all_comments.append(secondary_row)
                    # print(f"抓取 {reply['rpid']} 的子评论")
                    fetch_secondary_comments(session, oid, type_id, reply['rpid'])
                else:
                    print(f"{reply['rpid']} 无子评论")
            write_to_csv(custom_filename, all_comments)
            print(f"完成第 {page} 页抓取, 抓取到 {len(all_comments)} 条评论")
            time.sleep(SLEEP_TIME)
            if json_data['data'].get("cursor", []).get("is_end"):
                break
        except requests.exceptions.ReadTimeout:
            print(f"读取超时！尝试重新连接...")
            time.sleep(SLEEP_TIME)
        except requests.exceptions.ConnectionError:
            print(f"连接错误！尝试重新连接...")
            time.sleep(SLEEP_TIME)
        except Exception as e:
            print(f"[异常] {e}")
            break


# ----------- 主入口 -------------
def main():
    write_to_csv(custom_filename, None, True)

    session = create_session()

    oid, type_id = get_real_oid(session)

    print("开始抓取")
    fetch_main_comments(session, oid, type_id)

    print("全部抓取完成")


if __name__ == '__main__':
    main()
