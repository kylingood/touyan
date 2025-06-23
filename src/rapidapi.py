# -*- coding: utf-8 -*-
import requests
from util.db import *
from src.config import X_RAPIDAPI_KEY,X_RAPIDAPI_HOST
# 定义常量
HEADERS = {
    "x-rapidapi-key": X_RAPIDAPI_KEY,
    "x-rapidapi-host": X_RAPIDAPI_HOST
}

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



## 通过推特用户名取到账号详细数据
def getFollowingsByUserID(user_id,sum_user=None,sleep_time=1, max_repeat_cursor=3, max_repeat_user=5):
    url = "https://twitter241.p.rapidapi.com/followings"
    all_users = []
    seen_ids = set()
    cursor = None
    last_cursor = None
    repeat_cursor_count = 0
    repeat_user_count = 0
    last_user_count = 0

    while True:
        querystring = {"user": user_id}
        if cursor:
            querystring["cursor"] = cursor

        try:
            response = requests.get(url, headers=HEADERS, params=querystring, timeout=10)
            data = response.json()

            instructions = data.get("result", {}).get("timeline", {}).get("instructions", [])
            all_entries = []
            for inst in instructions:
                if inst.get("type") == "TimelineAddEntries":
                    all_entries.extend(inst.get("entries", []))

            has_next = False
            for entry in all_entries:
                entry_id = entry.get("entryId", "")
                if entry_id.startswith("user-"):
                    for _ in range(3):
                        try:
                            user_data = entry["content"]["itemContent"]["user_results"]["result"]

                            legacy = user_data.get("legacy", {})
                            user = {
                                "rest_id": user_data["rest_id"],
                                "username": legacy.get("screen_name", ""),  # Twitter 用户名
                                "show_name": legacy.get("name", ""),  # 显示名称
                                "url": f"https://x.com/{legacy.get('screen_name', '')}" if legacy.get(
                                    "screen_name") else None,  # 推特主页链接
                                "remark": None,  # 备注，接口没，暂时空着
                                "description": legacy.get("description", ""),  # 个人简介
                                "avatar": legacy.get("profile_image_url_https", "0"),  # 用户头像链接
                                "followers": str(legacy.get("friends_count", 0)),  # 粉丝数
                                "fans": str(legacy.get("followers_count", 0)),  # 关注数（你叫fans？一般是friends_count）
                            }

                            if user["rest_id"] not in seen_ids:
                                all_users.append(user)
                                seen_ids.add(user["rest_id"])
                            break
                        except Exception as e:
                            print(f"解析失败，重试中：{e} - entryId: {entry_id}")
                            time.sleep(0.5)
                elif entry_id.startswith("cursor-bottom"):
                    cursor_value = entry["content"].get("value", "")
                    if not cursor_value:
                        print("未找到有效 cursor，终止")
                        return all_users

                    if cursor_value == last_cursor:
                        repeat_cursor_count += 1
                        print(f"cursor 未变，第 {repeat_cursor_count} 次：{cursor_value}")
                        if repeat_cursor_count >= max_repeat_cursor:
                            print("cursor 重复超过限制，终止抓取")
                            return all_users
                    else:
                        repeat_cursor_count = 0

                    last_cursor = cursor_value
                    cursor = cursor_value
                    has_next = True

            # 监测用户数是否有变化
            current_user_count = len(all_users)
            if sum_user:
                if current_user_count >= sum_user:
                    print(f"抓取的用户总数量超过 {sum_user} 限制，终止抓取")
                    break
            if current_user_count == last_user_count:
                repeat_user_count += 1
                print(f"用户数未增加，连续第 {repeat_user_count} 次，当前数量：{current_user_count}")
                if repeat_user_count >= max_repeat_user:
                    print("用户数量连续未变超过限制，终止抓取")
                    break
            else:
                repeat_user_count = 0

            last_user_count = current_user_count

            print(f"[{user_id}] 已获取 {current_user_count} 个用户")

            if not has_next:
                print("没有更多 followings 了")
                break

            time.sleep(sleep_time)

        except Exception as e:
            print(f"请求失败或接口异常：{e}")
            break

    # 按倒序排列（即最后抓取的用户排在最前）
    all_users.reverse()
    return all_users

