from flask import Flask, render_template, request, jsonify,g, Blueprint
from eth_account.messages import encode_defunct
from eth_account import Account
from functools import wraps
import time
import jwt
import datetime
from util.db import *
from auth import require_user

# 创建一个 Blueprint 用于 Web3 登录功能
category = Blueprint('category', __name__)


@category.route('/category/twitter', methods=['GET'])
def twitter():
    return render_template("category/twitter.html")


@category.route('/category/discord', methods=['GET'])
def discord():
    return render_template("category/discord.html")

@category.route('/category/list', methods=['GET', 'POST'])
@require_user
def list():
    uid = g.uid
    is_type = request.args.get('is_type', default=1, type=int)
    data = dbMysql.table('guzi_category').where(f"uid='{uid}'  AND is_type='{is_type}' AND status=1").field('id,title').select()
    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    return jsonify({'status': 1, 'data': data})



@category.route("/category/page", methods=['GET', 'POST'])
@require_user  # 使用装饰器来验证登录状态
def page():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        is_type = request.args.get('is_type', default=1, type=int)


        where = f"uid='{uid}' AND is_type='{is_type}' AND status=1"


        order = "id DESC"

        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1

        data_list = dbMysql.table('guzi_category').where(where).order(order).page(page, limit).select()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        total =  dbMysql.table('guzi_category').where(where).count()

        layui_result = {
            "code": 0,
            "count": total,
            "data": [
                {
                    "num": i + start_index,
                    "id": item["id"],
                    "uid": item["uid"],
                    "title": item["title"],
                    "total": item["total"],
                    "remark": item["remark"]
                } for i, item in enumerate(data_list)
            ]
        }

        return jsonify(layui_result)



@category.route('/category/del_cate', methods=['POST'])
@require_user  # 使用装饰器来验证登录状态
def del_cate():  # 因为 require_login 会解码 token
    if request.method == 'POST':
        id = request.form.get('id')
        uid = g.uid
        where = f"id='{id}' AND uid='{uid}'"
        result = dbMysql.table('guzi_category').where(where).delete()  # 返回删除的行数

        if result:
            where = f"cactegory_id='{id}' AND uid='{uid}'"
            result = dbMysql.table('guzi_twitter_category_map').where(where).delete()  # 返回删除的行数

            return jsonify({
                'status': 1,
                'message': '恭喜您，数据删除成功！'
            })

        else:
            return jsonify({
                'status': 0,
                'message': f'对不起，数据删除失败！{id}'
            })

@category.route('/category/add', methods=['POST'])
@require_user
def add():
    uid = g.uid
    address = g.address
    if not address:
        return jsonify({"error": "Error Missing address "}), 400


    if request.method == 'POST':

        title = request.form.get('username')
        remark = request.form.get('remark')
        is_type = request.form.get('is_type')

        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_category').where(
            f"title='{title}' AND uid='{uid}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            uid = data_one['uid']
            dbdata['updated'] = today_time
            dbdata['remark'] = remark
            dbdata['title'] = title
            result_db = dbMysql.table('guzi_category').where(f"uid = '{uid}'").save(dbdata)
        else:
            # 获取当前日期
            dbdata['title'] = title
            dbdata['remark'] = remark
            dbdata['is_type'] = is_type
            dbdata['uid'] = uid
            dbdata['status'] = 1
            dbdata['created'] = today_time
            result_db = dbMysql.table('guzi_category').add(dbdata)
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


@category.route('/category/edit', methods=['POST'])
@require_user
def edit():
    uid = g.uid
    address = g.address
    if not address:
        return jsonify({"error": "Error Missing address "}), 400


    if request.method == 'POST':

        title = request.form.get('username')
        remark = request.form.get('remark')
        id = request.form.get('id')

        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_category').where(
            f"id='{id}' AND uid='{uid}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            uid = data_one['uid']
            dbdata['updated'] = today_time
            dbdata['remark'] = remark
            dbdata['title'] = title
            result_db = dbMysql.table('guzi_category').where(f"id='{id}'").save(dbdata)

            if result_db:
                return jsonify({
                    'status': 1,
                    'message': '恭喜您，数据修改成功！'
                })

        return jsonify({
            'status': 0,
            'message': '对不起，数据修改失败！'
        })