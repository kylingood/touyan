from quart import Quart, request, jsonify,g, Blueprint
from eth_account.messages import encode_defunct
from eth_account import Account
import jwt
from util.db import *
from src.auth import require_user,require_login,require_user_async
from src.model.discord.get_discord_info import *
from datetime import datetime, timedelta
from src.rapidapi import getDataByUsername
from src.config import DB_MAX_DISCORD,DB_MAX_TWITTER,DB_MAX_DISCORD_CHANNEL
from src.config import ADMIN_LIST_ID

SECRET_KEY = '681f4d8e-d290-800f-a7e5-06bd9291c0d8'

# 存储 nonce 和签名消息
NONCE_STORE = {}
EXPIRE_SECONDS = 300  # 5分钟有效

# 创建一个 Blueprint 用于 Web3 登录功能
web3_auth = Blueprint('web3_auth', __name__)


# 根据Token获取discord相关信息
@web3_auth.route('/api/auth/get_discord')
async def get_discord():
    if request.method == 'GET':
        token = request.args.get("token")
        if not token:
            return jsonify({"error": "Missing token"}), 400
        #token = 'OTkyMzc5NDU1NjY0MzEyMzcy.GFlyQZ.o7wCF4Y3IsqkCqj6DMecKyWSt578e54enOLeng'
        async with AsyncSession() as session:
            discord_info = await get_discord_info(token, session)
            if discord_info:
                # 有值，处理逻辑
                return jsonify({'status': 1, 'data': discord_info})

        return jsonify({'status': 0, 'message': '无效或被封禁的 token'})

# 根据用户名获取推特信息
@web3_auth.route('/api/auth/get_twitter')
async def get_twitter():
    if request.method == 'GET':
        username = request.args.get("username")
        if not username:
            return jsonify({"error": "Missing username"}), 400

        twitter_info = getDataByUsername(username)

        data = {
            "followers": twitter_info['legacy']['friends_count'],
            "fans": twitter_info['legacy']['followers_count'],
            "description": twitter_info['legacy']['description'],
            "avatar": twitter_info['legacy']['profile_image_url_https'],
            "username": username,
            "rest_id": twitter_info['rest_id'],
            "screen_name": twitter_info['legacy']['screen_name'],
            "show_name": twitter_info['legacy']['name']
        }
        if data:
            # 有值，处理逻辑
            return jsonify({'status': 1, 'data': data})

        return jsonify({'status': 0, 'message': '无效或被封禁的 token'})



# 获取签名消息（带时间戳/nonce）
@web3_auth.route('/api/auth/get_channel')
async def get_channel():
    if request.method == 'GET':
        token = request.args.get("token")
        guild_id = request.args.get("guild_id")
        channel_id = request.args.get("channel_id")
        if not token:
            return jsonify({"error": "Missing token"}), 400
        #token = 'OTkyMzc5NDU1NjY0MzEyMzcy.GFlyQZ.o7wCF4Y3IsqkCqj6DMecKyWSt578e54enOLeng'
        async with AsyncSession() as session:
            discord_info = await get_channel_info(token,guild_id,channel_id, session)
            if discord_info:
                # 有值，处理逻辑
                return jsonify({'status': 1, 'data': discord_info})

        return jsonify({'status': 0, 'message': '无效或被封禁的 token'})


async def insert_message_db(item):

    token = item['token']
    guild_id = item['guild_id']
    channel_id = item['channel_id']
    did = item['did']
    async with AsyncSession() as session:
        message_info = await get_discord_message(token, guild_id, channel_id, 5, session)

        for message in message_info:
            mid = message['id']
            content = message['content']

            # print(f"edited_timestamp: {message['edited_timestamp']}, timestamp: {message['timestamp']}")
            dt = datetime.fromisoformat(message['timestamp'])
            timestamp = int(dt.timestamp())

            edited_timestamp = 0
            if message['edited_timestamp']:
                edit_dt = datetime.fromisoformat(message['edited_timestamp'])
                edited_timestamp = int(edit_dt.timestamp())

            ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
            data_one = dbMysql.table('guzi_discord_message').where(
                f"channel_id='{channel_id}' AND mid='{mid}'").find()
            # print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
            # return jsonify({'status': 0, 'message': data_one})
            dbdata = {}
            today_time = int(time.time())
            content_cn = ''
            if data_one and edited_timestamp != data_one.get('edited_timestamp'):
                dbid = data_one['id']
                dbdata['updated'] = today_time
                dbdata['content'] = content
                dbdata['did'] = did
                dbdata['content_cn'] = content_cn
                dbdata['timestamp'] = timestamp
                dbdata['edited_timestamp'] = edited_timestamp
                id = dbMysql.table('guzi_discord_message').where(f"id = '{dbid}'").save(dbdata)
            else:
                # 获取当前日期
                dbdata['mid'] = mid
                dbdata['username'] = item['username']
                dbdata['did'] = did
                dbdata['guild_id'] = item['guild_id']
                dbdata['guild_name'] = item['guild_name']
                dbdata['guild_icon'] = item['guild_icon']
                dbdata['guild_description'] = item['guild_description']
                dbdata['channel_id'] = channel_id
                dbdata['guild_id'] = guild_id
                dbdata['content'] = content
                dbdata['content_cn'] = content_cn
                dbdata['timestamp'] = timestamp
                dbdata['edited_timestamp'] = edited_timestamp
                dbdata['url'] = item['url']
                dbdata['status'] = 1
                dbdata['created'] = today_time
                id = dbMysql.table('guzi_discord_message').add(dbdata)

            # print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    return did


