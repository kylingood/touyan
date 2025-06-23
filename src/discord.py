# -*- coding: utf-8 -*-
from quart import Quart, render_template, request, jsonify, g, Blueprint
from util.db import *
from src.auth import check_user_login_do,require_user_async
from src.web3_auth import insert_message_db
from src.config import SYSTEM_MAX_DISCORD,SYSTEM_MAX_DISCORD_CHANNEL,DEFAULT_UID
import asyncio
import requests

# 创建一个 Blueprint 用于 Web3 登录功能
discord = Blueprint('discord', __name__)



@discord.route('/discord/index', methods=['GET'])
async def index():

    return await render_template("/discord/index.html")


@discord.route("/discord/page", methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
async def page():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        cid = request.args.get('cid', default=0, type=int)
        keyword = request.args.get('keyword')

        where_sql_clauses = [f" d.uid='{uid}' AND d.status=1"]

        order_sql = "d.id DESC"

        if cid:
            where_sql_clauses.append(f"d.cid='{cid}'")

        if keyword:
            where_sql_clauses.append(
                f"(d.username LIKE '%{keyword}%' OR d.global_name LIKE '%{keyword}%' OR "
                f"d.token LIKE '%{keyword}%' OR d.email LIKE '%{keyword}%' OR "
                f"d.remark LIKE '%{keyword}%' OR c.title LIKE '%{keyword}%' )"
            )

        where_sql = ' AND '.join(where_sql_clauses)
        # 然后再计算偏移量
        offset = (page - 1) * limit
        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1

        sql = f'''SELECT 
                    d.*, 
                    c.title AS category_title
                FROM 
                    guzi_discord AS d
                LEFT JOIN 
                    guzi_category AS c 
                ON 
                    d.cid = c.id
                WHERE {where_sql} ORDER BY {order_sql}   LIMIT  {limit} OFFSET {offset}'''

        data_list = dbMysql.query(sql)
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        total_sql = f"SELECT   COUNT(*) AS total  FROM    guzi_discord AS d  LEFT JOIN   guzi_category AS c  ON   d.cid = c.id  WHERE  {where_sql}"
        print(total_sql)  # 打印由Model类拼接填充生成的SQL语句
        total_list = dbMysql.query(total_sql)
        total = total_list[0]['total'] if total_list and 'total' in total_list[0] else 0



        if total > 0:
            layui_result = {
                "code": 0,
                "count": total,
                "data": [
                    {
                        "num": i + start_index,
                        "id": item["id"],
                        "uid": item["uid"],
                        "cid": item["cid"],
                        "cate_name": item["category_title"] or "未知分类",
                        "username": item["username"],
                        "global_name": item["global_name"],
                        "token": (
                            item["token"][:5] + "****" + item["token"][-4:]
                            if getattr(g, 'login_uid', 0) != DEFAULT_UID and getattr(g, 'login_uid', 0) <= 0 and  "token" in item and len(
                                item["token"]) > 6
                            else item["token"]
                        ),
                        "email": (
                            item["email"][:3] + "****" + item["email"].split('@')[1]
                            if getattr(g, 'login_uid', 0) != DEFAULT_UID and getattr(g, 'login_uid', 0) <= 0 and "email" in item and len(
                                item["email"]) > 6
                            else item["email"]
                        ),
                        "remark": item["remark"]
                    } for i, item in enumerate(data_list)
                ]
            }
            print(getattr(g, 'login_uid', 0))
            print(DEFAULT_UID)
            print(layui_result)
        else:
            layui_result = {
                "code": 0,
                "count": 0,
                "data": []
            }



        return jsonify(layui_result)




@discord.route('/discord/edit', methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
@check_user_login_do
async def edit():
    uid = g.uid

    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        username = form.get('username')
        remark = form.get('remark')
        cid = form.get('cid')
        discord_id = form.get('id')
        email = form.get('email')
        token = form.get('token')
        global_name = form.get('global_name')


        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_discord').where(
            f"uid='{uid}' AND id='{discord_id}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            id = data_one['id']
            dbdata['updated'] = today_time
            dbdata['global_name'] = global_name
            dbdata['username'] = username
            dbdata['remark'] = remark
            dbdata['email'] = email
            dbdata['token'] = token
            dbdata['uid'] = uid
            dbdata['cid'] = cid
            dbMysql.table('guzi_discord').where(f"id = '{id}'").save(dbdata)


        if discord_id:

            ###插入关联表
            ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
            data_one = dbMysql.table('guzi_discord_category_map').where(
                f"discord_id='{discord_id}' AND uid='{uid}' AND category_id='{cid}'").find()
            dbdata = {}
            if data_one:
                id = data_one['id']
                dbdata['discord_id'] = discord_id
                dbdata['category_id'] = cid
                dbdata['uid'] = uid
                result_id = dbMysql.table('guzi_discord_category_map').where(f"id = '{id}'").save(dbdata)
            else:
                # 获取当前日期
                dbdata['discord_id'] = discord_id
                dbdata['category_id'] = cid
                dbdata['uid'] = uid
                dbdata['status'] = 1
                result_id = dbMysql.table('guzi_discord_category_map').add(dbdata)
                # print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

            return jsonify({
                'status': 1,
                'message': '恭喜您，Discord账号修改成功！'
            })


        else:
            return jsonify({
                'status': 0,
                'message': '对不起，无权限修改此Discord账号！'
            })


@discord.route('/discord/add', methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
@check_user_login_do
async def add():
    uid = g.uid

    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        username = form.get('username')
        global_name = form.get('global_name')
        remark = form.get('remark')
        cid = form.get('cid')
        email = form.get('email')
        token = form.get('token')

        ###统计此账号下有多少个推特，超过配置的限制，不让再增加
        total_discord = dbMysql.table('guzi_discord').where(f"uid='{uid}' AND status='1'").count()
        data_one = dbMysql.table('guzi_member').where(f"uid='{uid}'").field("max_twitter,max_discord,max_discord_channel").find()
        # print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        db_max_discord = data_one['max_discord']
        # 取两个限制中较大的一个
        max_limit = max(SYSTEM_MAX_DISCORD, db_max_discord)
        if total_discord >= max_limit:
            return jsonify({
                'status': 0,
                'message': f'对不起，已超过系统限制的 <span style="color:#16b777;">{max_limit}</span> 个账号，请联系管理员！'
            })


        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_discord').where(
            f"username='{username}' AND uid='{uid}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            id = data_one['id']
            dbdata['updated'] = today_time
            dbdata['remark'] = remark
            dbdata['email'] = email
            dbdata['username'] = username
            dbdata['global_name'] = global_name
            dbdata['token'] = token
            discord_id = dbMysql.table('guzi_discord').where(f"id = '{id}'").save(dbdata)
        else:
            # 获取当前日期
            dbdata['username'] = username
            dbdata['global_name'] = global_name
            dbdata['remark'] = remark
            dbdata['email'] = email
            dbdata['token'] = token
            dbdata['uid'] = uid
            dbdata['cid'] = cid
            dbdata['status'] = 1
            dbdata['created'] = today_time
            discord_id = dbMysql.table('guzi_discord').add(dbdata)
            print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句


        if discord_id:

            ###插入关联表
            ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
            data_one = dbMysql.table('guzi_discord_category_map').where(
                f"discord_id='{discord_id}' AND uid='{uid}' AND category_id='{cid}'").find()
            dbdata = {}
            if data_one:
                id = data_one['id']
                dbdata['discord_id'] = discord_id
                dbdata['category_id'] = cid
                dbdata['uid'] = uid
                result_id = dbMysql.table('guzi_discord_category_map').where(f"id = '{id}'").save(dbdata)
            else:
                # 获取当前日期
                dbdata['discord_id'] = discord_id
                dbdata['category_id'] = cid
                dbdata['uid'] = uid
                dbdata['status'] = 1
                result_id = dbMysql.table('guzi_discord_category_map').add(dbdata)
                # print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

            return jsonify({
                'status': 1,
                'message': '恭喜您，Discord账号增加成功！'
            })


        else:
            return jsonify({
                'status': 0,
                'message': '对不起，Discord账号增加失败！'
            })

    return render_template('add.html')




@discord.route('/discord/delete', methods=['POST'])
@require_user_async  # 使用装饰器来验证登录状态
@check_user_login_do
async def delete():  # 因为 require_login 会解码 token
    if request.method == 'POST':

        form = await request.form  # 注意必须 await
        id = form.get('id')
        uid = g.uid
        data = await request.get_json()  # ✅ 这里必须加 await


        if id:
            where = f"id='{id}' AND uid='{uid}'"

            result = dbMysql.table('guzi_discord').where(where).delete()  # 返回删除的行数

            if result:
                where = f"discord_id='{id}' AND uid='{uid}'"
                result = dbMysql.table('guzi_discord_category_map').where(where).delete()  # 返回删除的行数

                return jsonify({
                    'status': 1,
                    'message': '恭喜您，数据删除成功！'
                })
        if data:
            ids = data.get('ids', [])
            if not isinstance(ids, list):
                return jsonify({'status': 0, 'message': '参数错误，ids 应该是一个列表'})

            print('将要删除的 Twitter ID 列表：', ids)
            # 构造 SQL 条件
            id_conditions = " OR ".join([f"id='{did}'" for did in ids])
            where = f"({id_conditions}) AND uid='{uid}'"
            result = dbMysql.table('guzi_discord').where(where).delete()  # 返回删除的行数
            print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
            if result:

                id_conditions = " OR ".join([f"discord_id='{did}'" for did in ids])
                where = f"({id_conditions}) AND uid='{uid}'"
                result = dbMysql.table('guzi_discord_category_map').where(where).delete()  # 返回删除的行数
                print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

                return jsonify({
                    'status': 1,
                    'message': '恭喜您，数据删除成功！'
                })


        else:
            return jsonify({
                'status': 0,
                'message': f'对不起，数据删除失败！{id}'
            })



## 监控频道列表
@discord.route('/discord/guild', methods=['GET'])
@discord.route('/discord/guild/gid/<int:gid>', methods=['GET'])
@discord.route('/discord/guild/did/<int:did>', methods=['GET'])
async def guild(gid=0, did=0):

    return await render_template("/discord/guild.html", gid=gid, did=did)


## 监控频道列表
@discord.route('/discord/message', methods=['GET'])
@discord.route('/discord/message/gid/<int:gid>', methods=['GET'])
async def message(gid=0):

    return await render_template("/discord/message.html", gid=gid)



@discord.route('/discord/list_data', methods=['GET', 'POST'])
@require_user_async
async def list_data():
    uid = g.uid
    data = dbMysql.table('guzi_discord').where(f"uid='{uid}'  AND  status=1").field('id,global_name').select()
    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    return jsonify({'status': 1, 'data': data})



@discord.route('/discord/guild_data', methods=['GET', 'POST'])
@require_user_async
async def guild_data():

    uid = g.uid
    data = dbMysql.table('guzi_discord_channel').where(f"uid='{uid}'  AND  status=1").order("id DESC").field('guild_id,guild_name,guild_icon').select()
    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    seen = set()
    result = []
    for row in data:
        gid = row.get('guild_id')
        if gid not in seen:
            seen.add(gid)
            result.append(row)
    return jsonify({'status': 1, 'data': result})



@discord.route('/discord/add_channel', methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
@check_user_login_do
async def add_channel():
    uid = g.uid
    if request.method == 'POST':
        form = await request.form  # 注意必须 await

        username = form.get('username')
        remark = form.get('remark')
        did = form.get('did')
        token = form.get('token')
        url = form.get('url')
        guild_id = form.get('guild_id')
        channel_id = form.get('channel_id')
        guild_name = form.get('guild_name')
        guild_icon = form.get('guild_icon')
        guild_description = form.get('guild_description')

        ###统计此账号下有多少个监控频道，超过配置的限制，不让再增加
        total_discord_channel = dbMysql.table('guzi_discord_channel').where(f"uid='{uid}' AND status='1'").count()
        data_one = dbMysql.table('guzi_member').where(f"uid='{uid}'").field(
            "max_twitter,max_discord,max_discord_channel").find()
        # print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        db_max_discord_channel = data_one['max_discord_channel']
        # 取两个限制中较大的一个
        max_limit = max(SYSTEM_MAX_DISCORD_CHANNEL, db_max_discord_channel)
        if total_discord_channel >= max_limit:
            return jsonify({
                'status': 0,
                'message': f'对不起，已超过系统限制的 <span style="color:#16b777;">{max_limit}</span> 个频道，请联系管理员！'
            })


        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_discord_channel').where(
            f"did='{did}' AND channel_id='{channel_id}' AND uid='{uid}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            discord_id = data_one['id']
            dbdata['updated'] = today_time
            dbdata['username'] = username
            dbdata['remark'] = remark
            dbdata['did'] = did
            dbdata['url'] = url
            dbdata['guild_id'] = guild_id
            dbdata['guild_name'] = guild_name
            dbdata['guild_icon'] = guild_icon
            dbdata['guild_description'] = guild_description
            dbdata['channel_id'] = channel_id
            dbdata['token'] = token
            dbdata['status'] = 1
            discord_id = dbMysql.table('guzi_discord_channel').where(f"id = '{discord_id}'").save(dbdata)
        else:
            # 获取当前日期
            dbdata['username'] = username
            dbdata['remark'] = remark
            dbdata['url'] = url
            dbdata['token'] = token
            dbdata['uid'] = uid
            dbdata['did'] = did
            dbdata['guild_id'] = guild_id
            dbdata['guild_name'] = guild_name
            dbdata['guild_icon'] = guild_icon
            dbdata['guild_description'] = guild_description
            dbdata['channel_id'] = channel_id
            dbdata['status'] = 1
            dbdata['created'] = today_time
            discord_id = dbMysql.table('guzi_discord_channel').add(dbdata)

        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        if discord_id:
            ## 修改的频道数据后，同步更新频道公告
            # mid = await insert_message_db(dbdata)
            return jsonify({
                'status': 1,
                'message': '恭喜您，监控频道增加成功！'
            })

        else:
            return jsonify({
                'status': 0,
                'message': f'对不起，监控频道增加失败！{discord_id}'
            })


@discord.route('/discord/edit_channel', methods=['GET', 'POST'])
@require_user_async
@check_user_login_do
async def edit_channel():
    uid = g.uid

    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        id = form.get('id')
        username = form.get('username')
        remark = form.get('remark')
        did = form.get('did')
        token = form.get('token')
        url = form.get('url')
        guild_id = form.get('guild_id')
        channel_id = form.get('channel_id')
        guild_name = form.get('guild_name')
        guild_icon = form.get('guild_icon')
        guild_description = form.get('guild_description')

        data_one = dbMysql.table('guzi_discord_channel').where(f"id='{id}' AND uid='{uid}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            discord_id = data_one['id']
            dbdata['updated'] = today_time
            dbdata['username'] = username
            dbdata['remark'] = remark
            dbdata['did'] = did
            dbdata['url'] = url
            dbdata['guild_id'] = guild_id
            dbdata['guild_name'] = guild_name
            dbdata['guild_icon'] = guild_icon
            dbdata['guild_description'] = guild_description
            dbdata['channel_id'] = channel_id
            dbdata['token'] = token
            discord_id = dbMysql.table('guzi_discord_channel').where(f"id = '{discord_id}'").save(dbdata)
        else:

            ###统计此账号下有多少个监控频道，超过配置的限制，不让再增加
            total_discord_channel = dbMysql.table('guzi_discord_channel').where(f"uid='{uid}' AND status='1'").count()
            data_one = dbMysql.table('guzi_member').where(f"uid='{uid}'").field(
                "max_twitter,max_discord,max_discord_channel").find()
            # print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
            db_max_discord_channel = data_one['max_discord_channel']
            # 取两个限制中较大的一个
            max_limit = max(SYSTEM_MAX_DISCORD_CHANNEL, db_max_discord_channel)
            if total_discord_channel >= max_limit:
                return jsonify({
                    'status': 0,
                    'message': f'对不起，已超过系统限制的 <span style="color:#16b777;">{max_limit}</span> 个频道，请联系管理员！'
                })

            dbdata['username'] = username
            dbdata['remark'] = remark
            dbdata['url'] = url
            dbdata['token'] = token
            dbdata['uid'] = uid
            dbdata['did'] = did
            dbdata['guild_id'] = guild_id
            dbdata['guild_name'] = guild_name
            dbdata['guild_icon'] = guild_icon
            dbdata['guild_description'] = guild_description
            dbdata['channel_id'] = channel_id
            dbdata['status'] = 1
            dbdata['created'] = today_time
            discord_id = dbMysql.table('guzi_discord_channel').add(dbdata)

        if discord_id:

            ## 修改的频道数据后，同步更新频道公告
            # mid = await insert_message_db(dbdata)

            return jsonify({
                'status': 1,
                'message': '恭喜您，数据修改成功！'
            })
        else:
            return jsonify({
                'status': 0,
                'message': f'对不起，数据增加失败！{discord_id}'
            })


@discord.route("/discord/page_channel", methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
async def page_channel():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        did = request.args.get('did', default=0, type=int)
        guild_id = request.args.get('guild_id', default=0, type=int)
        keyword = request.args.get('keyword')



        where_sql_clauses = [f"uid='{uid}' AND status=1"]

        order = "id DESC"
        if did:
            where_sql_clauses.append(f" did='{did}' ")

        if guild_id:
            where_sql_clauses.append(f" guild_id='{guild_id}'")


        if keyword:
            where_sql_clauses.append(f" ( username LIKE '%{keyword}%'  OR remark LIKE '%{keyword}%'    OR guild_id LIKE '%{keyword}%'  OR channel_id LIKE '%{keyword}%'  "  
                                     f" OR guild_name LIKE '%{keyword}%'   OR guild_description LIKE '%{keyword}%'  OR token LIKE '%{keyword}%'  )  ")

        where_sql = ' AND '.join(where_sql_clauses)

        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1

        data_list = dbMysql.table('guzi_discord_channel').where(where_sql).order(order).page(page, limit).select()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        total =  dbMysql.table('guzi_discord_channel').where(where_sql).count()


        rows = dbMysql.table('guzi_discord').where(f"uid='{uid}' AND status=1").field('id,global_name').select()
        discord_data = {}
        for row in rows:
            discord_data[row['id']] = row['global_name']

        if total > 0:
            layui_result = {
                "code": 0,
                "count": total,
                "data": [
                    {
                        "num": i + start_index,
                        "id": item["id"],
                        "uid": item["uid"],
                        "did": item["did"],
                        "discord_name": discord_data.get(item["did"], "未知discord"),
                        "username": item["username"],
                        "token": item["token"],
                        "guild_id": item["guild_id"],
                        "guild_name": item["guild_name"],
                        "guild_icon": item["guild_icon"],
                        "guild_description": item["guild_description"],
                        "channel_id": item["channel_id"],
                        "url": item["url"],
                        "remark": item["remark"]
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


@discord.route('/discord/delete_channel', methods=['POST'])
@require_user_async  # 使用装饰器来验证登录状态
@check_user_login_do
async def delete_channel():  # 因为 require_login 会解码 token
    if request.method == 'POST':
        uid = g.uid
        form = await request.form  # 注意必须 await
        id = form.get('id')
        data = await request.get_json()  # ✅ 这里必须加 await

        if id:

            where = f"id='{id}' AND uid='{uid}'"

            result = dbMysql.table('guzi_discord_channel').where(where).delete()  # 返回删除的行数
            print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

            if result:
                return jsonify({
                    'status': 1,
                    'message': '恭喜您，监控数据移除成功！'
                })

        if data:
            ids = data.get('ids', [])
            if not isinstance(ids, list):
                return jsonify({'status': 0, 'message': '参数错误，ids 应该是一个列表'})

            print('将要删除的 Twitter ID 列表：', ids)
            # 构造 SQL 条件
            id_conditions = " OR ".join([f"id='{tid}'" for tid in ids])
            where = f"({id_conditions}) AND uid='{uid}'"
            print('将要删除的 Twitter ID 列表：', where)
            result = dbMysql.table('guzi_discord_channel').where(where).delete()  # 返回删除的行数
            print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

            if result:
                return jsonify({
                    'status': 1,
                    'message': '恭喜您，监控数据移除成功！'
                })


        else:
            return jsonify({
                'status': 0,
                'message': f'对不起，监控数据移除失败！{id}'
            })



@discord.route("/discord/page_messages", methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
async def page_messages():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        did = request.args.get('did', default=0, type=int)
        guild_id = request.args.get('guild_id', default=0, type=int)


        # 初始化
        where_clauses = ["status=1"]  # 永远有的条件
        where_channel = [f" uid='{uid}' AND status='1' "]
        order = "timestamp DESC,mid DESC"
        # 可选条件
        if did:
            where_clauses.append(f"did='{did}'")
            where_channel.append(f"did='{did}'")

        if guild_id:
            where_clauses.append(f"guild_id='{guild_id}'")
            where_channel.append(f"guild_id='{guild_id}'")

        where_channel_sql = ' AND '.join(where_channel)

        ## 先取到所有关注频道信息
        channel_list = dbMysql.table('guzi_discord_channel').where(where_channel_sql).field('channel_id').select()
        print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        if channel_list:
            channel_ids = [f"'{row['channel_id']}'" for row in channel_list]
            channel_in_sql = f"channel_id IN ({', '.join(channel_ids)})"
            where_clauses.append(channel_in_sql)
        else:
            layui_result = {
                "code": 0,
                "count": 0,
                "data": []
            }

            return jsonify(layui_result)

        where = ' AND '.join(where_clauses)

        print(where)


        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1

        #print(where)
        data_list = dbMysql.table('guzi_discord_message').where(where).order(order).page(page, limit).select()
        print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

        total_page =  dbMysql.table('guzi_discord_message').where(where).count()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        #total_page = 10
        rows = dbMysql.table('guzi_discord').where(f"uid='{uid}' AND status=1").field('id,global_name').select()
        discord_data = {}
        for row in rows:
            discord_data[row['id']] = row['global_name']

        if total_page > 0:
            layui_result = {
                "code": 0,
                "count": total_page,
                "data": [
                    {
                        "num": i + start_index,
                        "id": item["id"],
                        "did": item["did"],
                        "discord_name": discord_data.get(item["did"], "未知discord"),
                        "username": item["username"],
                        "timestamp": datetime.utcfromtimestamp(int(item["timestamp"])).strftime("%Y-%m-%d %H:%M:%S"),
                        "guild_id": item["guild_id"],
                        "guild_name": item["guild_name"],
                        "guild_icon": item["guild_icon"],
                        "guild_description": item["guild_description"],
                        "channel_id": item["channel_id"],
                        "url": item["url"],
                        "content": item["content"]
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