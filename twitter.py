from quart import Quart, render_template, request, jsonify,g, Blueprint
from eth_account.messages import encode_defunct
from eth_account import Account
from functools import wraps
import time
import jwt
import datetime
from util.db import *
from auth import require_user


# 创建一个 Blueprint 用于 Web3 登录功能
twitter = Blueprint('twitter', __name__)


@twitter.route('/twitter/index', methods=['GET'])
async def index():

    return await render_template("/twitter/index.html")


@twitter.route("/twitter/page", methods=['GET', 'POST'])
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

        data_list = dbMysql.table('guzi_twitter').where(where).order(order).page(page, limit).select()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        total =  dbMysql.table('guzi_twitter').where(where).count()


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
                    "followers": item["followers"],
                    "fans": item["fans"],
                    "remark": item["remark"]
                } for i, item in enumerate(data_list)
            ]
        }

        return  jsonify(layui_result)




@twitter.route('/twitter/edit', methods=['GET', 'POST'])
@require_user  # 使用装饰器来验证登录状态
def edit():
    uid = g.uid

    if request.method == 'POST':
        username = request.form.get('username')
        remark = request.form.get('remark')
        cid = request.form.get('cid')
        id = request.form.get('id')

        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_twitter').where(
            f"uid='{uid}' AND id='{id}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            id = data_one['id']
            dbdata['updated'] = today_time
            dbdata['username'] = username
            dbdata['remark'] = remark
            dbdata['uid'] = uid
            dbdata['cid'] = cid
            twitter_id = dbMysql.table('guzi_twitter').where(f"id = '{id}'").save(dbdata)


            if twitter_id:

                ###插入关联表
                ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
                data_one = dbMysql.table('guzi_twitter_category_map').where(
                    f"twitter_id='{twitter_id}' AND uid='{uid}' AND cactegory_id='{cid}'").find()
                dbdata = {}
                if data_one:
                    id = data_one['id']
                    dbdata['twitter_id'] = twitter_id
                    dbdata['cactegory_id'] = cid
                    dbdata['uid'] = uid
                    result_id = dbMysql.table('guzi_twitter_category_map').where(f"id = '{id}'").save(dbdata)
                else:
                    # 获取当前日期
                    dbdata['twitter_id'] = twitter_id
                    dbdata['cactegory_id'] = cid
                    dbdata['uid'] = uid
                    dbdata['status'] = 1
                    result_id = dbMysql.table('guzi_twitter_category_map').add(dbdata)
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


@twitter.route('/twitter/add', methods=['GET', 'POST'])
@require_user  # 使用装饰器来验证登录状态
def add():
    uid = g.uid

    if request.method == 'POST':
        username = request.form.get('username')
        remark = request.form.get('remark')
        cid = request.form.get('cid')

        ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
        data_one = dbMysql.table('guzi_twitter').where(
            f"username='{username}' AND uid='{uid}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            id = data_one['id']
            dbdata['updated'] = today_time
            dbdata['remark'] = remark
            twitter_id = dbMysql.table('guzi_twitter').where(f"id = '{id}'").save(dbdata)
        else:
            # 获取当前日期
            dbdata['username'] = username
            dbdata['remark'] = remark
            dbdata['uid'] = uid
            dbdata['cid'] = cid
            dbdata['status'] = 1
            dbdata['created'] = today_time
            twitter_id = dbMysql.table('guzi_twitter').add(dbdata)
            #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句


        if twitter_id:

            ###插入关联表
            ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
            data_one = dbMysql.table('guzi_twitter_category_map').where(
                f"twitter_id='{twitter_id}' AND uid='{uid}' AND cactegory_id='{cid}'").find()
            dbdata = {}
            if data_one:
                id = data_one['id']
                dbdata['twitter_id'] = twitter_id
                dbdata['cactegory_id'] = cid
                dbdata['uid'] = uid
                result_id = dbMysql.table('guzi_twitter_category_map').where(f"id = '{id}'").save(dbdata)
            else:
                # 获取当前日期
                dbdata['twitter_id'] = twitter_id
                dbdata['cactegory_id'] = cid
                dbdata['uid'] = uid
                dbdata['status'] = 1
                result_id = dbMysql.table('guzi_twitter_category_map').add(dbdata)
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




@twitter.route('/twitter/delete', methods=['POST'])
@require_user  # 使用装饰器来验证登录状态
def delete():  # 因为 require_login 会解码 token
    if request.method == 'POST':
        id = request.form.get('id')
        uid = g.uid
        where = f"id='{id}' AND uid='{uid}'"
        result = dbMysql.table('guzi_twitter').where(where).delete()  # 返回删除的行数

        if result:
            where = f"twitter_id='{id}' AND uid='{uid}'"
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



