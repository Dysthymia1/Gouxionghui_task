from datetime import datetime

import requests
import time
import random
import urllib3
import csv
from urllib3.util.retry import Retry

from common import  url_to_mid

# ==================== 【全局设置区】 ====================
TIME_OUT_TIMES = 10
RETRY_TIME = 10
SORT_TYPE = 1  #  0为按热度，1为按时间

# 微博帖子 ID（从 URL 或者接口中获取）
WEIBO_ID = "Phq0IBkx5"
mid = url_to_mid(WEIBO_ID)

custom_filename = f"{WEIBO_ID}_{SORT_TYPE}.csv"

# 你的 Cookie（带有效的登录态）
with open('../resources/cookie/weibo.txt', 'rt', encoding='utf-8') as f:
    COOKIE = f.read().strip()

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 自定义请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://weibo.com/',
    'Cookie': COOKIE
}

# 配置重试机制（失败自动重试）
retry_strategy = Retry(
    total=RETRY_TIME,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"],
    connect=True,
    read=True
)

# 全局重试计数器
attempt_count = 0

total_pages = None

def parse_comment(comment,is_child,csv_writer):
    # 评论 ID / 用户 UID / 评论内容 / 点赞数 / 等等
    # print(comment)
    c_id = comment["id"]
    root_id = comment["rootid"]
    user_info = comment["user"]
    nickname = user_info.get("screen_name")
    gender_raw = user_info.get('gender')
    if gender_raw == 'm':
        gender = '男'
    elif gender_raw == 'f':
        gender = '女'
    else:
        gender = '未知'
    level = 0  # 会员等级或微博等级，仅示意

    # 获取粉丝数
    fans_count = user_info.get("followers_count")

    ip_location_raw = comment["source"]
    if ip_location_raw.startswith("来自"):
        ip_location = ip_location_raw.replace("来自", "").strip()
    else:
        ip_location = ip_location_raw

    created_at_raw = comment.get('created_at')
    input_format = '%a %b %d %H:%M:%S %z %Y'
    dt = datetime.strptime(created_at_raw, input_format)
    output_format = '%Y-%m-%d %H:%M:%S'
    created_at_formatted = dt.strftime(output_format)
    # 评论文本
    text = comment["text_raw"]
    like_count = comment["like_counts"]

    # 整理一条记录
    record = {
        "comment_id": c_id,
        "nickname": nickname,
        "gender": gender,
        "level": level,
        "followers": fans_count if fans_count else 0,
        "address": ip_location,
        "content": text,
        "likes": like_count,
        "time": created_at_formatted,
        "hierarchy": "子评论" if is_child else "根评论",
        "root_id": root_id if is_child else c_id,
    }
    # 写入 CSV
    if csv_writer:
        csv_writer.writerow(record.values())

# ==================== 【核心函数：获取评论 & 递归子评论】 ====================
def fetch_comments(csv_writer=None):
    """
    爬取单页微博评论或指定评论的子评论，并写入 CSV。
    :param csv_writer: CSV 写入器
    """
    global attempt_count, total_pages

    page = 1

    while True:
        url = ""
        if SORT_TYPE == 0:
            url = (f"https://weibo.com/ajax/statuses/buildComments?"
                   f"flow=0&"
                   f"is_show_bulletin=2&"
                   f"id={mid}&"
                   f"page={page}&"
                   f"count=20")
        elif SORT_TYPE == 1:
            url = (f"https://weibo.com/ajax/statuses/buildComments?"
                   f"is_asc=0&"
                   f"is_show_bulletin=0&"
                   f"id={mid}&"
                   f"page={page}&"
                   f"count=20")
        print(f"正在读取链接 {url}")
        print(f"正在爬取第 {page} 页评论...")

        try:
            response = requests.get(url, headers=headers, timeout=TIME_OUT_TIMES, verify=False)
            data = response.json()

            if total_pages is None :
                size = 20
                total_pages = data["total_number"] // size

            comment_list = data["data"]
            if not comment_list:
                print(f"评论列表为空，结束抓取。当前页数: {page}")
                break

            if SORT_TYPE == 0:
                # 处理本页的所有评论
                for comment in comment_list:
                    if comment["total_number"] !=0 :
                        for sub_comment in comment["comments"]:
                            print(f"正在爬取根评论{comment['id']}子评论{sub_comment['id']}")
                            parse_comment(sub_comment,True,csv_writer)
                    print(f"正在爬取根评论{comment['id']}")
                    parse_comment(comment,False,csv_writer)
            elif SORT_TYPE == 1:
                for comment in comment_list:
                    print(comment)
                    if "reply_comment" in comment:
                        print(f"正在爬取根评论{comment.get('rootid')}子评论{comment.get('id')}")
                        parse_comment(comment, True, csv_writer)
                    else:
                        print(f"正在爬取根评论{comment['id']}")
                        parse_comment(comment, False, csv_writer)


            # 翻页逻辑
            if page >= total_pages:
                break
            print(f"已爬取第 {page} 页")
            page += 1
            time.sleep(random.uniform(1, 2))  # 随机睡眠，避免频率过高

        except requests.exceptions.ReadTimeout:
            attempt_count += 1
            print(f"读取超时！第 {attempt_count} 次尝试重新连接...")
            time.sleep(3)
        except requests.exceptions.ConnectionError as e:
            attempt_count += 1
            print(f"连接错误！第 {attempt_count} 次尝试重新连接: {e}")
            time.sleep(3)
        except Exception as e:
            print(f"[异常] {e}")
            break


# ==================== 【主函数：边爬边存储到 CSV】 ====================
def save_comments_immediately():
    """
    直接启动爬虫，将微博评论抓取后即时写入 CSV 文件
    """
    # 先获取微博基础信息（如果需要）
    # 比如获取博主 UID 等信息
    with open(f"../../result/task2/weibo/{custom_filename}", mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # CSV 表头
        writer.writerow(["ID", "nickname", "gender", "level", "followers", 'address',
                         "content", "likes", "time", "hierarchy", "rootID"])
        # 开始爬取
        fetch_comments(csv_writer=writer)

    print("爬取完成！")


if __name__ == "__main__":
    save_comments_immediately()