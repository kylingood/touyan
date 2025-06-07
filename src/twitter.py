# -*- coding: utf-8 -*-
from quart import Quart, render_template, request, jsonify,g, Blueprint
from eth_account.messages import encode_defunct
from eth_account import Account
from functools import wraps
import time
import jwt
import datetime
from util.db import *
from src.config import SYSTEM_MAX_TWITTER,DEFAULT_UID
from src.auth import check_user_login_do,require_user_async
from src.rapidapi import *




# 创建一个 Blueprint 用于 Web3 登录功能
twitter = Blueprint('twitter', __name__)


@twitter.route('/twitter/index', methods=['GET'])
async def index():

    return await render_template("/twitter/index.html")

###批量提交推特
@twitter.route('/twitter/batch', methods=['GET'])
async def batch():

    return await render_template("/twitter/batch.html")

## 推特信息流列表
@twitter.route('/twitter/message', methods=['GET'])
@twitter.route('/twitter/message/gid/<int:gid>', methods=['GET'])
async def message(gid=0):

    return await render_template("/twitter/message.html", gid=gid)


## 推特信息总结列表
@twitter.route('/twitter/summary', methods=['GET'])
@twitter.route('/twitter/summary/gid/<int:gid>', methods=['GET'])
async def summary(gid=0):

    return await render_template("/twitter/summary.html", gid=gid)



@twitter.route('/twitter/listuser', methods=['GET', 'POST'])
@require_user_async
async def listuser():
    uid = g.uid
    sql = f'''SELECT t.tid, t.show_name
        FROM guzi_member_twitter_map AS m
        INNER JOIN guzi_twitter AS t ON m.twitter_id = t.tid
        WHERE m.status = 1 AND m.uid='{uid}' ORDER BY m.sorts DESC,m.id DESC  Limit 50
        '''
    data = dbMysql.query(sql)
    print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    return jsonify({'status': 1, 'data': data})



