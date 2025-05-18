from quart import Quart, render_template, request, jsonify, g, Blueprint
from util.db import *
from auth import require_user,require_user_async
import asyncio


# 创建一个 Blueprint 用于 Web3 登录功能
discord = Blueprint('discord', __name__)


@discord.route('/discord/index', methods=['GET'])
async def index():

    return await render_template("/discord/index.html")


@discord.route("/discord/page", methods=['GET', 'POST'])
@require_user  # 使用装饰器来验证登录状态
def page():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        cid = request.args.get('cid', default=0, type=int)

        where = f"uid='{uid}' AND status=1"
        order = "id DESC"
        if cid:
            where = f"uid='{uid}' AND status=1 AND cid='{cid}' "

        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1

        data_list = dbMysql.table('guzi_discord').where(where).order(order).page(page, limit).select()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        total =  dbMysql.table('guzi_discord').where(where).count()


        rows = dbMysql.table('guzi_category').where(f"uid='{uid}' AND status=1").field('id,title').select()
        cate_data = {}
        for row in rows:
            cate_data[row['id']] = row['title']

        layui_result = {
            "code": 0,
            "count": total,
            "data": [
                {
                    "num": i + start_index,
                    "id": item["id"],
                    "uid": item["uid"],
                    "cid": item["cid"],
                    "cate_name": cate_data.get(item["cid"], "未知分类"),
                    "username": item["username"],
                    "global_name": item["global_name"],
                    "token": item["token"],
                    "email": item["email"],
                    "remark": item["remark"]
                } for i, item in enumerate(data_list)
            ]
        }

        return jsonify(layui_result)




@discord.route('/discord/edit', methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
async def edit():
    uid = g.uid

    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        username = form.get('username')
        remark = form.get('remark')
        cid = form.get('cid')
        id = form.get('id')
        email = form.get('email')
        token = form.get('token')
        global_name = form.get('global_name')


        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_discord').where(
            f"uid='{uid}' AND id='{id}'").find()
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
            discord_id = dbMysql.table('guzi_discord').where(f"id = '{id}'").save(dbdata)


            if discord_id:

                ###插入关联表
                ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
                data_one = dbMysql.table('guzi_discord_category_map').where(
                    f"discord_id='{discord_id}' AND uid='{uid}' AND cactegory_id='{cid}'").find()
                dbdata = {}
                if data_one:
                    id = data_one['id']
                    dbdata['discord_id'] = discord_id
                    dbdata['cactegory_id'] = cid
                    dbdata['uid'] = uid
                    result_id = dbMysql.table('guzi_discord_category_map').where(f"id = '{id}'").save(dbdata)
                else:
                    # 获取当前日期
                    dbdata['discord_id'] = discord_id
                    dbdata['cactegory_id'] = cid
                    dbdata['uid'] = uid
                    dbdata['status'] = 1
                    result_id = dbMysql.table('guzi_discord_category_map').add(dbdata)
                    # print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

                return jsonify({
                    'status': 1,
                    'message': '恭喜您，数据修改成功！'
                })


        else:
            return jsonify({
                'status': 0,
                'message': '对不起，无权限修改此数据！'
            })


