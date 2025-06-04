# -*- coding: utf-8 -*-
from markdown_it.rules_core.normalize import NULL_RE
from quart import Quart, render_template, request, jsonify,g, Blueprint

from eth_account.messages import encode_defunct
from eth_account import Account
from functools import wraps
import time
import jwt
import datetime
from util.db import *
from src.auth import require_user_async,require_admin

# 创建一个 Blueprint 用于 Web3 登录功能
website = Blueprint('website', __name__)

@website.route('/website/index', methods=['GET'])
async def index():
    return await render_template("website/index.html")




@website.route("/website/page", methods=['GET', 'POST'])
def page():

    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        is_type = request.args.get('is_type', default=1, type=int)
        keyword = request.args.get('keyword')

        # 初始化
        if is_type == 1:
            where_clauses = [" id >='1'"]
        else:
            where_clauses = ["status = '1'"]

        if keyword:
            where_clauses.append(f" ( title LIKE '%{keyword}%' OR description LIKE '%{keyword}%'  OR id LIKE '%{keyword}%'   OR logo LIKE '%{keyword}%'  OR url LIKE '%{keyword}%' ) ")

        where = ' AND '.join(where_clauses)

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
                        "sort": item["sort"],
                        "status": item["status"],
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



@website.route('/website/add', methods=['POST'])
@require_user_async
@require_admin()
async def add():
    uid = g.uid
    address = g.address
    if not address:
        return jsonify({"error": "Error Missing address "}), 400


    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        title = form.get('title')
        description = form.get('description')
        logo = form.get('logo')
        sort = form.get('sort')
        status = form.get('status')
        url = form.get('url')


        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_website').where(f"url='{url}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            id = data_one['id']
            dbdata['updated'] = today_time
            dbdata['title'] = title
            dbdata['description'] = description
            dbdata['logo'] = logo
            dbdata['sort'] = sort
            dbdata['status'] = status
            dbdata['url'] = url
            dbdata['description'] = description

            result_db = dbMysql.table('guzi_website').where(f"id = '{id}'").save(dbdata)
        else:
            # 获取当前日期
            dbdata['title'] = title
            dbdata['description'] = description
            dbdata['logo'] = logo
            dbdata['sort'] = sort
            dbdata['status'] = status
            dbdata['url'] = url
            dbdata['description'] = description
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
@require_admin()
async def edit():
    uid = g.uid
    address = g.address
    if not address:
        return jsonify({"error": "Error Missing address "}), 400


    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        title = form.get('title')
        description = form.get('description')
        logo = form.get('logo')
        sort = form.get('sort')
        url = form.get('url')
        status = form.get('status')
        id = form.get('id')

        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_website').where( f"id='{id}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            dbdata['updated'] = today_time
            if title:
                dbdata['title'] = title
                dbdata['description'] = description
                dbdata['logo'] = logo
                dbdata['sort'] = sort
                dbdata['url'] = url

            if status:
                dbdata['status'] = status

            result_db = dbMysql.table('guzi_website').where(f"id='{id}'").save(dbdata)

            if result_db:
                return jsonify({
                    'status': 1,
                    'message': '恭喜您，数据修改成功！'
                })

        return jsonify({
            'status': 0,
            'message': '对不起，数据修改失败！'
        })



@website.route('/website/delete', methods=['POST'])
@require_user_async  # 使用装饰器来验证登录状态
@require_admin()
async def delete():
    if request.method == 'POST':
        form = await request.form  # 注意必须 await
        id = form.get('id')
        uid = g.uid
        where = f"id='{id}'"
        result = dbMysql.table('guzi_website').where(where).delete()  # 返回删除的行数

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