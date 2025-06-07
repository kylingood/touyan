# -*- coding: utf-8 -*-
from quart import Quart, render_template, request, jsonify,g, Blueprint
from util.db import *
from src.auth import require_user,require_user_async,check_user_login_do

# 创建一个 Blueprint 用于 Web3 登录功能
category = Blueprint('category', __name__)


@category.route('/category/twitter', methods=['GET'])
async def twitter():
    return await render_template("category/twitter.html")


@category.route('/category/discord', methods=['GET'])
async def discord():
    return await render_template("category/discord.html")


@category.route('/category/list_data', methods=['GET', 'POST'])
@require_user_async
def list_data():
    uid = g.uid
    is_type = request.args.get('is_type', default=1, type=int)
    data = dbMysql.table('guzi_category').where(f"uid='{uid}'  AND is_type='{is_type}' AND status=1").field('id,title').select()
    #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    return jsonify({'status': 1, 'data': data})

@category.route("/category/page_discord", methods=['GET', 'POST'])
@require_user  # 使用装饰器来验证登录状态
def page_discord():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        is_type = request.args.get('is_type', default=1, type=int)
        keyword = request.args.get('keyword')


        where_clauses = [f"c.uid='{uid}' AND c.is_type='{is_type}' AND c.status=1"]

        if keyword:
            where_clauses.append(
                f"( c.title LIKE '%{keyword}%' OR c.remark LIKE '%{keyword}%'  OR c.id LIKE '%{keyword}%' )")

        where = ' AND '.join(where_clauses)

        order = "c.id DESC"

        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1
        sql = f'''
            SELECT 
                c.*,
                c.id AS category_id,
                c.title AS category_title,
                COUNT(m.discord_id) AS twitter_count
            FROM 
                guzi_category AS c
            LEFT JOIN 
                guzi_discord_category_map AS m
            ON 
                c.id = m.category_id
            WHERE 
                 {where}
            GROUP BY 
                c.id
            ORDER BY 
                 twitter_count  DESC;
        '''
        data_list = dbMysql.query(sql)
        print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        #data_list = dbMysql.table('guzi_category').where(where).order(order).page(page, limit).select()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        total_sql = f"SELECT COUNT(*) AS total FROM guzi_category AS c   WHERE  {where}  "
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
                        "title": item["title"],
                        "total": item["twitter_count"],
                        "created": item["created"],
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


@category.route("/category/page", methods=['GET', 'POST'])
@require_user  # 使用装饰器来验证登录状态
def page():
    uid = g.uid
    if request.method == 'GET':

        # 获取参数并设置默认值（如未传则为1或10）
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        is_type = request.args.get('is_type', default=1, type=int)
        keyword = request.args.get('keyword')

        where_clauses = [f"c.uid='{uid}' AND c.is_type='{is_type}' AND c.status=1"]

        if keyword:
            where_clauses.append(f"( c.title LIKE '%{keyword}%' OR c.remark LIKE '%{keyword}%'  OR c.id LIKE '%{keyword}%' )")

        where = ' AND '.join(where_clauses)

        order = "c.id DESC"

        # 然后再计算偏移量
        start_index = (page - 1) * limit + 1
        sql = f'''
            SELECT 
                c.*,
                c.id AS category_id,
                c.title AS category_title,
                COUNT(m.twitter_id) AS twitter_count
            FROM 
                guzi_category AS c
            LEFT JOIN 
                guzi_member_twitter_map AS m
            ON 
                c.id = m.category_id
            WHERE 
                {where}
            GROUP BY 
                c.id
            ORDER BY 
                 twitter_count  DESC;
        '''
        data_list = dbMysql.query(sql)
        print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        #data_list = dbMysql.table('guzi_category').where(where).order(order).page(page, limit).select()
        #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
        #total =  dbMysql.table('guzi_category').where(where).count()

        total_sql = f"SELECT COUNT(*) AS total FROM guzi_category AS c   WHERE  {where}  "
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
                        "title": item["title"],
                        "total": item["twitter_count"],
                        "created": item["created"],
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



@category.route('/category/del_cate', methods=['POST'])
@require_user_async  # 使用装饰器来验证登录状态
@check_user_login_do
async def del_cate():  # 因为 require_login 会解码 token
    if request.method == 'POST':
        uid = g.uid
        form = await request.form  # 注意必须 await
        id = form.get('id')
        data = await request.get_json()  # ✅ 这里必须加 await

        if id:
            where = f"id='{id}' AND uid='{uid}'"
            result = dbMysql.table('guzi_category').where(where).delete()  # 返回删除的行数

            if result:
                # where = f"category_id='{id}' AND uid='{uid}'"
                # result = dbMysql.table('guzi_twitter_category_map').where(where).delete()  # 返回删除的行数
                return jsonify({
                    'status': 1,
                    'message': '恭喜您，数据删除成功！'
                })

        if data:
            twitter_ids = data.get('ids', [])
            if not isinstance(twitter_ids, list):
                return jsonify({'status': 0, 'message': '参数错误，ids 应该是一个列表'})

            print('将要删除的 Twitter ID 列表：', twitter_ids)
            # 构造 SQL 条件
            id_conditions = " OR ".join([f"id='{tid}'" for tid in twitter_ids])
            where = f"({id_conditions}) AND uid='{uid}'"
            ###删除分类关联数据
            result = dbMysql.table('guzi_category').where(where).delete()  # 返回删除的行数
            print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

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

@category.route('/category/add', methods=['POST'])
@require_user_async
@check_user_login_do
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
        data_one = dbMysql.table('guzi_category').where(
            f"title='{title}' AND uid='{uid}' AND is_type='{is_type}'").find()
        print(dbMysql.getLastSql())
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            id = data_one['id']
            dbdata['updated'] = today_time
            dbdata['remark'] = remark
            dbdata['title'] = title
            result_db = dbMysql.table('guzi_category').where(f"id = '{id}'").save(dbdata)
            print(dbMysql.getLastSql())
        else:
            # 获取当前日期
            dbdata['title'] = title
            dbdata['remark'] = remark
            dbdata['is_type'] = is_type
            dbdata['uid'] = uid
            dbdata['status'] = 1
            dbdata['created'] = today_time
            result_db = dbMysql.table('guzi_category').add(dbdata)
            print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

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
@require_user_async
@check_user_login_do
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
        data_one = dbMysql.table('guzi_category').where(
            f"id='{id}' AND uid='{uid}'").find()
        dbdata = {}
        today_time = int(time.time())

        if data_one:
            uid = data_one['uid']
            dbdata['updated'] = today_time
            dbdata['remark'] = remark
            dbdata['title'] = title
            result_db = dbMysql.table('guzi_category').where(f"id='{id}' AND uid='{uid}'").save(dbdata)

            if result_db:
                return jsonify({
                    'status': 1,
                    'message': '恭喜您，数据修改成功！'
                })

        return jsonify({
            'status': 0,
            'message': '对不起，数据修改失败！'
        })