###结构化推特账号数据
def extract_twitter_info(data, username):
    # 先取到深层的result节点
    user = data.get('result', {}).get('data', {}).get('user', {}).get('result', {})
    legacy = user.get('legacy', {})
    avatar = user.get('avatar', {})
    core = user.get('core', {})

    followers = legacy.get('followers_count', 0)
    fans = legacy.get('friends_count', 0)
    description = legacy.get('description', '')
    avatar_url = legacy.get('profile_image_url_https') or avatar.get('image_url', '')
    rest_id = user.get('rest_id') or user.get('id', '')
    screen_name = legacy.get('screen_name') or core.get('screen_name', '')
    show_name = legacy.get('name') or core.get('name', '')
    created_at = legacy.get('created_at') or core.get('created_at', '')
    url = f"https://x.com/{username}"
    return {
        "followers": followers,
        "fans": fans,
        "description": description,
        "avatar": avatar_url,
        "username": username,
        "rest_id": rest_id,
        "screen_name": screen_name,
        "url": url,
        "show_name": show_name,
        "remark": show_name,
        "created_at": created_at
    }



## 通过推特用户名取到账号详细数据
def getDataByUsername(username):
    url = "https://twitter241.p.rapidapi.com/user"
    querystring = {"username": username}

    retries = 3
    sleep_time = 1

    data = None
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, params=querystring)
            response.raise_for_status()  # 如果响应状态码不是200，会抛异常
            data = response.json()  # 解析 JSON
            user_data = extract_twitter_info(data, username)
            print(user_data)
            # 检查是否有预期结构
            if (
                    data and
                    'result' in data and
                    'data' in data['result'] and
                    'user' in data['result']['data'] and
                    'result' in data['result']['data']['user']
            ):
                return user_data
            else:
                print(f"⚠️ 第 {attempt + 1} 次请求数据结构异常: {data}")
                data = None
        except Exception as e:
            print(f"⚠️ 第 {attempt + 1} 次请求失败：{e}")
            if attempt < retries - 1:
                time.sleep(sleep_time)
            else:
                print("❌ 超过最大重试次数，放弃请求")

    return None


## 通过推特账号id号取到账号详细数据
def getDataByUserID(user_id):
    url = "https://twitter241.p.rapidapi.com/get-users"
    querystring = {"users": str(user_id)}

    retries = 3
    sleep_time = 1

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, params=querystring)
            data = response.json()  # 解析 JSON
            break  # 成功就退出循环
        except Exception as e:
            print(f"⚠️ 第 {attempt + 1} 次请求失败：{e}")
            if attempt < retries - 1:
                time.sleep(sleep_time)
            else:
                data = None
                print("❌ 超过最大重试次数，放弃请求")

    #print(json.dumps(data, indent=2, ensure_ascii=False))
    # 打印一下实际收到的内容，确认是否真的有 "result"
    #print("接口实际返回：", json.dumps(data, indent=2, ensure_ascii=False))
    user_data = data['result']['data']['users'][0]['result']


    tid = user_data.get('rest_id', '')
    username = user_data['legacy'].get('screen_name', '')
    show_name = user_data['legacy'].get('name', '')
    description = user_data['legacy'].get('description', '')
    avatar = user_data['legacy'].get('profile_image_url_https', '')
    followers = user_data['legacy'].get('followers_count', 0)
    fans = user_data['legacy'].get('friends_count', 0)
    url = f"https://x.com/{username}"
    created_at = user_data['legacy'].get('created_at', '')

    dbdata = {
        'rest_id': tid,
        'username': username,
        'show_name': show_name,
        'url': url,
        'description': description,
        'remark': show_name,
        'avatar': avatar,
        'followers': followers,
        'fans': fans,
        'created_at': created_at
    }

    return dbdata



## 通过推文id号取到推文详细数据
def getTweetByID(tweet_id):
    url = "https://twitter241.p.rapidapi.com/tweet"

    querystring = {"pid": tweet_id}

    retries = 1
    sleep_time = 1

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, params=querystring)
            data = response.json()  # 解析 JSON
            break  # 成功就退出循环
        except Exception as e:
            print(f"⚠️ 第 {attempt + 1} 次请求失败：{e}")
            if attempt < retries - 1:
                time.sleep(sleep_time)
            else:
                data = None
                print("❌ 超过最大重试次数，放弃请求")

    if not data or 'tweet' not in data or 'user' not in data:
        print(f"❌ 无法获取 tweet_id={tweet_id} 的有效数据")
        return None

    # === 原始数据 ===
    tweet = data['tweet']
    #print(json.dumps(tweet, indent=2, ensure_ascii=False))
    user = data['user']
    legacy = user.get('legacy', {})

    # === 提取内容 ===
    tweet_id = tweet['id_str']
    user_id = tweet['user_id_str']
    created_at = to_unix_timestamp(tweet['created_at'])

    likes = tweet.get('favorite_count', 0)
    retweets = tweet.get('retweet_count', 0)
    replies = tweet.get('reply_count', 0)
    text = tweet.get('full_text', '')
    # is_type = 1  # 默认原创
    # Tweet 类型识别
    is_type = 1
    if tweet.get('retweeted_status_id_str'):
        is_type = 2
    elif tweet.get('is_quote_status'):
        is_type = 3

    # === 媒体补充（你可按需完善） ===
    media_html = extract_media_html(tweet)
    content = text + "\n" + media_html if media_html else text

    # === 是否引用其他推文？===
    original_tweet_id = tweet['quoted_status_id_str'] if tweet.get('is_quote_status') else None
    original_tweet_user_id = None  # 此接口无法直接取出引用的 user_id，可通过补接口再查
    now_ts = format_created_ts()
    # === 组装 record ===
    record = {
        "tweet_id": tweet_id,
        "twitter_id": user_id,
        "is_type": is_type,
        "likes": likes,
        "retweets": retweets,
        "replies": replies,
        "content": content,
        "original_tweet_id": original_tweet_id,
        "original_tweet_user_id": original_tweet_user_id,
        "created_at": created_at,
        "status": 1,
        "created": now_ts,
        "updated": now_ts
    }

    return record


