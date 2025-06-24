from util.db import *

## 通过把用户数据入库
def insertUserToDB(records):
    if not records:
        print("⚠️ insertUserToDB：records 是 None，跳过插入。")
        return
    if not records.get('rest_id'):
        print("⚠️ insertUserToDB：缺少 rest_id 字段，跳过插入。")
        return
    tid = records['rest_id']
    uid = 1
    cid = 1
    ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
    data_one = dbMysql.table('guzi_twitter').where( f"tid='{tid}'").find()
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

## 把推文数据相关推特数据和推文循环插入数据库
def insertUserDataToDB(records,twitter_id = None):
        following_id = None

        for user in records:
            username = user.get('username', '')

            if username:
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
                print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
                ## 如果俩个id都存在，则插入关联表中
                if not map_one or len(map_one) == 0:
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
            if not dbdata.get('tweet_id'):
                print("警告：tweet_id为空，跳过此条数据", dbdata)
                continue
            tweet_id = dbdata['tweet_id']
            ## 推特用户如果没有，操作直接入数据库
            twitter_id = dbdata['twitter_id']
            #record_id = insertUserToDB(user_id)

            original_tweet_user_id = dbdata['original_tweet_user_id']
            original_tweet_id = dbdata['original_tweet_id']
            original_userdata = dbdata['original_userdata']
            ## 推特原作者也需要入库
            if original_tweet_user_id and original_tweet_user_id != twitter_id:
                insertUserToDB(original_userdata)


            data_one = dbMysql.table('guzi_tweets').where(f"tweet_id='{tweet_id}'").find()
            #print(dbMysql.getLastSql())
            today_time = int(time.time())
            dbdata.pop('original_userdata', None) ### 去掉不在数据库里的值

            # if data_one:
            #     result_id = data_one['id']
            #     dbdata['updated'] = today_time
            #     dbdata.pop("created", None)
            #     result_id = dbMysql.table('guzi_tweets').where(f"id ='{result_id}'").save(dbdata)
            #     #print(dbMysql.getLastSql())

            if not data_one:
                dbdata['created'] = today_time
                dbdata['status'] = 1
                tweets_id = dbMysql.table('guzi_tweets').add(dbdata)
                #print(dbMysql.getLastSql())

