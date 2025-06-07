# -*- coding: utf-8 -*-
from util.db import *
import aiohttp
import asyncio
import time
from src.config import X_RAPIDAPI_KEY,X_RAPIDAPI_HOST
# 定义常量
HEADERS = {
    "x-rapidapi-key": X_RAPIDAPI_KEY,
    "x-rapidapi-host": X_RAPIDAPI_HOST
}
print(HEADERS)


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



# 通过推特用户名获取账号详细数据（异步版本）
async def async_getDataByUsername(session, username):
    url = "https://twitter241.p.rapidapi.com/user"
    querystring = {"username": username}

    retries = 3
    sleep_time = 1

    for attempt in range(retries):
        try:
            async with session.get(url, headers=HEADERS, params=querystring) as resp:
                resp.raise_for_status()
                data = await resp.json()  # 解析 JSON
                user_data = data['result']['data']['user']['result']

                tid = user_data.get('rest_id', '')
                username = user_data['legacy'].get('screen_name', '')
                show_name = user_data['legacy'].get('name', '')
                description = user_data['legacy'].get('description', '')
                avatar = user_data['legacy'].get('profile_image_url_https', '')
                followers = user_data['legacy'].get('friends_count', 0)
                fans = user_data['legacy'].get('followers_count', 0)
                url = f"https://x.com/{username}"
                created_at = user_data['legacy'].get('created_at', '')

                user_data = {
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

                return user_data


        except Exception as e:
            print(f"⚠️ 第 {attempt + 1} 次请求失败：{e}")
            if attempt < retries - 1:
                await asyncio.sleep(sleep_time)  # 异步睡眠
            else:
                print("❌ 超过最大重试次数，放弃请求")
                return None


## 通过接口取推特账号数据
async def async_getDataByUserID(session, user_id):
    url = "https://twitter241.p.rapidapi.com/get-users"
    params = {"users": str(user_id)}

    retries = 3
    sleep_time = 1

    for attempt in range(retries):
        try:
            async with session.get(url, headers=HEADERS, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
                break
        except Exception as e:
            print(f"⚠️ 第 {attempt + 1} 次请求失败：{e}")
            if attempt < retries - 1:
                await asyncio.sleep(sleep_time)
            else:
                print("❌ 超过最大重试次数，放弃请求")
                return None

    try:

        user_data = data['result']['data']['users'][0]['result']

        tid = user_data.get('rest_id', '')
        username = user_data['legacy'].get('screen_name', '')
        show_name = user_data['legacy'].get('name', '')
        description = user_data['legacy'].get('description', '')
        avatar = user_data['legacy'].get('profile_image_url_https', '')
        followers = user_data['legacy'].get('friends_count', 0)
        fans = user_data['legacy'].get('followers_count', 0)
        url = f"https://x.com/{username}"
        created_at = user_data['legacy'].get('created_at', '')

        user_data = {
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

        return user_data

    except Exception as e:
        print("❌ 数据解析失败：", e)
        return None


##通过推特账号取到本推特号指定数量的粉丝数据
async def async_getUserFollowingIds(session, username,count=50):
    url = "https://twitter241.p.rapidapi.com/following-ids"
    params = {"username": username, "count": count}

    retries = 3
    for attempt in range(retries):
        try:
            async with session.get(url, headers=HEADERS, params=params) as resp:
                resp.raise_for_status()
                user_data = await resp.json()
                return user_data['ids']
        except Exception as e:
            print(f"⚠️ 第 {attempt+1} 次请求失败：{e}")
            if attempt == retries - 1:
                print("❌ 超过最大重试次数")
            await asyncio.sleep(1)

    return None


##通过推特id取到本推特号下面的推文数据
async def fetch_user_tweets(session, user_id):
    url = "https://twitter241.p.rapidapi.com/user-tweets"
    params = {"user": user_id, "count": "20"}

    retries = 3
    for attempt in range(retries):
        try:
            async with session.get(url, headers=HEADERS, params=params) as resp:
                resp.raise_for_status()
                return await resp.json()
        except Exception as e:
            print(f"⚠️ 第 {attempt+1} 次请求失败：{e}")
            if attempt == retries - 1:
                print("❌ 超过最大重试次数")
            await asyncio.sleep(1)

    return None


async def async_getTweetByUserID(session, user_id):
    data = await fetch_user_tweets(session, user_id)
    if not data:
        return []

    records = []

    for instr in data.get('result', {}).get('timeline', {}).get('instructions', []):
        for entry in instr.get('entries', []):
            try:
                tweet = entry['content']['itemContent']['tweet_results']['result']
                legacy = tweet.get('legacy', {})
                tweet_id = tweet.get('rest_id')
                twitter_id = extract_user_id(tweet)
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
                original_userdata  = None
                # 转推
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
                        "original_userdata": None,
                        "created_at": r_created_at_ts,
                        "status": 1,
                        "created": now_ts,
                        "updated": now_ts
                    })

                # 引用推文
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
                        "original_userdata": None,
                        "created_at": q_created_at_ts,
                        "status": 1,
                        "created": now_ts,
                        "updated": now_ts
                    })

                ## 推特原作者也需要入库,这里先一并取了数据
                if original_tweet_user_id and original_tweet_user_id != twitter_id:
                    original_userdata = await async_getDataByUserID(session, original_tweet_user_id)

                # 当前推文
                records.append({
                    "tweet_id": tweet_id,
                    "twitter_id": twitter_id,
                    "is_type": is_type,
                    "likes": likes,
                    "retweets": retweets,
                    "replies": replies,
                    "content": content,
                    "original_tweet_id": original_tweet_id,
                    "original_tweet_user_id": original_tweet_user_id,
                    "original_userdata": original_userdata,
                    "created_at": created_at_ts,
                    "status": 1,
                    "created": now_ts,
                    "updated": now_ts
                })



                # 原推引用
                if original_tweet_id:
                    print(f"original_tweet_id:{original_tweet_id} tweet_id:{tweet_id}")
                    origin_data = await async_getTweetByID(session, original_tweet_id)
                    if origin_data:
                        records.append(origin_data)

            except Exception as e:
                print("❌ 跳过异常:", e)

    records.sort(key=lambda r: r['created_at'])

    return records