@discord.route('/discord/add', methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
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
            #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句


        if discord_id:

            ###插入关联表
            ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
            data_one = dbMysql.table('guzi_discord_category_map').where(
                f"discord_id='{discord_id}' AND uid='{uid}' AND cactegory_id='{cid}'").find()
            dbdata = {}
            if data_one:
                id = data_one['id']
                dbdata['discord_id'] = discord_id
                dbdata['cactegory_id'] = cid
                dbdata['uid'] = uid
                result_id = dbMysql.table('guzi_discord_category_map').where(f"id = '{id}'").save(dbdata)
            else:
                # 获取当前日期
                dbdata['discord_id'] = discord_id
                dbdata['cactegory_id'] = cid
                dbdata['uid'] = uid
                dbdata['status'] = 1
                result_id = dbMysql.table('guzi_discord_category_map').add(dbdata)
                # print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

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




@discord.route('/discord/delete', methods=['POST'])
@require_user_async  # 使用装饰器来验证登录状态
async def delete():  # 因为 require_login 会解码 token
    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        id = form.get('id')
        uid = g.uid
        where = f"id='{id}' AND uid='{uid}'"
        result = dbMysql.table('guzi_discord').where(where).delete()  # 返回删除的行数

        if result:
            where = f"discord_id='{id}' AND uid='{uid}'"
            result = dbMysql.table('guzi_discord_category_map').where(where).delete()  # 返回删除的行数

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
@discord.route('/discord/guild/did/<int:did>', methods=['GET'])
async def guild(did=0):

    return await render_template("/discord/guild.html", did=did)


## 监控频道列表
@discord.route('/discord/message', methods=['GET'])
@discord.route('/discord/message/did/<int:did>', methods=['GET'])
async def message(did=0):

    return await render_template("/discord/message.html", did=did)



@discord.route('/discord/list', methods=['GET', 'POST'])
@require_user
def list():
    uid = g.uid
    data = dbMysql.table('guzi_discord').where(f"uid='{uid}'  AND  status=1").field('id,global_name').select()
    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    return jsonify({'status': 1, 'data': data})


@discord.route('/discord/add_channel', methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
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

            return jsonify({
                'status': 1,
                'message': '恭喜您，数据增加成功！'
            })

        else:
            return jsonify({
                'status': 0,
                'message': f'对不起，数据增加失败！{discord_id}'
            })


@discord.route('/discord/edit_channel', methods=['GET', 'POST'])
@require_user_async
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
@require_user  # 使用装饰器来验证登录状态
def page_channel():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        did = request.args.get('did', default=0, type=int)
        guild_id = request.args.get('guild_id', default=0, type=int)

        where = f"uid='{uid}' AND status=1"
        order = "id DESC"
        if did:
            where = f" did='{did}'  AND {where} "

        if guild_id:
            where = f" guild_id='{guild_id}' AND {where}"

        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1

        data_list = dbMysql.table('guzi_discord_channel').where(where).order(order).page(page, limit).select()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        total =  dbMysql.table('guzi_discord_channel').where(where).count()


        rows = dbMysql.table('guzi_discord').where(f"uid='{uid}' AND status=1").field('id,global_name').select()
        discord_data = {}
        for row in rows:
            discord_data[row['id']] = row['global_name']

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

        return jsonify(layui_result)


@discord.route('/discord/delete_channel', methods=['POST'])
@require_user_async  # 使用装饰器来验证登录状态
async def delete_channel():  # 因为 require_login 会解码 token
    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        id = form.get('id')
        uid = g.uid
        where = f"id='{id}' AND uid='{uid}'"
        result = dbMysql.table('guzi_discord_channel').where(where).delete()  # 返回删除的行数

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



@discord.route("/discord/page_messages", methods=['GET', 'POST'])
@require_user  # 使用装饰器来验证登录状态
def page_messages():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        did = request.args.get('did', default=0, type=int)
        guild_id = request.args.get('guild_id', default=0, type=int)

        where = f" status=1 "
        order = "timestamp DESC,mid DESC"
        if did:
            where = f" did='{did}'  AND {where} "

        if guild_id:
            where = f" guild_id='{guild_id}' AND {where}"

        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1


        data_list = dbMysql.table('guzi_discord_message').where(where).order(order).page(page, limit).select()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        total_page =  dbMysql.table('guzi_discord_message').where(where).count()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        total_page = 10
        rows = dbMysql.table('guzi_discord').where(f"uid='{uid}' AND status=1").field('id,global_name').select()
        discord_data = {}
        for row in rows:
            discord_data[row['id']] = row['global_name']

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

        return jsonify(layui_result)