@web3_auth.route('/api/auth/update_message')
@require_user_async
async def update_message():
    uid = g.uid
    data = dbMysql.table('guzi_discord_channel').where(f"uid='{uid}' AND status=1").order("id DESC").limit(50).select()
    # 判断 data 是否为非空列表
    if not data:
        return  jsonify({'status': 0, 'data': [], 'msg': '暂无数据'})

    # 循环打印日志（或处理你想要的字段）
    for item in data:
        #print(f"id: {item['id']}, 用户名: {item['username']}")
        print(print)
        id = await insert_message_db(item)

    if id:
        # 有值，处理逻辑
        return jsonify({'status': 1, 'data': id})
    else:
        return jsonify({'status': 0, 'message': '无效或被封禁的token'})



# 检测邀请码（带时间戳/nonce）
@web3_auth.route('/api/auth/check_invite')
def check_invite():
    code = request.args.get("code")

    if not code:
        return jsonify({"error": "Missing code"}), 400


    # 检查这个邀请码是否已使用
    data_one = dbMysql.table('guzi_invite_codes').where( f"code='{code}'").find()
    if data_one:
        is_used = data_one['is_used']
        if is_used == 1:
            valid = 0
            message = '对不起，邀请码已被使用！'
        else:
            valid = 1
            message = '恭喜，邀请码有效，可注册'

    else:
        valid = 0
        message = '对不起，非法邀请码，不可使用'

    return  jsonify({"message": message,"valid": valid})


# 获取签名消息（带时间戳/nonce）
@web3_auth.route('/api/auth/message')
def get_message():
    address = request.args.get("address").lower()

    if not address:
        return jsonify({"error": "Missing address"}), 400

    # 生成签名消息，带有时间戳
    timestamp = int(time.time())
    message = f"Login request for {address} at {timestamp}"

    # 检查这个地址是否已注册
    data_one = dbMysql.table('guzi_member').where( f"wallet='{address}'").find()
    exists = 1 if data_one else 0


    # 保存消息和时间戳
    NONCE_STORE[address.lower()] = {
        "message": message,
        "timestamp": timestamp
    }

    return  jsonify({"message": message,"exists": exists})


##给新用户初始化数据
def member_data(uid):

    # alldata 现在是一个列表，包含多个字典
    alldata = [
        {'title': 'Discord主号', 'is_type': '2'},
        {'title': '重点项目', 'is_type': '1'},
        {'title': '投研KOL', 'is_type': '1'}
    ]

    ### 处理推特和DC的默认分组
    dbdata = {}
    today_time = int(time.time())
    category_id = 0
    for item in alldata:
        # 获取当前日期
        dbdata['title'] = item['title']
        dbdata['remark'] = item['title']
        dbdata['is_type'] = item['is_type']
        dbdata['uid'] = uid
        dbdata['status'] = 1
        dbdata['created'] = today_time
        category_id = dbMysql.table('guzi_category').add(dbdata)
        print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

    ### 处理默认关注的人默认分组
    # 获取当前日期
    dbmapdata = {}
    twitter_id = 44196397
    dbmapdata['twitter_id'] = twitter_id
    dbmapdata['uid'] = uid
    dbmapdata['category_id'] = category_id
    dbmapdata['created'] = today_time
    dbmapdata['status'] = 1
    result_id = dbMysql.table('guzi_member_twitter_map ').add(dbmapdata)
    print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

