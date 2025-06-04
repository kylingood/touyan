import requests
import time
import random
from datetime import datetime
import json
import asyncio
from src.rapidapi import *
from util.utils import get_countdown
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.web3_auth import get_message_db,insert_message_db

# 并发限制：最多 20 个任务同时执行
semaphore = asyncio.Semaphore(3)

# 假设这是你的异步插入函数
async def get_message_db_limited(item):
    #async with semaphore:
    return await get_message_db(item)  # 原来的插入逻辑


# 同步获取数据
def get_data():
    sql = '''
        SELECT 
        dc.*, 
        d.token AS discord_token 
    FROM 
        guzi_discord_channel dc
    LEFT JOIN 
        guzi_discord d ON dc.did = d.id
    WHERE 
        dc.status = 1 AND dc.updated_message < UNIX_TIMESTAMP() - 600
    ORDER BY 
        dc.id DESC  
    '''
    data_list = dbMysql.query(sql)
    return data_list

# 主逻辑
async def main():
    data = get_data()
    if not data:
        print("最近10分钟内，没有要更新的数据~")
        return

    tasks = [get_message_db_limited(item) for item in data]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for item, message_info in zip(data, results):
        # 这里你同时拿到了 item 和对应的 message_info
        insert_message_db(item, message_info)


# 程序入口
if __name__ == '__main__':

    asyncio.run(main())