async def async_getTweetByID(session, tweet_id):
    url = "https://twitter241.p.rapidapi.com/tweet"
    params = {"pid": tweet_id}
    retries = 1
    sleep_time = 1

    data = None
    for attempt in range(retries):
        try:
            async with session.get(url, headers=HEADERS, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
                break
        except Exception as e:
            print(f"⚠️ 第 {attempt + 1} 次请求失败（tweet_id={tweet_id}）：{e}")
            if attempt < retries - 1:
                await asyncio.sleep(sleep_time)
            else:
                print("❌ 超过最大重试次数，放弃请求")

    if not data or 'tweet' not in data or 'user' not in data:
        print(f"❌ 无法获取 tweet_id={tweet_id} 的有效数据")
        return None

    # 原始数据提取
    tweet = data['tweet']
    user = data['user']
    legacy = user.get('legacy', {})

    tweet_id = tweet['id_str']
    user_id = tweet['user_id_str']
    created_at = to_unix_timestamp(tweet['created_at'])

    likes = tweet.get('favorite_count', 0)
    retweets = tweet.get('retweet_count', 0)
    replies = tweet.get('reply_count', 0)
    text = tweet.get('full_text', '')

    # 类型判断
    is_type = 1
    if tweet.get('retweeted_status_id_str'):
        is_type = 2
    elif tweet.get('is_quote_status'):
        is_type = 3

    media_html = extract_media_html(tweet)
    content = text + "\n" + media_html if media_html else text

    original_tweet_id = tweet['quoted_status_id_str'] if tweet.get('is_quote_status') else None
    original_tweet_user_id = None  # 此接口取不到

    now_ts = format_created_ts()

    return {
        "tweet_id": tweet_id,
        "twitter_id": user_id,
        "is_type": is_type,
        "likes": likes,
        "retweets": retweets,
        "replies": replies,
        "content": content,
        "original_tweet_id": original_tweet_id,
        "original_tweet_user_id": original_tweet_user_id,
        "original_userdata": None,
        "created_at": created_at,
        "status": 1,
        "created": now_ts,
        "updated": now_ts
    }



async def async_getFollowingsByUserID(
            session,
            user_id,
            sum_user=None,
            sleep_time=1,
            max_repeat_cursor=3,
            max_repeat_user=3
        ):
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
            async with session.get(url, headers=HEADERS, params=querystring, timeout=10) as resp:
                resp.raise_for_status()
                data = await resp.json()

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
                                "username": legacy.get("screen_name", ""),
                                "show_name": legacy.get("name", ""),
                                "url": f"https://x.com/{legacy.get('screen_name', '')}" if legacy.get("screen_name") else None,
                                "remark": None,
                                "description": legacy.get("description", ""),
                                "avatar": legacy.get("profile_image_url_https", "0"),
                                "followers": str(legacy.get("friends_count", 0)),
                                "fans": str(legacy.get("followers_count", 0)),
                            }

                            if user["rest_id"] not in seen_ids:
                                all_users.append(user)
                                seen_ids.add(user["rest_id"])
                            break
                        except Exception as e:
                            print(f"解析失败，重试中：{e} - entryId: {entry_id}")
                            await asyncio.sleep(0.5)

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

            # 检查用户数量变化
            current_user_count = len(all_users)
            if sum_user and current_user_count >= sum_user:
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

            await asyncio.sleep(sleep_time)

        except Exception as e:
            print(f"请求失败或接口异常：{e}")
            break

    all_users.reverse()
    return all_users