@twitter.route("/twitter/page_followings", methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
async def page_followings():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        user_id = request.args.get('user_id', default=0, type=int)
        guild_id = request.args.get('guild_id', default=0, type=int)


        # 初始化
        where_clauses = ["status=1"]  # 永远有的条件
        order = "id DESC"
        # 可选条件
        if user_id:
            where_clauses.append(f"twitter_id='{user_id}'")



        #where_clauses.append(f"t2.uid='{uid}'")

        # ## 先取到所有关注频道信息
        channel_list = dbMysql.table('guzi_member_twitter_map').where(f"uid='{uid}' AND status='1' ").select()
        twitter_data = {}

        if channel_list:
            channel_ids = []  # ✅ 正确：初始化为空列表
            for row in channel_list:
                twitter_data[row['twitter_id']] = row
                channel_ids.append(f"'{row['twitter_id']}'")  # 正确使用 append

            channel_in_sql = f"twitter_id IN ({', '.join(channel_ids)})"
            where_clauses.append(channel_in_sql)
        else:
            layui_result = {
                "code": 0,
                "count": 0,
                "data": []
            }
            return jsonify(layui_result)

        where = ' AND '.join(where_clauses)


        # 然后再计算偏移量
        offset = (page - 1) * limit
        sql = f'''SELECT
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
          WHERE {where}
          ORDER BY {order}
          LIMIT  {limit} OFFSET {offset}
        ) AS fmap

        INNER JOIN guzi_twitter AS t1 ON fmap.twitter_id = t1.tid
        INNER JOIN guzi_twitter AS t2 ON fmap.following_id = t2.tid
        '''
        data_list = dbMysql.query(sql)
        print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句


        total_page =  dbMysql.table('guzi_twitter_followings_map').where(where).count()
        print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        #total_page = 10

        if total_page > 0:
            layui_result = {
                "code": 0,
                "count": total_page,
                "data": data_list
            }
        else:
            layui_result = {
                "code": 0,
                "count": 0,
                "data": []
            }
        return jsonify(layui_result)



@twitter.route("/twitter/page_messages", methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
async def page_messages():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        user_id = request.args.get('user_id', default=0, type=int)
        guild_id = request.args.get('guild_id', default=0, type=int)


        # 初始化
        where_clauses = ["status=1"]  # 永远有的条件
        order = "tweet_id DESC,created DESC"
        # 可选条件
        if user_id:
            where_clauses.append(f"twitter_id='{user_id}'")

        # ## 先取到所有关注频道信息
        sql = f'''SELECT t.*
                FROM guzi_member_twitter_map AS m
                INNER JOIN guzi_twitter AS t ON m.twitter_id = t.tid
                WHERE m.status = 1 AND m.uid='{uid}';
                '''
        channel_list = dbMysql.query(sql)
        print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        twitter_data = {}

        if channel_list:
            channel_ids = []  # ✅ 正确：初始化为空列表
            for row in channel_list:
                twitter_data[row['tid']] = row
                channel_ids.append(f"'{row['tid']}'")  # 正确使用 append

            channel_in_sql = f"twitter_id IN ({', '.join(channel_ids)})"
            where_clauses.append(channel_in_sql)
        else:
            layui_result = {
                "code": 0,
                "count": 0,
                "data": []
            }
            return jsonify(layui_result)

        where = ' AND '.join(where_clauses)
        print(twitter_data)
        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1

        print(where)
        data_list = dbMysql.table('guzi_tweets').where(where).order(order).page(page, limit).select()
        print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        total_page =  dbMysql.table('guzi_tweets').where(where).count()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        #total_page = 10
        print(data_list)
        original_tweet_ids = set()
        original_user_ids = set()

        # 第一步：遍历收集所有需要查的 ID
        for item in data_list:
            if item.get("original_tweet_id"):
                original_tweet_ids.add(item["original_tweet_id"])
            if item.get("original_tweet_user_id"):
                original_user_ids.add(item["original_tweet_user_id"])

        # 假设你用 dbMysql 来查询：
        if original_tweet_ids:
            tweet_id_list_str = "', '".join(original_tweet_ids)
            tweet_where_sql = f"tweet_id IN ('{tweet_id_list_str}')"
            result_tweets = dbMysql.table('guzi_tweets').where(tweet_where_sql).select()
            data_original_tweets = {row['tweet_id']: row for row in result_tweets}
        else:
            data_original_tweets = {}

        if original_user_ids:
            user_id_list_str = "', '".join(original_user_ids)
            user_where_sql = f"tid IN ('{user_id_list_str}')"
            result_user = dbMysql.table('guzi_twitter').where(user_where_sql).select()
            data_original_user = {row['tid']: row for row in result_user}
        else:
            data_original_user = {}

        if total_page > 0:
            layui_result = {
                "code": 0,
                "count": total_page,
                "data": [
                    {
                        "num": i + start_index,
                        "id": item["id"],
                        "tweet_id": item["tweet_id"],
                        "user_id": item["twitter_id"],
                        "is_type": item["is_type"],
                        "likes":item["likes"],
                        "retweets": item["retweets"],
                        "replies": item["replies"],
                        "content": item["content"],
                        "original_tweet_id": item["original_tweet_id"],
                        "original_tweet_user_id": item["original_tweet_user_id"],
                        "data_original_tweets": data_original_tweets.get(item["original_tweet_id"], None),
                        "data_original_user": data_original_user.get(item["original_tweet_user_id"], None),
                        "created_at":datetime.fromtimestamp(int(item["created_at"])).strftime("%Y/%m/%d %H:%M"),
                        "avatar": twitter_data.get(str(item["twitter_id"]), {}).get("avatar") ,
                        "username": twitter_data.get(str(item["twitter_id"]), {}).get("username"),
                        "show_name": twitter_data.get(str(item["twitter_id"]), {}).get("show_name"),
                        "description": twitter_data.get(str(item["twitter_id"]), {}).get("description"),

                    } for i, item in enumerate(data_list)
                ]
            }

        else:
            layui_result = {
                "code": 0,
                "count": 0,
                "data": []
            }

        return jsonify(layui_result)

@twitter.route("/twitter/page", methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
async def page():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        cid = request.args.get('cid', default=0, type=int)
        keyword = request.args.get('keyword')

        where_sql_clauses = [f" m.uid='{uid}' AND m.status=1"]

        if cid:
            where_sql_clauses.append(f"m.category_id='{cid}'")


        if keyword:
            where_sql_clauses.append(
                f"(m.twitter_id LIKE '%{keyword}%' OR c.title LIKE '%{keyword}%' OR "
                f"t.username LIKE '%{keyword}%' OR t.show_name LIKE '%{keyword}%' OR "
                f"t.fans LIKE '%{keyword}%' OR t.url LIKE '%{keyword}%' OR "
                f"t.remark LIKE '%{keyword}%' OR t.followers LIKE '%{keyword}%' OR "
                f"t.description LIKE '%{keyword}%')"
            )


        where_sql = ' AND '.join(where_sql_clauses)

        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1

        order_sql = f"m.sorts DESC,m.id DESC"
        # 然后再计算偏移量
        offset = (page - 1) * limit
        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1
        sql = f'''SELECT
              m.id,
              m.uid,
              m.category_id,
              m.twitter_id,
              m.remark,
              m.sorts,
              t.id AS twitter_table_id,
              t.username,
              t.show_name,
              t.description,
              t.avatar,
              t.followers,
              t.fans,
              t.url,
              c.title AS category_title
            FROM guzi_member_twitter_map m
            LEFT JOIN guzi_twitter t ON m.twitter_id = t.tid
            LEFT JOIN guzi_category c ON m.category_id = c.id WHERE {where_sql} ORDER BY {order_sql}   LIMIT  {limit} OFFSET {offset}'''

        data_list = dbMysql.query(sql)
        # data_list = dbMysql.table('guzi_invite_codes').where(where).order(order).page(page, limit).select()
        print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        # total =  dbMysql.table('guzi_invite_codes').where(where).count()
        total_sql = f"SELECT COUNT(*) AS total FROM guzi_member_twitter_map m LEFT JOIN guzi_twitter t ON m.twitter_id = t.tid LEFT JOIN guzi_category c ON m.category_id = c.id WHERE  {where_sql}"
        print(total_sql)  # 打印由Model类拼接填充生成的SQL语句
        total_list = dbMysql.query(total_sql)
        total = total_list[0]['total'] if total_list and 'total' in total_list[0] else 0


        print(data_list)
        if total>0:
            layui_result = {
                "code": 0,
                "count": total,
                "data": [
                    {
                        "num": i + start_index,
                        "id": item["id"],
                        "uid": item["uid"],
                        "sorts": item["sorts"],
                        "cid": item["category_id"],
                        "tid": item["twitter_id"],
                        "cate_name": item["category_title"] or "未知分类",
                        "username": item["username"],
                        "url": item["url"],
                        "show_name": item["show_name"],
                        "avatar": item["avatar"],
                        "followers": item["followers"],
                        "fans": item["fans"],
                        "description": item["description"],
                        "remark": item["remark"] or "-",
                    } for i, item in enumerate(data_list)
                ]
            }
        else:
            layui_result = {
                "code": 0,
                "count": 0,
                "data": []
            }

        return  jsonify(layui_result)




@twitter.route('/twitter/edit', methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
@check_user_login_do
async def edit():
    uid = g.uid

    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        username = form.get('username')
        remark = form.get('remark')
        id = form.get('id')
        cid = form.get('cid')
        twitter_id = form.get('tid')
        show_name = form.get('show_name')
        url = form.get('url')
        avatar = form.get('avatar')
        sorts = form.get('sorts')
        followers = form.get('followers')
        fans = form.get('fans')
        description = form.get('description')

        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_member_twitter_map ').where(
            f"uid='{uid}' AND twitter_id='{twitter_id}'").find()
        print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        dbdata = {}
        today_time = int(time.time())


        if data_one:

            if twitter_id:

                ###插入关联表
                ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
                data_one = dbMysql.table('guzi_twitter_category_map').where( f"twitter_id='{twitter_id}' AND uid='{uid}' AND category_id='{cid}'").find()
                print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
                dbdata = {}
                print(data_one)
                if data_one:
                    id = data_one['id']
                    dbdata['twitter_id'] = twitter_id
                    dbdata['category_id'] = cid
                    dbdata['uid'] = uid
                    print('@@@@@@@@')
                    print(dbdata)
                    result_id = dbMysql.table('guzi_twitter_category_map').where(f"id = '{id}'").save(dbdata)
                    print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
                else:
                    # 获取当前日期
                    dbdata['twitter_id'] = twitter_id
                    dbdata['category_id'] = cid
                    dbdata['uid'] = uid
                    dbdata['status'] = 1
                    print(dbdata)
                    result_id = dbMysql.table('guzi_twitter_category_map').add(dbdata)
                    print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

                ###插入会员与推特账号关联表
                ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
                data_one = dbMysql.table('guzi_member_twitter_map ').where(
                    f"twitter_id='{twitter_id}' AND uid='{uid}' ").find()
                dbdata = {}
                today_time = int(time.time())
                if data_one:
                    id = data_one['id']
                    dbdata['twitter_id'] = twitter_id
                    dbdata['updated'] = today_time
                    dbdata['uid'] = uid
                    dbdata['sorts'] = sorts
                    dbdata['remark'] = remark
                    dbdata['category_id'] = cid
                    result_id = dbMysql.table('guzi_member_twitter_map ').where(f"id = '{id}'").save(dbdata)
                else:

                    ###统计此账号下有多少个推特，超过配置的限制，不让再增加
                    total_twitter = dbMysql.table('guzi_member_twitter_map').where(
                        f"uid='{uid}' AND status='1'").count()
                    data_one = dbMysql.table('guzi_member').where(f"uid='{uid}'").field(
                        "max_twitter,max_discord,max_discord_channel").find()
                    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
                    db_max_twitter = data_one['max_twitter']
                    # 取两个限制中较大的一个
                    max_limit = max(SYSTEM_MAX_TWITTER, db_max_twitter)
                    if total_twitter >= max_limit:
                        return jsonify({
                            'status': 0,
                            'message': f'对不起，可能更换过新推特链接，<br/>已超过系统限制的 <span style="color:#16b777;">{max_limit}</span> 个账号，请联系管理员！'
                        })

                    # 获取当前日期
                    dbdata['twitter_id'] = twitter_id
                    dbdata['uid'] = uid
                    dbdata['sorts'] = sorts
                    dbdata['remark'] = remark
                    dbdata['category_id'] = cid
                    dbdata['created'] = today_time
                    dbdata['status'] = 1
                    result_id = dbMysql.table('guzi_member_twitter_map ').add(dbdata)

                time.sleep(1)

                return jsonify({
                    'status': 1,
                    'message': '恭喜您，数据修改成功！'
                })


        else:
            return jsonify({
                'status': 0,
                'message': '对不起，无权限修改此数据！'
            })



@twitter.route('/twitter/addbatch', methods=['POST'])
@require_user_async  # 使用装饰器来验证登录状态
@check_user_login_do
async def addbatch():
    uid = g.uid

    if request.method == 'POST':
        data = await request.get_json()
        alldata = data.get('alldata', [])
        #print("收到的地址数据：", alldata)

        if not alldata:
            return jsonify({
                'status': 0,
                'message': '对不起，空数据不能提交！'
            })

        success = False  # 标记是否至少成功插入一条
        failed_usernames = []  # 记录插入失败的 username
        # 示例插入数据库
        for dataone in alldata:

            username = dataone.get('username')
            remark = dataone.get('remark')
            cid = dataone.get('cid')
            twitter_id = dataone.get('tid')
            show_name = dataone.get('show_name')
            url = dataone.get('url')
            avatar = dataone.get('avatar')
            followers = dataone.get('followers')
            fans = dataone.get('fans')
            description = dataone.get('description')
            #print(dataone)

            try:
                ###统计此账号下有多少个推特，超过配置的限制，不让再增加
                total_twitter = dbMysql.table('guzi_member_twitter_map').where(f"uid='{uid}' AND status='1'").count()
                data_one = dbMysql.table('guzi_member').where(f"uid='{uid}'").field("max_twitter,max_discord,max_discord_channel").find()
                #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
                db_max_twitter = data_one['max_twitter']
                # 取两个限制中较大的一个
                max_limit = max(SYSTEM_MAX_TWITTER,db_max_twitter)
                if total_twitter >= max_limit:
                    return jsonify({
                        'status': 0,
                        'message': f'对不起，已超过系统限制的 <span style="color:#16b777;">{max_limit}</span> 个账号，请联系管理员！'
                    })

                ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
                data_one = dbMysql.table('guzi_twitter').where(f"username='{username}' AND tid='{twitter_id}'").find()
                #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
                dbdata = {}
                today_time = int(time.time())
                dbdata['uid'] = uid
                dbdata['cid'] = cid
                dbdata['tid'] = twitter_id
                dbdata['username'] = username
                dbdata['show_name'] = show_name
                dbdata['url'] = url
                dbdata['description'] = description
                dbdata['remark'] = remark
                dbdata['avatar'] = avatar
                dbdata['followers'] = followers
                dbdata['fans'] = fans

                if data_one:
                    id = data_one['id']
                    dbdata['updated'] = today_time
                    result_id = dbMysql.table('guzi_twitter').where(f"id = '{id}'").save(dbdata)
                    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
                else:
                    dbdata['status'] = 1
                    dbdata['created'] = today_time
                    id = dbMysql.table('guzi_twitter').add(dbdata)
                    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句


                if twitter_id:

                    ###插入分类关联表
                    ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
                    data_one = dbMysql.table('guzi_twitter_category_map').where(
                        f"twitter_id='{twitter_id}' AND uid='{uid}' AND category_id='{cid}'").find()
                    dbdata = {}
                    today_time = int(time.time())
                    if data_one:
                        id = data_one['id']
                        dbdata['twitter_id'] = twitter_id
                        dbdata['category_id'] = cid
                        dbdata['updated'] = today_time
                        dbdata['uid'] = uid
                        result_id = dbMysql.table('guzi_twitter_category_map').where(f"id = '{id}'").save(dbdata)
                        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
                    else:
                        # 获取当前日期
                        dbdata['twitter_id'] = twitter_id
                        dbdata['category_id'] = cid
                        dbdata['uid'] = uid
                        dbdata['created'] = today_time
                        dbdata['status'] = 1
                        result_id = dbMysql.table('guzi_twitter_category_map').add(dbdata)
                        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

                    ###插入会员与推特账号关联表
                    ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
                    data_one = dbMysql.table('guzi_member_twitter_map ').where(
                        f"twitter_id='{twitter_id}' AND uid='{uid}' ").find()
                    dbdata = {}
                    today_time = int(time.time())
                    if data_one:
                        id = data_one['id']
                        dbdata['twitter_id'] = twitter_id
                        dbdata['updated'] = today_time
                        dbdata['uid'] = uid
                        dbdata['remark'] = remark
                        dbdata['category_id'] = cid
                        result_id = dbMysql.table('guzi_member_twitter_map ').where(f"id = '{id}'").save(dbdata)
                        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
                    else:
                        # 获取当前日期
                        dbdata['twitter_id'] = twitter_id
                        dbdata['uid'] = uid
                        dbdata['remark'] = remark
                        dbdata['category_id'] = cid
                        dbdata['created'] = today_time
                        dbdata['status'] = 1
                        result_id = dbMysql.table('guzi_member_twitter_map ').add(dbdata)
                        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
                    success = True  # 有一个成功就标记

            except Exception as e:
                #print(f"Inserting {username} failed: {str(e)}")
                failed_usernames.append(username)

        # 最后统一处理结果
        if success:
            result = {
                'status': 1,
                'message': '恭喜您，数据增加成功！'
            }
        else:
            # 将 failed_usernames 转换为以逗号分隔的字符串部分失败用户（前5个）
            failed_usernames_str = ', '.join(failed_usernames[:5])
            result = {
                'status': 0,
                'message': f'对不起，以下账号可能您已关注过（只显示前5个）：{failed_usernames_str}',
                "failed_usernames": failed_usernames
            }

        return result



    else:
        return jsonify({
            'status': 0,
            'message': '对不起，数据增加失败！'
        })




@twitter.route('/twitter/add', methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
@check_user_login_do
async def add():
    uid = g.uid

    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        username = form.get('username')
        remark = form.get('remark')
        cid = form.get('cid')
        twitter_id = form.get('tid')
        show_name = form.get('show_name')
        url = form.get('url')
        avatar = form.get('avatar')
        followers = form.get('followers')
        fans = form.get('fans')
        description = form.get('description')

        ###统计此账号下有多少个推特，超过配置的限制，不让再增加
        total_twitter = dbMysql.table('guzi_member_twitter_map').where(f"uid='{uid}' AND status='1'").count()
        data_one = dbMysql.table('guzi_member').where(f"uid='{uid}'").field("max_twitter,max_discord,max_discord_channel").find()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        db_max_twitter = data_one['max_twitter']
        # 取两个限制中较大的一个
        max_limit = max(SYSTEM_MAX_TWITTER,db_max_twitter)
        if total_twitter >= max_limit:
            return jsonify({
                'status': 0,
                'message': f'对不起，已超过系统限制的 <span style="color:#16b777;">{max_limit}</span> 个账号，请联系管理员！'
            })

        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_twitter').where(f"username='{username}' AND tid='{twitter_id}'").find()
        dbdata = {}
        today_time = int(time.time())
        dbdata['uid'] = uid
        dbdata['cid'] = cid
        dbdata['tid'] = twitter_id
        dbdata['username'] = username
        dbdata['show_name'] = show_name
        dbdata['url'] = url
        dbdata['description'] = description
        dbdata['remark'] = remark
        dbdata['avatar'] = avatar
        dbdata['followers'] = followers
        dbdata['fans'] = fans

        if data_one:
            id = data_one['id']
            dbdata['updated'] = today_time
            result_id = dbMysql.table('guzi_twitter').where(f"id = '{id}'").save(dbdata)
        else:
            dbdata['status'] = 1
            dbdata['created'] = today_time
            id = dbMysql.table('guzi_twitter').add(dbdata)
            #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句


        if twitter_id:

            ###插入分类关联表
            ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
            data_one = dbMysql.table('guzi_twitter_category_map').where(
                f"twitter_id='{twitter_id}' AND uid='{uid}' AND category_id='{cid}'").find()
            dbdata = {}
            today_time = int(time.time())
            if data_one:
                id = data_one['id']
                dbdata['twitter_id'] = twitter_id
                dbdata['category_id'] = cid
                dbdata['updated'] = today_time
                dbdata['uid'] = uid
                result_id = dbMysql.table('guzi_twitter_category_map').where(f"id = '{id}'").save(dbdata)
            else:
                # 获取当前日期
                dbdata['twitter_id'] = twitter_id
                dbdata['category_id'] = cid
                dbdata['uid'] = uid
                dbdata['created'] = today_time
                dbdata['status'] = 1
                result_id = dbMysql.table('guzi_twitter_category_map').add(dbdata)
                # print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

            ###插入会员与推特账号关联表
            ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
            data_one = dbMysql.table('guzi_member_twitter_map ').where(
                f"twitter_id='{twitter_id}' AND uid='{uid}' ").find()
            dbdata = {}
            today_time = int(time.time())
            if data_one:
                id = data_one['id']
                dbdata['twitter_id'] = twitter_id
                dbdata['updated'] = today_time
                dbdata['uid'] = uid
                dbdata['remark'] = remark
                dbdata['category_id'] = cid
                result_id = dbMysql.table('guzi_member_twitter_map ').where(f"id = '{id}'").save(dbdata)
            else:
                # 获取当前日期
                dbdata['twitter_id'] = twitter_id
                dbdata['uid'] = uid
                dbdata['remark'] = remark
                dbdata['category_id'] = cid
                dbdata['created'] = today_time
                dbdata['status'] = 1
                result_id = dbMysql.table('guzi_member_twitter_map ').add(dbdata)


            return jsonify({
                'status': 1,
                'message': '恭喜您，数据增加成功！'
            })


        else:
            return jsonify({
                'status': 0,
                'message': '对不起，数据增加失败！'
            })

    return render_template('add.html')




@twitter.route('/twitter/delete', methods=['POST'])
@require_user_async  # 使用装饰器来验证登录状态
@check_user_login_do
async def delete():  # 因为 require_login 会解码 token
    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        twitter_id = form.get('id')
        uid = g.uid

        ###删除分类关联数据
        where = f"twitter_id='{twitter_id}' AND uid='{uid}'"
        result = dbMysql.table('guzi_twitter_category_map').where(where).delete()  # 返回删除的行数

        ###删除推特关联数据
        where = f"twitter_id='{twitter_id}' AND uid='{uid}'"
        result = dbMysql.table('guzi_member_twitter_map ').where(where).delete()  # 返回删除的行数

        if result:

            return jsonify({
                'status': 1,
                'message': '恭喜您，数据删除成功！'
            })

        else:
            return jsonify({
                'status': 0,
                'message': f'对不起，数据删除失败！{id}'
            })

