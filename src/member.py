# -*- coding: utf-8 -*-
# from quart import Quart, render_template, request, jsonify,g, Blueprint
from util.db import *
from util.utils import generate_invite_codes
from src.auth import require_user,require_user_async,require_admin

# 创建一个 Blueprint 用于 Web3 登录功能
member = Blueprint('member', __name__)


@member.route('/member/index', methods=['GET'])
async def index():
    return await render_template("member/index.html")


@member.route('/member/error', methods=['GET'])
async def error():
    return await render_template("member/error.html")


@member.route('/member/codes', methods=['GET'])
async def codes():
    uid = g.get("uid")  # 从 g 中获取 uid
    return await render_template("member/codes.html")

@member.route('/member/list', methods=['GET', 'POST'])
@require_user_async
@require_admin()
async def list():
    uid = g.uid
    is_type = request.args.get('is_type', default=1, type=int)
    data = dbMysql.table('guzi_member').where(f"uid='{uid}'  AND is_type='{is_type}' AND status=1").field('id,title').select()
    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    return jsonify({'status': 1, 'data': data})



@member.route("/member/page_codes", methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
@require_admin()
async def page_codes():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        is_used = request.args.get('is_used', default=1, type=int)
        keyword = request.args.get('keyword')

        where_sql_clauses = [" a.id >='0'"]
        if keyword:
            where_sql_clauses.append(f" ( a.uid LIKE '%{keyword}%'   OR a.code LIKE '%{keyword}%'   OR b.wallet LIKE '%{keyword}%' )  ")

        where_sql = ' AND '.join(where_sql_clauses)

        order_sql = f"a.id DESC"
        # 然后再计算偏移量
        offset = (page - 1) * limit
        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1
        sql = f"SELECT a.*, b.wallet,b.username FROM guzi_invite_codes a LEFT JOIN guzi_member b ON a.uid = b.uid WHERE {where_sql} ORDER BY {order_sql}   LIMIT  {limit} OFFSET {offset}"
        data_list = dbMysql.query(sql)
        #data_list = dbMysql.table('guzi_invite_codes').where(where).order(order).page(page, limit).select()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        #total =  dbMysql.table('guzi_invite_codes').where(where).count()
        total_sql = f"SELECT COUNT(*) as total FROM guzi_invite_codes a LEFT JOIN guzi_member b ON a.uid = b.uid WHERE {where_sql}"
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
                        "code": item["code"],
                        "username": item["username"] if item["username"] else '-' ,
                        "is_used": item["is_used"],
                        "wallet": item["wallet"] if item["wallet"] else '-' ,
                        "created": item["created"],
                        "use_time": item["use_time"]
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


@member.route("/member/page", methods=['GET', 'POST'])
@require_user_async  # 使用装饰器来验证登录状态
@require_admin()
async def page():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        is_type = request.args.get('is_type', default=1, type=int)
        keyword = request.args.get('keyword')
        where_clauses = [" uid >='0'"]
        if keyword:
            where_clauses.append(
                f" ( wallet LIKE '%{keyword}%' OR username LIKE '%{keyword}%'  OR uid LIKE '%{keyword}%'   OR code LIKE '%{keyword}%'  OR remark LIKE '%{keyword}%' ) ")

        where = ' AND '.join(where_clauses)


        order = "uid DESC"

        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1

        data_list = dbMysql.table('guzi_member').where(where).order(order).page(page, limit).select()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        total =  dbMysql.table('guzi_member').where(where).count()

        if total > 0:
            layui_result = {
                "code": 0,
                "count": total,
                "data": [
                    {
                        "num": i + start_index,
                        "uid": item["uid"],
                        "wallet": item["wallet"],
                        "status": item["status"],
                        "username": item["username"],
                        "max_twitter": item["max_twitter"],
                        "max_discord": item["max_discord"],
                        "max_discord_channel": item["max_discord_channel"],
                        "code": item["code"] if item["code"] not in [None, '', 0, '0'] else '-',
                        "created": item["created"],
                        "remark": item["remark"] if item["remark"] else '-'
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



@member.route('/member/del_codes', methods=['POST'])
@require_user_async  # 使用装饰器来验证登录状态
@require_admin()
async def del_codes():
    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        id = form.get('id')
        uid = g.uid
        where = f"id='{id}' AND is_used='0'"
        result = dbMysql.table('guzi_invite_codes').where(where).delete()  # 返回删除的行数

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

@member.route('/member/add_code', methods=['POST'])
@require_user_async
@require_admin()
async def add_code():
    uid = g.uid

    if request.method == 'POST':
        form = await request.form  # 注意必须 await

        nums_str = form.get('nums')
        if not nums_str or not nums_str.strip().isdigit():
            return jsonify({
                'status': 0,
                'message': '邀请码数量必须大于0！'
            })

        nums = int(nums_str)


        codes = generate_invite_codes(nums)
        print(codes)
        result_db = 0
        for code in codes:
            ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
            data_one = dbMysql.table('guzi_invite_codes').where(f"code='{code}'").find()
            dbdata = {}
            today_time = int(time.time())

            if not data_one:
                # 获取当前日期
                dbdata['code'] = code
                dbdata['created'] = today_time
                result_db = dbMysql.table('guzi_invite_codes').add(dbdata)
                print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

        if result_db:
            return jsonify({
                'status': 1,
                'message': '恭喜您，邀请码增加成功！'
            })
        else:
            return jsonify({
                'status': 0,
                'message': '对不起，邀请码增加失败！'
            })


@member.route('/member/edit', methods=['POST'])
@require_user_async
@require_admin()
async def edit():
    uid = g.uid


    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        remark = form.get('remark')
        max_twitter = form.get('max_twitter')
        max_discord = form.get('max_discord')
        max_discord_channel = form.get('max_discord_channel')

        uid = form.get('id')
        status = form.get('status')

        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_member').where( f"uid='{uid}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            dbdata['updated'] = today_time
            if remark:
                dbdata['remark'] = remark
                dbdata['max_twitter'] = max_twitter
                dbdata['max_discord'] = max_discord
                dbdata['max_discord_channel'] = max_discord_channel

            if status:
                dbdata['status'] = status
            result_db = dbMysql.table('guzi_member').where(f"uid='{uid}'").save(dbdata)

            if result_db:
                return jsonify({
                    'status': 1,
                    'message': '恭喜您，操作成功！'
                })

        return jsonify({
            'status': 0,
            'message': '对不起，操作失败！'
        })