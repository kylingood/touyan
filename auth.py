from quart import Quart, request, jsonify, g, Blueprint
from eth_account.messages import encode_defunct
from eth_account import Account
from functools import wraps
import time
import jwt
import datetime
from util.db import *
import asyncio


# 如果你已经在其他地方创建了 Flask 应用实例，就不要再重复创建
# app = Flask(__name__)  # 已存在，不要重复创建

SECRET_KEY = '681f4d8e-d290-800f-a7e5-06bd9291c0d8'

# 存储 nonce 和签名消息
NONCE_STORE = {}
EXPIRE_SECONDS = 300  # 5分钟有效


# 提取 token 并验证
def get_logged_in_address():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    try:
        token = auth_header.split()[1]  # 去掉 Bearer 前缀
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        # 设置为全局可访问
        g.address = decoded.get('address')
        g.username = decoded.get('username')
        g.uid = decoded.get('uid')

        return decoded['address']  # 返回地址
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, IndexError):
        return None


# 提取 token 并验证
def extract_user_from_token():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return False  # 未提供 Authorization 头

    try:
        token = auth_header.split()[1]  # 去掉 Bearer 前缀
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        # 设置为全局可访问
        g.address = decoded.get('address')
        g.username = decoded.get('username')
        g.uid = decoded.get('uid')
        return True
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, IndexError):
        return False


# 通用装饰器
def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        address = get_logged_in_address()

        if not address:
            return jsonify({'error': 'login 未登录或Token无效'}), 401
        return f(address, *args, **kwargs)
    return wrapper


# 装饰器：获取地址和uid
def require_user(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not extract_user_from_token():
            return  jsonify({'error': 'auth 未登录或Token无效'}), 401
        return f(*args, **kwargs)
    return wrapper

# def require_user_async(f):
#     @wraps(f)
#     async def wrapper(*args, **kwargs):  # wrapper也要是async
#         if not extract_user_from_token():
#             return jsonify({'error': 'async 未登录或Token无效'}), 401
#         return await f(*args, **kwargs)  # 一定要 await f(...)
#     return wrapper



def require_user_async(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        if not extract_user_from_token():
            return jsonify({'error': 'async 未登录或Token无效'}), 401

        result = f(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    return wrapper


### 检测账号是不是管理员
def require_admin(uid_whitelist=None):
    if uid_whitelist is None:
        uid_whitelist = [10000]  # 默认只有 10001 是管理员

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if getattr(g, 'uid', None) not in uid_whitelist:
                return jsonify({'status': 0, 'message': '对不起，此账号没有权限！@_@'})
            return await func(*args, **kwargs)
        return wrapper
    return decorator