## 通过推特账号id取到此账号下的推文数据
def getTweetByUserID(user_id):

    url = "https://twitter241.p.rapidapi.com/user-tweets"
    querystring = {"user": user_id, "count": "20"}

    retries = 3
    sleep_time = 1

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, params=querystring)
            data = response.json()  # 解析 JSON
            break  # 成功就退出循环
        except Exception as e:
            print(f"⚠️ 第 {attempt + 1} 次请求失败：{e}")
            if attempt < retries - 1:
                time.sleep(sleep_time)
            else:
                data = None
                print("❌ 超过最大重试次数，放弃请求")

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
                now_ts = format_created_ts()
                media_html = extract_media_html(legacy)
                content = text + "\n" + media_html if media_html else text

                is_type = 1
                original_tweet_id = None
                original_tweet_user_id = None

                # ✅ 转发处理
                if 'retweeted_status_result' in legacy:
                    is_type = 3
                    retweeted = legacy['retweeted_status_result']['result']
                    original_tweet_id = retweeted.get('rest_id')
                    original_tweet_user_id = extract_user_id(retweeted)
                    r_legacy = retweeted.get('legacy', {})
                    r_text = r_legacy.get('full_text', '')
                    r_media_html = extract_media_html(r_legacy)
                    r_content = r_text + "\n" + r_media_html if r_media_html else r_text
                    r_created_at_ts = to_unix_timestamp(r_legacy.get('created_at', ''))

                    records.append({
                        "tweet_id": original_tweet_id,
                        "twitter_id": original_tweet_user_id,
                        "is_type": 1,
                        "likes": r_legacy.get('favorite_count', 0),
                        "retweets": r_legacy.get('retweet_count', 0),
                        "replies": r_legacy.get('reply_count', 0),
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
                    original_tweet_id = quoted.get('rest_id')
                    original_tweet_user_id = extract_user_id(quoted)
                    q_legacy = quoted.get('legacy', {})
                    q_text = q_legacy.get('full_text', '')
                    q_media_html = extract_media_html(q_legacy)
                    q_content = q_text + "\n" + q_media_html if q_media_html else q_text
                    q_created_at_ts = to_unix_timestamp(q_legacy.get('created_at', ''))

                    records.append({
                        "tweet_id": original_tweet_id,
                        "twitter_id": original_tweet_user_id,
                        "is_type": 1,
                        "likes": q_legacy.get('favorite_count', 0),
                        "retweets": q_legacy.get('retweet_count', 0),
                        "replies": q_legacy.get('reply_count', 0),
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
                    "twitter_id": user_id,
                    "is_type": is_type,
                    "likes": likes,
                    "retweets": retweets,
                    "replies": replies,
                    "content": content,
                    "original_tweet_id": original_tweet_id,
                    "original_tweet_user_id": original_tweet_user_id,
                    "created_at": created_at_ts,
                    "status": 1,
                    "created": now_ts,
                    "updated": now_ts
                })

                # ## 推特原作者也需要入库
                # if original_tweet_user_id and original_tweet_user_id!=user_id:
                #     record_id = insertUserToDB(original_tweet_user_id)
                #     print(record_id)
                #
                #
                if original_tweet_id:
                    print(f"original_tweet_id:{original_tweet_id} tweet_id:{tweet_id}")
                    original_record = getTweetByID(original_tweet_id)

                    if original_record:
                        records.append(original_record)

            except Exception as e:
                print("❌ 跳过异常:", e)

    records.sort(key=lambda r: r['created_at'])  # 旧推文在前
    ### 插入数据库
    insertTeeetToDB(records)
    return records


## 通过把用户数据入库
def insertUserToDB(user_id):
    ## 通过接口取推特账号数据
    records = getDataByUserID(user_id)
    tid = records['rest_id']
    uid = 1
    cid = 1
    ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
    data_one = dbMysql.table('guzi_twitter').where(
        f"tid='{tid}'").find()
    today_time = int(time.time())

    dbdata = {
        'uid': uid,
        'cid': cid,
        'tid': records.get('rest_id', ''),
        'username': records.get('username', ''),
        'show_name': records.get('show_name', ''),
        'url': records.get('url', ''),
        'remark': records.get('remark', ''),
        'description': records.get('description', ''),
        'avatar': records.get('avatar', '0'),
        'followers': records.get('followers', '0'),
        'fans': records.get('fans', '0'),
        'status': 1,
        'created': int(time.time()),
    }

    user_id = None
    if not data_one:
        dbdata['status'] = 1
        dbdata['created'] = today_time
        user_id = dbMysql.table('guzi_twitter').add(dbdata)
        time.sleep(0.5)
        print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

    return user_id


## 把推文数据相关推特数据和推文循环插入数据库
def insertUserDataToDB(records,twitter_id=None):
        following_id = None
        for user in records:

            ## 推特用户如果没有，操作直接入数据库
            following_id = user.get('rest_id', '')
            uid = user.get('uid', 1)
            cid = user.get('cid', 1)
            ## 先查看此推特有没有入库，没有就插入
            data_one = dbMysql.table('guzi_twitter').where(f"tid='{following_id}'").find()
            today_time = int(time.time())
            dbdata = {
                'uid': uid,
                'cid': cid,
                'tid': following_id,
                'username': user.get('username', ''),
                'show_name': user.get('show_name', ''),
                'url': user.get('url', ''),
                'remark': user.get('remark', ''),
                'description': user.get('description', ''),
                'avatar': user.get('avatar', '0'),
                'followers': user.get('followers', '0'),
                'fans': user.get('fans', '0'),
                'status': 1,
                'created': int(time.time()),
            }
            # print(data_one)

            if not data_one:
                id = dbMysql.table('guzi_twitter').add(dbdata)
                print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句


            ## 先查看此推特和用户数据有没有入库，没有就插入
            map_one = dbMysql.table('guzi_twitter_followings_map').where(f"twitter_id='{twitter_id}' AND  following_id = '{following_id}'").find()
            ## 如果俩个id都存在，则插入关联表中
            if not map_one:
                insertTwitterFollowingsToDB(twitter_id, following_id)


        return following_id

#guzi_twitter_followings_map
def insertTwitterFollowingsToDB(twitter_id,following_id):

    data_one = dbMysql.table('guzi_twitter_followings_map').where(f"twitter_id='{twitter_id}' and following_id='{following_id}'  ").find()
    today_time = int(time.time())
    if not data_one:
        dbdata = {}
        dbdata['twitter_id'] = twitter_id
        dbdata['following_id'] = following_id
        dbdata['created_at'] = today_time
        dbdata['status'] = 1
        tweets_id = dbMysql.table('guzi_twitter_followings_map').add(dbdata)
        print(dbMysql.getLastSql())



## 把推文数据相关推特数据和推文循环插入数据库
def insertTeeetToDB(records):

        for dbdata in records:
            tweet_id = dbdata['tweet_id']
            ## 推特用户如果没有，操作直接入数据库
            twitter_id = dbdata['twitter_id']
            #record_id = insertUserToDB(user_id)

            original_tweet_user_id = dbdata['original_tweet_user_id']
            original_tweet_id = dbdata['original_tweet_id']

            ## 推特原作者也需要入库
            if original_tweet_user_id and original_tweet_user_id != twitter_id:
                insertUserToDB(original_tweet_user_id)


            data_one = dbMysql.table('guzi_tweets').where(f"tweet_id='{tweet_id}'").find()
            today_time = int(time.time())
            if data_one:
                result_id = data_one['id']
                dbdata['updated'] = today_time
                dbdata.pop("created", None)
                result_id = dbMysql.table('guzi_tweets').where(f"id ='{result_id}'").save(dbdata)
                #print(dbMysql.getLastSql())
            else:
                dbdata['created'] = today_time
                dbdata['status'] = 1
                tweets_id = dbMysql.table('guzi_tweets').add(dbdata)
                #print(dbMysql.getLastSql())

