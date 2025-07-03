import requests
import time
from datetime import datetime
import json
from util.db import *


import requests

def generate_new_password(length=12):
    import random, string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

with open('accounts.txt', 'r') as f:
    for line in f:
        login, old_pass = line.strip().split(':')
        new_pass = generate_new_password()

        data = {

            "login": login,
            "old_password": old_pass,
            "new_password": new_pass
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Content-Type": "application/json"
        }

        resp = requests.post("https://api.firstmail.ltd/v1/account/change-password", json=data, headers=headers)
        if resp.status_code == 200:
            print(f"[成功] {login} 密码已更改为：{new_pass}")
        else:
            print(f"[失败] {login} → {resp.text}")





























exit()
sql='''SELECT
  fmap.*,
  t1.id AS t1_id,
  t1.uid AS t1_uid,
  t1.cid AS t1_cid,
  t1.tid AS t1_tid,
  t1.username AS t1_username,
  t1.show_name AS t1_show_name,
  t1.url AS t1_url,
  t1.remark AS t1_remark,
  t1.description AS t1_description,
  t1.avatar AS t1_avatar,
  t1.followers AS t1_followers,
  t1.fans AS t1_fans,
  t1.status AS t1_status,
  t1.created AS t1_created,
  t1.updated AS t1_updated,

  t2.id AS t2_id,
  t2.uid AS t2_uid,
  t2.cid AS t2_cid,
  t2.tid AS t2_tid,
  t2.username AS t2_username,
  t2.show_name AS t2_show_name,
  t2.url AS t2_url,
  t2.remark AS t2_remark,
  t2.description AS t2_description,
  t2.avatar AS t2_avatar,
  t2.followers AS t2_followers,
  t2.fans AS t2_fans,
  t2.status AS t2_status,
  t2.created AS t2_created,
  t2.updated AS t2_updated

FROM (
  SELECT *
  FROM guzi_twitter_followings_map
  WHERE status = 1
  ORDER BY id DESC
  LIMIT 20 OFFSET 0
) AS fmap

INNER JOIN guzi_twitter AS t1 ON fmap.twitter_id = t1.tid
INNER JOIN guzi_twitter AS t2 ON fmap.following_id = t2.tid
'''
total_page =  dbMysql.query(sql)
#print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
#print(total_page)

exit()


# ✅ 时间格式化
def to_unix_timestamp(timestr):
    try:
        dt = datetime.strptime(timestr, "%a %b %d %H:%M:%S %z %Y")
        return int(dt.timestamp())
    except:
        return 0

def format_created_ts():
    return int(time.time())

# ✅ 获取作者 ID
def extract_user_id(tweet_obj):
    return tweet_obj.get('core', {}).get('user_results', {}).get('result', {}).get('rest_id')

# ✅ 提取媒体内容为 HTML（图片 + 视频）
def extract_media_html(legacy):
    html_parts = []
    media_list = legacy.get('extended_entities', {}).get('media', [])
    for media in media_list:
        mtype = media.get('type')
        if mtype == 'photo':
            url = media.get('media_url_https')
            if url:
                html_parts.append(f'<img src="{url}" style="max-width:100%; margin-top:5px;" />')
        elif mtype in ['video', 'animated_gif']:
            variants = media.get('video_info', {}).get('variants', [])
            mp4s = [v['url'] for v in variants if 'video/mp4' in v.get('content_type', '')]
            if mp4s:
                html_parts.append(f'''
                    <video controls style="max-width:100%; margin-top:5px;">
                      <source src="{mp4s[0]}" type="video/mp4">
                      Your browser does not support the video tag.
                    </video>
                ''')
    return "\n".join(html_parts)

user_id = "1762471547485184000"

id = insertUserToDB(user_id)

print(id)
exit()

twitter_id = 578266788

records = getFollowingsByUserID(twitter_id)
print(f"\n共获取 {len(records)} 个关注用户\n")

for f in records[:5]:  # 只打印前5个示例
        print(f)

insertUserDataToDB(records,twitter_id=twitter_id)
#print(json.dumps(data, indent=2, ensure_ascii=False))
exit()

id = '1925739084921594049'
raw_data = getTweetByID(id)
print(raw_data)
exit()

user_id = 1762471547485184000
usre_data = getDataByUserID(user_id)
id = insertUserToDB(usre_data)

print(id)

id = '1925026529739997425'
raw_data = getTweetByID(id)


print(json.dumps(raw_data, indent=2, ensure_ascii=False))
exit()





url = "https://twitter241.p.rapidapi.com/user-tweets"

querystring = {"user":"1272455925132079104","count":"100"}

