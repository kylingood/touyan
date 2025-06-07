# -*- coding: utf-8 -*-
from quart import Quart, request, jsonify, g, Blueprint,redirect
from eth_account.messages import encode_defunct
from eth_account import Account
from functools import wraps
import time
import jwt
import datetime
from util.db import *
import asyncio
from src.config import ADMIN_LIST_ID,LOGIN_EXPIRE_SECONDS,SECRET_KEY,DEFAULT_UID

# 如果你已经在其他地方创建了 Flask 应用实例，就不要再重复创建
# app = Flask(__name__)  # 已存在，不要重复创建


# 存储 nonce 和签名消息
NONCE_STORE = {}
EXPIRE_SECONDS = LOGIN_EXPIRE_SECONDS  # 5分钟有效


# 提取 token 并验证
def get_logged_in_address():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    try:
        token = auth_header.split()[1]  # 去掉 Bearer 前缀
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        # 设置为全局可访问
        for key in ["address", "username", "uid", "max_twitter", "max_discord", "max_discord_channel"]:
            setattr(g, key, decoded.get(key))
        g.login_uid = decoded.get('uid')
        return decoded['address']  # 返回地址
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, IndexError):
        return None


# 提取 token 并验证
def extract_user_from_token():
    auth_header = request.headers.get('Authorization')

    # 未提供 Authorization 头
    if not auth_header:
        g.uid = DEFAULT_UID ###只要出错就提供默认账号，让游客能查看登陆
        return True

    try:
        token = auth_header.split()[1]  # 去掉 Bearer 前缀
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        # 设置为全局可访问
        for key in ["address", "username", "uid", "max_twitter", "max_discord", "max_discord_channel"]:
            setattr(g, key, decoded.get(key))
        g.login_uid = decoded.get('uid')
        return True
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, IndexError):
        g.uid = DEFAULT_UID ###只要出错就提供默认账号，让游客能查看登陆
        return True


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

### 检测用户是否可以操作
def check_user_login_do(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        ### 处理默认数据
        if getattr(g, 'login_uid', 0) != getattr(g, 'uid', DEFAULT_UID):
            return jsonify({
                'status': 0,
                'not_login': 1,
                'message': f'操作失败，账号未登录状态！'
            }), 200

        result = f(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    return wrapper

### 检测用户Token是否有效
def require_user_async(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):

        if not extract_user_from_token():
            return jsonify({
                'status': 0,
                'message': '账号未登录或Token无效'
            }), 200

        result = f(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    return wrapper


### 检测账号是不是管理员
def require_admin(uid_whitelist=None):
    if uid_whitelist is None:
        uid_whitelist = ADMIN_LIST_ID  # 默认只有 10000 是管理员

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if getattr(g, 'uid', None) not in uid_whitelist:
                return jsonify({'status': 0, 'message': '对不起，此账号没有管理权限！@_@'})
                #return redirect('/error')
            return await func(*args, **kwargs)
        return wrapper
    return decorator