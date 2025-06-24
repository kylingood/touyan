import requests
import time
import random
from datetime import datetime
import json
from src.asyn_rapidapi import *
from util.utils import get_countdown
from crontab.db import *
import aiohttp
from aiohttp import ClientSession, TCPConnector
import asyncio
import time



def get_data():
    ### 先查到所有推特账号
    sql = """
        SELECT
            map.twitter_id,
            map.uid
        FROM guzi_member_twitter_map map
        JOIN (
            SELECT twitter_id, MAX(id) AS max_id
            FROM guzi_member_twitter_map
            WHERE status = 1
            GROUP BY twitter_id
        ) latest_map ON map.id = latest_map.max_id
        JOIN guzi_twitter t ON map.twitter_id = t.tid
        WHERE  t.updated_fans < UNIX_TIMESTAMP() - 10850
        ORDER BY map.id DESC
    """

    # update_time = 10800 ##距上次API抓取超过3小时
    # sql = f"""
    #     SELECT
    #         map.twitter_id,
    #         map.uid
    #     FROM guzi_member_twitter_map map
    #     JOIN (
    #         SELECT twitter_id, MAX(id) AS max_id
    #         FROM guzi_member_twitter_map
    #         WHERE status = 1
    #         GROUP BY twitter_id
    #     ) latest_map ON map.id = latest_map.max_id
    #     JOIN guzi_twitter t ON map.twitter_id = t.tid
    #     JOIN guzi_member m ON map.uid = m.uid
    #     WHERE
    #         t.status = 1                                                 -- 推特账号有效
    #         AND IFNULL(t.updated_fans, 0) < UNIX_TIMESTAMP() - {update_time}      -- 粉丝数据超过1小时未更新
    #         AND IFNULL(m.active_time, 0) > UNIX_TIMESTAMP() - 7200       -- 用户最近2小时登录过
    #         AND IFNULL(m.last_fetch_fans_time, 0) < UNIX_TIMESTAMP() - {update_time} -- 用户上次抓粉丝超1小时
    #     ORDER BY map.id DESC;
    #
    #     """

    # sql = """
    #     SELECT
    #         map.twitter_id,
    #         map.uid
    #     FROM guzi_member_twitter_map map
    #     JOIN (
    #         SELECT twitter_id, MAX(id) AS max_id
    #         FROM guzi_member_twitter_map
    #         WHERE status = 1
    #         GROUP BY twitter_id
    #     ) latest_map ON map.id = latest_map.max_id
    #     JOIN guzi_twitter t ON map.twitter_id = t.tid
    #     WHERE  t.updated_fans < UNIX_TIMESTAMP() - 10850
    #     ORDER BY map.id DESC Limit 1
    # """

    data_list =  dbMysql.query(sql)
    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    print(sql)
    return data_list




MAX_CONCURRENT = 5  # 最多 5 个并发任务
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

# 限制并发包装器
async def limited_async_getFollowingsByUserID(session, user_id, sum_user=50):
    async with semaphore:
        print(f"🚀 开始抓取 {user_id}")
        result = await async_getFollowingsByUserID(session, user_id, sum_user=sum_user)
        print(f"✅ 完成 {user_id}，共获取 {len(result)} 个 followings")
        return {"user_id": user_id, "followings": result}

# 批量抓取入口函数
async def run_batch(user_ids, sum_user=100):
    async with ClientSession(connector=TCPConnector(ssl=False)) as session:
        tasks = [
            limited_async_getFollowingsByUserID(session, uid, sum_user=sum_user)
            for uid in user_ids
        ]
        return await asyncio.gather(*tasks)




# 示例主函数
async def main():

    # 示例推特用户 ID 列表
    # user_ids = ["44196397", "813286", "1339835893"]  # 示例 ID 列表
    user_data = get_data()
    print(user_data)

    ###去重uid
    uids = list(set(item['uid'] for item in user_data))
    # 把用户抓取时间更新
    for uid in uids:
        dbdata = {}
        today_time = int(time.time())
        dbdata['last_fetch_fans_time'] = today_time
        dbMysql.table('guzi_member').where(f"uid = '{uid}'").save(dbdata)
        print("执行SQL:", dbMysql.getLastSql())


    user_ids = [item['twitter_id'] for item in user_data]
    records = await run_batch(user_ids)

    for one_user in records:
        twitter_id = one_user['user_id']
        followings = one_user['followings']

        # 数据入库
        insertUserDataToDB(followings, twitter_id=twitter_id)

        print(f"\n🔍 user_id={twitter_id} 的前 5 个 followings：")
        for u in one_user["followings"][:5]:
            print(u)

        ##更新更新时间
        try:
            today_time = int(time.time())
            channeldata = {}
            channeldata['updated_fans'] = today_time
            result = dbMysql.table('guzi_twitter').where(f"tid = '{twitter_id}'").save(channeldata)
            print("执行SQL:", dbMysql.getLastSql())
            print("更新结果:", result)  # 一般是影响行数
            # dbMysql.commit()  # 如果需要手动提交

        except Exception as e:
            print("更新失败:", e)



if __name__ == "__main__":
    asyncio.run(main())
