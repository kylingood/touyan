import requests
import time
import random
from datetime import datetime
import json
from src.rapidapi import *
from util.utils import get_countdown
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_data():
    ### 先查到所有推特账号
    sql = """
        SELECT
            map.*,
            t.id AS twitter_id,
            t.uid AS twitter_uid,
            t.tid AS twitter_tid,
            t.username AS twitter_username,
            t.show_name AS twitter_show_name,
            t.url AS twitter_url,
            t.remark AS twitter_remark,
            t.description AS twitter_description,
            t.avatar AS twitter_avatar,
            t.followers AS twitter_followers,
            t.fans AS twitter_fans,
            t.status AS twitter_status,
            t.created AS twitter_created,
            t.updated AS twitter_updated
        FROM guzi_member_twitter_map map
        JOIN (
            SELECT twitter_id, MAX(id) AS max_id
            FROM guzi_member_twitter_map
            WHERE status = 1
            GROUP BY twitter_id
        ) latest_map ON map.id = latest_map.max_id
        JOIN guzi_twitter t ON map.twitter_id = t.tid
        WHERE  t.updated_message < UNIX_TIMESTAMP() - 300
        ORDER BY map.id DESC;
    """
    data_list =  dbMysql.query(sql)
    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    #print(data_list)
    return data_list

# 单个用户的处理逻辑
def process_member(member,sum_user=None):
    twitter_username = member['twitter_username']
    twitter_id = member['twitter_tid']

    try:
        print(f"开始处理账号：{twitter_username}\n ")

        # # 1. 抓取该账号的推文
        getTweetByUserID(twitter_id)

        # 2. 抓取关注列表
        records = getFollowingsByUserID(twitter_id,sum_user)
        print(f"\n共获取账号：{twitter_username} 的 {len(records)} 个关注用户\n")

        # 3. 入库
        insertUserDataToDB(records, twitter_id=twitter_id)

        # 4. 更新信息抓取的时间，减少抓取量
        try:
            today_time = int(time.time())
            channeldata = {}
            channeldata['updated_message'] = today_time
            result = dbMysql.table('guzi_twitter').where(f"tid = '{twitter_id}'").save(channeldata)
            print("执行SQL:", dbMysql.getLastSql())
            print("更新结果:", result)  # 一般是影响行数
            # dbMysql.commit()  # 如果需要手动提交

        except Exception as e:
            print("更新失败:", e)

        # 5. 随机等待 1~3 秒，防止 Twitter 限流
        sleep_time = random.uniform(1, 3)
        print(f"账号 {twitter_username} 处理完毕，休息 {sleep_time:.2f} 秒防止限流...\n")
        time.sleep(sleep_time)



        return f"{twitter_username} ✅ 处理成功"

    except Exception as e:
        return f"{twitter_username} ❌ 处理失败：{e}"


# 多线程处理所有用户
def process_all(data_list, max_threads=5, sum_user = None):
    results = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:

        futures = [executor.submit(process_member, member,sum_user) for member in data_list]
        for future in as_completed(futures):
            result = future.result()
            print(result)
            results.append(result)

    return results



# data_list = get_data()
# print(data_list)
# ###只跑一次
# results = process_all(data_list, max_threads=1, sum_user=20)


###循环执行
while True:
    data_list = get_data()
    results = process_all(data_list, max_threads=1, sum_user=20)
    print("执行完一次，等待 20 分钟...")
    get_countdown(30 * 60)  # 20 分钟



exit()

