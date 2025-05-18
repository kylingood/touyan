from quart import Quart, request, jsonify,g, Blueprint
from eth_account.messages import encode_defunct
from eth_account import Account
from functools import wraps
import time
import jwt
from util.db import *
from auth import require_user,require_login,require_user_async
from curl_cffi.requests import AsyncSession
import asyncio
from src.model.discord.get_discord_info import *
from datetime import datetime
from googletrans import Translator

SECRET_KEY = '681f4d8e-d290-800f-a7e5-06bd9291c0d8'

# 存储 nonce 和签名消息
NONCE_STORE = {}
EXPIRE_SECONDS = 300  # 5分钟有效

# 创建一个 Blueprint 用于 Web3 登录功能
web3_auth = Blueprint('web3_auth', __name__)


# 获取签名消息（带时间戳/nonce）
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




def translate_en_to_zh(text_en: str) -> str:
    translator = Translator()
    result = translator.translate(text_en, src='en', dest='zh-cn')
    return result.text


@web3_auth.route('/api/auth/update_message')
@require_user_async
async def update_message():
    uid = g.uid
    data = dbMysql.table('guzi_discord_channel').where(f"uid='{uid}' AND status=1").select()
    # 判断 data 是否为非空列表
    if not data:
        return  jsonify({'status': 0, 'data': [], 'msg': '暂无数据'})

    # 循环打印日志（或处理你想要的字段）
    for item in data:
        print(f"id: {item['id']}, 用户名: {item['username']}")
        token = item['token']
        guild_id = item['guild_id']
        channel_id = item['channel_id']
        async with AsyncSession() as session:
            message_info = await get_discord_message(token, guild_id, channel_id, 5,session)

            for message in message_info:
                mid = message['id']
                content = message['content']

                print(f"edited_timestamp: {message['edited_timestamp']}, timestamp: {message['timestamp']}")
                dt = datetime.fromisoformat(message['timestamp'])
                timestamp = int(dt.timestamp())

                edited_timestamp = 0
                if message['edited_timestamp']:
                    edit_dt = datetime.fromisoformat(message['edited_timestamp'])
                    edited_timestamp = int(edit_dt.timestamp())

                ## 先查看此钱包有没有数据，没有就插入，有就更新数据状态
                data_one = dbMysql.table('guzi_discord_message').where(
                    f"channel_id='{channel_id}' AND mid='{mid}'").find()
                #print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句
                #return jsonify({'status': 0, 'message': data_one})
                dbdata = {}
                today_time = int(time.time())
                content_cn = translate_en_to_zh(content)
                if data_one and edited_timestamp != data_one.get('edited_timestamp'):
                    id = data_one['id']
                    dbdata['updated'] = today_time
                    dbdata['content'] = content
                    dbdata['content_cn'] = content_cn
                    dbdata['timestamp'] = timestamp
                    dbdata['edited_timestamp'] = edited_timestamp
                    id = dbMysql.table('guzi_discord_message').where(f"id = '{id}'").save(dbdata)
                else:
                    # 获取当前日期
                    dbdata['mid'] = mid
                    dbdata['username'] = item['username']
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


    if id:
        # 有值，处理逻辑
        return jsonify({'status': 1, 'data': id})
    else:
        return jsonify({'status': 0, 'message': '无效或被封禁的token'})


# 获取签名消息（带时间戳/nonce）
@web3_auth.route('/api/auth/message')
def get_message():
    address = request.args.get("address")
    if not address:
        return jsonify({"error": "Missing address"}), 400

    # 生成签名消息，带有时间戳
    timestamp = int(time.time())
    message = f"Login request for {address} at {timestamp}"

    # 保存消息和时间戳
    NONCE_STORE[address.lower()] = {
        "message": message,
        "timestamp": timestamp
    }

    return  jsonify({"message": message})

# 验证签名并生成 JWT
@web3_auth.route('/api/auth/verify', methods=['POST'])
async def verify():
    data = await request.json
    address = data.get('address', '').lower()
    message = data.get('message')
    signature = data.get('signature')

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
            data_one = dbMysql.table('guzi_member').where(
                f"wallet='{address}'").find()
            dbdata = {}
            today_time = int(time.time())

            if data_one:
                uid = data_one['uid']
                dbdata['updated'] = today_time
                result_db = dbMysql.table('guzi_member').where(f"uid = '{uid}'").save(dbdata)
                print(result_db)
            else:
                # 获取当前日期
                username = address[:6] + '**' + address[-4:]
                dbdata['wallet'] = address
                dbdata['username'] = username
                dbdata['status'] = 1
                dbdata['created'] = today_time
                uid = dbMysql.table('guzi_member').add(dbdata)
                print(dbMysql.getLastSql())  # 打印由Model类拼接填充生成的SQL语句

            # 登录成功，生成 JWT Token
            payload = {
                'address': address,
                'uid':uid,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)  # 设置过期时间
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

    if not address:
        return jsonify({"error": "未登录或Token无效"}), 403

    return jsonify({"message": f"欢迎 {address} 登录成功！"})