headers = {
	"x-rapidapi-key": "a500f12012msh6da813a3681a40cp1578f4jsn3bc8772c883e",
	"x-rapidapi-host": "twitter241.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
data = response.json()

records = []

for instr in data['result']['timeline']['instructions']:
    if 'entries' not in instr:
        continue
    for entry in instr['entries']:
        try:
            tweet = entry['content']['itemContent']['tweet_results']['result']
            legacy = tweet.get('legacy', {})
            tweet_id = tweet.get('rest_id')
            user_id = extract_user_id(tweet)
            text = legacy.get('full_text', '')
            created_at_ts = to_unix_timestamp(legacy.get('created_at', ''))
            likes = legacy.get('favorite_count', 0)
            retweets = legacy.get('retweet_count', 0)
            replies = legacy.get('reply_count', 0)
            views = legacy.get('views', 0)
            now_ts = format_created_ts()
            media_html = extract_media_html(legacy)
            content = text + "\n" + media_html if media_html else text

            is_type = 1
            original_id = None
            original_user_id = None

            # ✅ 转发处理
            if 'retweeted_status_result' in legacy:
                is_type = 3
                retweeted = legacy['retweeted_status_result']['result']
                original_id = retweeted.get('rest_id')
                original_user_id = extract_user_id(retweeted)
                r_legacy = retweeted.get('legacy', {})
                r_text = r_legacy.get('full_text', '')
                r_media_html = extract_media_html(r_legacy)
                r_content = r_text + "\n" + r_media_html if r_media_html else r_text
                r_created_at_ts = to_unix_timestamp(r_legacy.get('created_at', ''))

                records.append({
                    "tweet_id": original_id,
                    "user_id": original_user_id,
                    "is_type": 1,
                    "likes": r_legacy.get('favorite_count', 0),
                    "retweets": r_legacy.get('retweet_count', 0),
                    "replies": r_legacy.get('reply_count', 0),
                    "views": r_legacy.get('views', 0),
                    "content": r_content,
                    "original_tweet_id": None,
                    "original_tweet_user_id": None,
                    "created_at": r_created_at_ts,
                    "status": 1,
                    "created": now_ts,
                    "updated": now_ts
                })

            # ✅ 引用处理
            elif legacy.get('is_quote_status') and 'quoted_status_result' in tweet:
                is_type = 3
                quoted = tweet['quoted_status_result']['result']
                original_id = quoted.get('rest_id')
                original_user_id = extract_user_id(quoted)
                q_legacy = quoted.get('legacy', {})
                q_text = q_legacy.get('full_text', '')
                q_media_html = extract_media_html(q_legacy)
                q_content = q_text + "\n" + q_media_html if q_media_html else q_text
                q_created_at_ts = to_unix_timestamp(q_legacy.get('created_at', ''))
                ### 如果有推文


                records.append({
                    "tweet_id": original_id,
                    "user_id": original_user_id,
                    "is_type": 1,
                    "likes": q_legacy.get('favorite_count', 0),
                    "retweets": q_legacy.get('retweet_count', 0),
                    "replies": q_legacy.get('reply_count', 0),
                    "views": q_legacy.get('views', 0),
                    "content": q_content,
                    "original_tweet_id": None,
                    "original_tweet_user_id": None,
                    "created_at": q_created_at_ts,
                    "status": 1,
                    "created": now_ts,
                    "updated": now_ts
                })

            # ✅ 当前推文入库
            records.append({
                "tweet_id": tweet_id,
                "user_id": user_id,
                "is_type": is_type,
                "likes": likes,
                "retweets": retweets,
                "replies": replies,
                "content": content,
                "original_tweet_id": original_id,
                "original_tweet_user_id": original_user_id,
                "created_at": created_at_ts,
                "status": 1,
                "created": now_ts,
                "updated": now_ts
            })

        except Exception as e:
            print("❌ 跳过异常:", e)
# ✅ 此处可以执行数据库批量插入
# 批量插入 records 到 guzi_tweets 表
# print(records) 或 return records
print("共提取推文条数：", len(records))
#print(records)
# 所有推文构造完成后
records.sort(key=lambda r: r['created_at'])  # 旧推文在前
for dbdata in records:
    tweet_id = dbdata['tweet_id']
    print(tweet_id)
    data_one = dbMysql.table('guzi_tweets').where(f"tweet_id='{tweet_id}'").find()
    today_time = int(time.time())
    if data_one:
        result_id = data_one['id']
        dbdata['updated'] = today_time
        dbdata.pop("created", None)
        result_id = dbMysql.table('guzi_tweets').where(f"id ='{result_id}'").save(dbdata)
        # print(dbMysql.getLastSql())
    else:
        dbdata['created'] = today_time
        dbdata['status'] = 1
        tweets_id = dbMysql.table('guzi_tweets').add(dbdata)

    print(dbMysql.getLastSql())
#print(json.dumps(records, indent=2, ensure_ascii=False))