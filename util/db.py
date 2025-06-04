# -*- coding: utf-8 -*-
import os
import sys
import time
from datetime import datetime
import urllib3
import warnings
from cryptography.fernet import Fernet
# 调整路径到包含 pythonMySQL 的目录
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# 现在您可以从 pythonMySQL 导入
from pythonMySQL.pythonMySQL import *
from loguru import logger

urllib3.disable_warnings()
warnings.filterwarnings("ignore", category=UserWarning, message="The log with transaction hash*")

##取到0点0分的时间戳
#today_time = int(time.mktime(datetime.date.today().timetuple()))


###  实例化mysql数据库
dbMysql = M('guzi_config')
#logger = create_logger()


### 取到相关配置文件
def get_db_config_data(field=None):

    try:
        #Config = M('guzi_config')
        data_list = dbMysql.table('guzi_config').select()
        if field:
            data = next((item[field] for item in data_list if field in item), None)
            return data

        return data_list

    except Exception as e:
        logger.error(e)
        # 打印异常堆栈信息
        logger.exception(e)


# data = get_db_config_data('okx_apikey')
# print(data)


### 取到所有钱包数据
def get_db_wallet_data(where="is_test=1",order="id ASC",limit=10000,address=None):

    try:
        #Wallet = M('guzi_wallet')
        if address:
            data_list = dbMysql.table('guzi_wallet').where(f"address='{address}'").select()
        else:
            data_list = dbMysql.table('guzi_wallet').where(where).order(order).limit(limit).select()

        return data_list

    except Exception as e:
        logger.error(e)
        # 打印异常堆栈信息
        logger.exception(e)



#取测试钱包数据
def get_db_test_wallet_data(address=None):
    try:

        if address:
            data_list = dbMysql.table('guzi_wallet').where(f"address='{address}'").find()
        else:
            data_list = dbMysql.table('guzi_wallet').where(f'is_test=2').select()

        return data_list

    except Exception as e:
        logger.error(e)
        # 打印异常堆栈信息
        logger.exception(e)



### 取到所有钱包数据
def get_db_server_data(ip=None):

    try:
        #Wallet = M('guzi_server')

        if ip:
            data_list = dbMysql.table('guzi_server').where(f"ip='{ip}'").find()
        else:
            data_list = dbMysql.table('guzi_server').select()

        return data_list

    except Exception as e:
        logger.error(e)
        # 打印异常堆栈信息
        logger.exception(e)



def get_db_project_data(where = 1):

    try:

        if where:
            data_list = dbMysql.table('guzi_project').where(where).select()
        else:
            data_list = {}

        return data_list

    except Exception as e:
        logger.error(e)
        # 打印异常堆栈信息
        logger.exception(e)



def get_filter_wallet_data(where = 1,filter = 'address'):
    try:

        # 取到已执行完任务的数据
        project_datas =  get_db_project_data(where)
        #print(project_datas)

        # 取到钱包相关的数据
        all_wallet = get_db_wallet_data()

        # 获取 project_datas 中所有的 username
        existing_usernames = set(item[filter] for item in project_datas)

        # 使用列表推导过滤 wallet_datas 中已存在的数据
        wallet_datas = [item for item in all_wallet if item[filter] not in existing_usernames]

        return wallet_datas

    except Exception as e:
        logger.error(e)
        # 打印异常堆栈信息
        logger.exception(e)


### 取到所有钱包数据
def get_db_project_name_data(pid=None):

    try:

        if pid:
            data_list = dbMysql.table('guzi_task').where(f"id='{pid}'").find()
        else:
            data_list = dbMysql.table('guzi_task').select()

        return data_list

    except Exception as e:
        logger.error(e)
        # 打印异常堆栈信息
        logger.exception(e)


### 取到所有钱包数据
def get_data_by_table_name(table_name='guzi_wallet',where=''):

    try:

        if where:
            data_list = dbMysql.table(table_name).where(where).select()
        else:
            data_list = dbMysql.table(table_name).select()

        return data_list

    except Exception as e:
        logger.error(e)
        # 打印异常堆栈信息
        logger.exception(e)



# 生成随机密钥
def guzi_generate_key():
    return Fernet.generate_key()



# 加密数据
def guzi_encrypt_data(data):
    try:
        key_content = get_db_config_data('private_key')

        if key_content:
            myobj = Fernet(key_content)
            encrypted_data = myobj.encrypt(data.encode())
            decrypted_string = encrypted_data.decode('utf-8')
            #print(decrypted_string)

            return decrypted_string
        else:
            logger.info(f"关键字串为空")
            return False
    except Exception as e:
        logger.error(e)
        # 打印异常堆栈信息
        logger.exception(e)
        return False


# 解密数据
def guzi_decrypted_data(encrypted_data):

    try:
        key_content = get_db_config_data('private_key')
        if not key_content:
            logger.info("关键字串为空")
            return False

        try:
            # 确保 key_content 是 bytes 类型
            if isinstance(key_content, str):
                key_content = key_content.encode('utf-8')
            # 初始化 Fernet 对象
            myobj = Fernet(key_content)
            # 检查并转换 encrypted_data
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode('utf-8')
            decrypted_data = myobj.decrypt(encrypted_data).decode()
            return decrypted_data
        except Exception as e:
            logger.error(f"解密失败: {e}")
            return False
    except Exception as e:
        logger.error(e)
        # 打印异常堆栈信息
        logger.exception(e)
        return False


# 加密数据
def guzi_encrypt_data_old(data):

    file_path = 'E:/key/words.txt'
    try:
        with open(file_path, 'r') as file:
            key_content = file.read()
            if key_content:
                myobj = Fernet(key_content)
                encrypted_data = myobj.encrypt(data.encode())
                return encrypted_data
            else:
                print("关键字串为空。")
                return False
    except FileNotFoundError:
        print("文件未找到或路径错误。")
        return False
    except IOError:
        print("读取文件时发生了错误。")
        return False


# 解密数据
def guzi_decrypted_data_old(encrypted_data):

    file_path = 'E:/key/words.txt'
    try:
        with open(file_path, 'r') as file:
            key_content = file.read()
            if key_content:
                myobj = Fernet(key_content)
                decrypted_data = myobj.decrypt(encrypted_data).decode()
                return decrypted_data
            else:
                print("关键字串为空。")
                return False
    except FileNotFoundError:
        print("文件未找到或路径错误。")
        return False
    except IOError:
        print("读取文件时发生了错误。")
        return False


