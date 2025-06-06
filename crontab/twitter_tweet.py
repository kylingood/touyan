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
            map.twitter_id
        FROM guzi_member_twitter_map map
        JOIN (
            SELECT twitter_id, MAX(id) AS max_id
            FROM guzi_member_twitter_map
            WHERE status = 1
            GROUP BY twitter_id
        ) latest_map ON map.id = latest_map.max_id
        JOIN guzi_twitter t ON map.twitter_id = t.tid
        WHERE  t.updated_twitter < UNIX_TIMESTAMP() - 650
        ORDER BY map.id DESC 
    """
    data_list =  dbMysql.query(sql)
    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    #print(data_list)
    return data_list


MAX_CONCURRENT = 9  # 最多5个并发任务

semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def limited_async_getTweetByUserID(session, user_id):
    async with semaphore:
        return await async_getTweetByUserID(session, user_id)



# 批量任务入口
async def run_batch(user_ids):
    async with ClientSession(connector=TCPConnector(ssl=False)) as session:
        tasks = [limited_async_getTweetByUserID(session, uid) for uid in user_ids]
        results = await asyncio.gather(*tasks)
        return results


# 主入口函数（可直接运行）
def main():
    # 示例推特用户 ID 列表
    user_data = get_data()
    print(user_data)
    user_ids = [item['twitter_id'] for item in user_data]

    ### 多线程
    start = time.time()
    records = asyncio.run(run_batch(user_ids))
    print(f"\n🎉 获取完毕，共获取 {len(records)} 个用户推文，用时 {time.time() - start:.2f} 秒")


    for user_tweets in records:
        if user_tweets and isinstance(user_tweets, list):
            twitter_id = user_tweets[0].get('twitter_id', '未知用户')
            print(f"\n🧾 user_id={twitter_id} 返回推文条数: {len(user_tweets)}")
            ### 插入数据库
            insertTeeetToDB(user_tweets)
            # # 这里你还可以遍历打印每条推文详情，比如：
            # for tweet in user_tweets:
            #     print(tweet)

            try:
                today_time = int(time.time())
                channeldata = {}
                channeldata['updated_twitter'] = today_time
                result = dbMysql.table('guzi_twitter').where(f"tid = '{twitter_id}'").save(channeldata)
                print("执行SQL:", dbMysql.getLastSql())
                print("更新结果:", result)  # 一般是影响行数
                # dbMysql.commit()  # 如果需要手动提交

            except Exception as e:
                print("更新失败:", e)

        else:
            print("\n🧾 该用户无推文或数据为空")

            # 4. 更新信息抓取的时间，减少抓取量



if __name__ == "__main__":
    main()


exit()
