from quart import Quart, render_template, request, jsonify,g, Blueprint

from eth_account.messages import encode_defunct
from eth_account import Account
from functools import wraps
import time
import jwt
import datetime
from util.db import *
from auth import require_user,require_user_async

# 创建一个 Blueprint 用于 Web3 登录功能
website = Blueprint('website', __name__)



@website.route('/website/list', methods=['GET', 'POST'])
@require_user
def list():
    uid = g.uid
    is_type = request.args.get('is_type', default=1, type=int)
    data = dbMysql.table('guzi_website').where(f"uid='{uid}'  AND is_type='{is_type}' AND status=1").field('id,title').select()
    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    return jsonify({'status': 1, 'data': data})



@website.route("/website/page", methods=['GET', 'POST'])
def page():

    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        is_type = request.args.get('is_type', default=1, type=int)

        where = " status ='1'"

        order = "sort DESC"

        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1

        data_list = dbMysql.table('guzi_website').where(where).order(order).page(page, limit).select()
        # print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        total = dbMysql.table('guzi_website').where(where).count()

        if total > 0:
            layui_result = {
                "code": 0,
                "count": total,
                "data": [
                    {
                        "num": i + start_index,
                        "id": item["id"],
                        "title": item["title"],
                        "description": item["description"],
                        "logo": item["logo"],
                        "url": item["url"],
                        "created": item["created"] if item["created"] else '-'
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



@website.route('/website/del_cate', methods=['POST'])
@require_user_async  # 使用装饰器来验证登录状态
async def del_cate():  # 因为 require_login 会解码 token
    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        id = form.get('id')
        uid = g.uid
        where = f"id='{id}' AND uid='{uid}'"
        result = dbMysql.table('guzi_website').where(where).delete()  # 返回删除的行数

        if result:
            where = f"category_id='{id}' AND uid='{uid}'"
            result = dbMysql.table('guzi_twitter_website_map').where(where).delete()  # 返回删除的行数

            return jsonify({
                'status': 1,
                'message': '恭喜您，数据删除成功！'
            })

        else:
            return jsonify({
                'status': 0,
                'message': f'对不起，数据删除失败！{id}'
            })

@website.route('/website/add', methods=['POST'])
@require_user_async
async def add():
    uid = g.uid
    address = g.address
    if not address:
        return jsonify({"error": "Error Missing address "}), 400


    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        title = form.get('username')
        remark = form.get('remark')
        is_type = form.get('is_type')

        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_website').where(
            f"title='{title}' AND uid='{uid}' AND is_type='{is_type}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            id = data_one['id']
            dbdata['updated'] = today_time
            dbdata['remark'] = remark
            dbdata['title'] = title
            result_db = dbMysql.table('guzi_website').where(f"id = '{id}'").save(dbdata)
        else:
            # 获取当前日期
            dbdata['title'] = title
            dbdata['remark'] = remark
            dbdata['is_type'] = is_type
            dbdata['uid'] = uid
            dbdata['status'] = 1
            dbdata['created'] = today_time
            result_db = dbMysql.table('guzi_website').add(dbdata)
            #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        if result_db:
            return jsonify({
                'status': 1,
                'message': '恭喜您，数据增加成功！'
            })
        else:
            return jsonify({
                'status': 0,
                'message': '对不起，数据增加失败！'
            })


@website.route('/website/edit', methods=['POST'])
@require_user_async
async def edit():
    uid = g.uid
    address = g.address
    if not address:
        return jsonify({"error": "Error Missing address "}), 400


    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        title = form.get('username')
        remark = form.get('remark')
        id = form.get('id')

        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_website').where(
            f"id='{id}' AND uid='{uid}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            uid = data_one['uid']
            dbdata['updated'] = today_time
            dbdata['remark'] = remark
            dbdata['title'] = title
            result_db = dbMysql.table('guzi_website').where(f"id='{id}' AND uid='{uid}'").save(dbdata)

            if result_db:
                return jsonify({
                    'status': 1,
                    'message': '恭喜您，数据修改成功！'
                })

        return jsonify({
            'status': 0,
            'message': '对不起，数据修改失败！'
        })