# 验证签名并生成 JWT
@web3_auth.route('/api/auth/verify', methods=['POST'])
async def verify():
    data = await request.json
    address = data.get('address', '').lower()
    message = data.get('message')
    signature = data.get('signature')
    inviteCode = data.get('inviteCode')

    if inviteCode:
        # 检查这个邀请码是否已使用
        data_code_one = dbMysql.table('guzi_invite_codes').where( f"code='{inviteCode}'").find()
        if data_code_one:
            is_used = data_code_one['is_used']
            if is_used == 1:
                return jsonify({"error": "对不起，邀请码已被使用！"}), 400
        else:
            return jsonify({"error": "对不起，非法邀请码，不可使用"}), 400



    entry = NONCE_STORE.get(address)
    if not entry or entry['message'] != message:
        return jsonify({"error": "消息不匹配"}), 400

    if int(time.time()) - entry['timestamp'] > EXPIRE_SECONDS:
        return jsonify({"error": "签名已过期"}), 400

    try:
        # 验证签名
        encoded = encode_defunct(text=message)
        recovered = Account.recover_message(encoded, signature=signature)

        if recovered.lower() == address:


            # 把账号写入数据库
            ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
            data_one = dbMysql.table('guzi_member').where(f"wallet='{address}'").find()
            dbdata = {}
            today_time = int(time.time())

            if data_one:
                uid = data_one['uid']
                username = data_one['username']
                max_twitter = data_one['max_twitter']
                max_discord = data_one['max_discord']
                max_discord_channel = data_one['max_discord_channel']
                dbdata['updated'] = today_time
                result_db = dbMysql.table('guzi_member').where(f"uid = '{uid}'").save(dbdata)
                print(result_db)
            else:
                max_twitter = DB_MAX_TWITTER
                max_discord = DB_MAX_DISCORD
                max_discord_channel = DB_MAX_DISCORD_CHANNEL
                if inviteCode:
                    # 获取当前日期
                    username = address[:6] + '**' + address[-4:]
                    dbdata['wallet'] = address
                    dbdata['username'] = username
                    dbdata['code'] = inviteCode
                    dbdata['status'] = 1
                    dbdata['created'] = today_time
                    dbdata['max_twitter'] = max_twitter
                    dbdata['max_discord'] =  max_discord
                    dbdata['max_discord_channel'] =  max_discord_channel
                    uid = dbMysql.table('guzi_member').add(dbdata)

                    if uid:
                        ### 处理邀请码逻辑
                        id = data_code_one['id']
                        dbcodedata = {}
                        dbcodedata['is_used'] = 1
                        dbcodedata['uid'] = uid
                        dbcodedata['use_time'] = today_time
                        dbMysql.table('guzi_invite_codes').where(f"id='{id}'").save(dbcodedata)

                        #### 给新用户初始化数据
                        member_data(uid)


                else:
                    return jsonify({"error": "无效邀请码，新用户不能注册"}), 400
                #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

            # 登录成功，生成 JWT Token
            payload = {
                'address': address,
                'uid':uid,
                'username':username,
                'max_twitter': max_twitter,
                'max_discord': max_discord,
                'max_discord_channel': max_discord_channel,
                'exp': datetime.utcnow() + timedelta(days=30) # 设置过期时间
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

            # 将 Token 返回给前端
            return jsonify({"token": token})
        else:
            return jsonify({"error": "签名验证失败"}), 400
    except Exception as e:
        return jsonify({"error": f"验证出错: {str(e)}"}), 500




# 保护路由，验证 JWT Token
@web3_auth.route('/api/protected', methods=['GET'])
@require_user
def protected():
    uid = g.uid
    address = g.address
    username = g.username

    if not address:
        return jsonify({"error": "protected 未登录或Token无效"}), 403

    return jsonify({"username":username,"message": f"欢迎 {address} 登录成功！"})


@web3_auth.route('/api/get_user_info', methods=['GET'])
@require_user_async
def get_user_info():
    uid = g.uid

    if uid not in ADMIN_LIST_ID:
        return jsonify({"status":0,"message": f"对不起，你非管理员！"})


    return jsonify({"status":1,"message": f"欢迎管理员登录成功！"})


@web3_auth.route('/api/get_total_info', methods=['GET'])
@require_user_async
def get_total_info():
    uid = g.uid
    sql = f'''
        SELECT COUNT(*) AS twitter_count
        FROM guzi_member_twitter_map
        WHERE uid = '{uid}' AND status = 1;
    '''
    twitter_data = dbMysql.query(sql)
    print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    print(twitter_data)
    twitter_count = twitter_data[0].get('twitter_count', 0)

    sql = f'''
            SELECT COUNT(*) AS discord_count
            FROM guzi_discord_category_map
            WHERE uid = '{uid}' AND status = 1;
        '''
    discord_data = dbMysql.query(sql)
    print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    print(discord_data)
    discord_count = discord_data[0].get('discord_count', 0)
    sql = f'''
           SELECT is_type, COUNT(*) AS group_count
            FROM guzi_category
            WHERE uid = '{uid}' AND status = 1
            GROUP BY is_type;
        '''
    category_data = dbMysql.query(sql)
    print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
    print(category_data)

    twitter_category_count = next((item['group_count'] for item in category_data if item['is_type'] == 1), 0)
    discord_category_count = next((item['group_count'] for item in category_data if item['is_type'] == 2), 0)

    show_data = {'twitter_count': twitter_count, 'discord_count': discord_count, 'twitter_category_count': twitter_category_count, 'discord_category_count': discord_category_count}

    return jsonify({"status":1,"data": show_data})
