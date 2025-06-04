# -*- coding: utf-8 -*-
import os
import sys
import random
import pandas as pd
import logging
import multiprocessing
from web3 import Web3
import json
import string
import time
import datetime
import urllib3
import warnings
import requests
import paramiko
from cryptography.fernet import Fernet
from util.Logger import create_logger
from itertools import islice
# 调整路径到包含 pythonMySQL 的目录
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# 现在您可以从 pythonMySQL 导入

from loguru import logger

urllib3.disable_warnings()
warnings.filterwarnings("ignore", category=UserWarning, message="The log with transaction hash*")

##取到0点0分的时间戳
today_time = int(time.mktime(datetime.date.today().timetuple()))


# 获取csv文件中的数据,返回所有数据
def get_csv_data(csv_file):
    data = pd.read_csv(csv_file, encoding='UTF-8', na_values=[''])
    data.fillna('', inplace=True)
    return data.to_dict(orient='records')


def read_content_from_file(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            if content:  # 如果内容非空
                num = int(content)
            else:  # 如果内容为空
                num = 0
    except FileNotFoundError:
        num = 0
    except ValueError:
        num = 0
    return num

##随机读取文件的一行数据
def get_random_line(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        if not lines:  # 检查文件是否为空
            return ''  # 如果文件为空，返回空值（None）
        random_line = random.choice(lines).strip()
        return random_line

##随机读取文件的一行数据
def get_random_line_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        random_line = random.choice(lines).strip()
        return random_line

# 从文件读取指定行的数据，再提交任务到线程池
def read_wallets_from_file(file_path, start_line, batch_size):
    wallets = []
    with open(file_path, 'r') as f:
        # 跳过指定行数
        for _ in range(start_line):
            try:
                next(f)
            except StopIteration:
                # 如果文件中没有足够的行数，则返回空列表
                return wallets

        # 逐行读取后面的数据，直到达到指定的批量大小或者文件结束
        for line in islice(f, batch_size):
            wallets.append(line.strip())
    return wallets

### 删除一行数据
def delete_line_in_file(file_path, target_content):
    """
    在文本文件中查找包含特定内容的行并删除它。

    :param file_path: 文本文件路径
    :param target_content: 要查找并删除的内容
    """
    # 读取文件中的所有行
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 过滤掉包含目标内容的行
    with open(file_path, 'w', encoding='utf-8') as file:
        for line in lines:
            if target_content not in line:
                file.write(line)

# 使用示例：
# start_line = 5  # 从第 5 行开始读取
# batch_size = 10  # 读取 10 行数据
# wallets_generator = read_wallets_from_file('../data/wallet.txt', 59, 2)
# print(wallets_generator[0])
# exit()

def find_line_with_content(file_path, content):
    # 用于存储匹配内容的行号
    line_numbers = []

    # 逐行读取文件内容
    with open(file_path, 'r') as file:
        lines = file.readlines()

        # 在每一行中查找匹配的内容
        for line_number, line in enumerate(lines, start=1):
            if content in line:
                line_numbers.append(line_number)

    return line_numbers


def find_lines_get_content(file_path, content,is_lower=0):
    # 用于存储匹配内容的行
    matching_lines = []

    ##不区分大小写内容
    if is_lower==1:
        # 逐行读取文件内容,
        with open(file_path, 'r') as file:
            lines = file.readlines()
            # 将 content 转换为小写（或大写）
            content_lower = content.lower()

            # 在每一行中查找匹配的内容
            for line in lines:
                # 将每一行转换为小写后进行比较
                if content_lower in line.lower():
                    matching_lines.append(line.strip())
    else:
        # 逐行读取文件内容,这里区分
        with open(file_path, 'r') as file:
            lines = file.readlines()
            # 在每一行中查找匹配的内容
            for line in lines:
                if content in line:
                    matching_lines.append(line.strip())

    return matching_lines

def update_column_csv(server_filepath,address,up_datas=[]):
    if not os.path.isfile(server_filepath):
        # 如果文件不存在，创建一个空的 DataFrame
        df = pd.DataFrame(columns=['address'] + [up_data["column_name"] for up_data in up_datas])
    else:
        # 否则，尝试读取现有的 CSV 文件
        df = pd.read_csv(server_filepath)

        # 如果 'address' 不在 DataFrame 中，增加一行数据
    if address not in df['address'].values:
        new_row = {'address': address}
        df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)

        # 创建缺失的列
    for up_data in up_datas:
        column_name = up_data["column_name"]
        if column_name not in df.columns:
            df[column_name] = None

        # 更新数据
    for up_data in up_datas:
        df.loc[df['address'] == address, up_data["column_name"]] = up_data["value"]

        # 将 DataFrame 写回 CSV 文件
    df.to_csv(server_filepath, index=False)
    logger.info(
        f'address: {address}, 写入数据至 {server_filepath} 完成')



##连接SSH 并执行命令
def execute_remote_command(hostname, command):
    # 创建SSH客户端对象
    client = paramiko.SSHClient()

    # 自动添加远程服务器的主机密钥（请谨慎使用）
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())




    try:
        if hostname=='192.168.60.2':
            username = 'guzi'
            port = '22'
            password = 'Guzi@123'
        else:
            # 取到服务器相关信息
            server_data = get_db_server_data(hostname)
            username = server_data["username"].strip()
            port = server_data["port"].strip()
            password = guzi_decrypted_data(server_data["password"].strip())


        # print(f"server_data:{server_data}")
        # print(f"username:{username}")
        # print(f"hostname:{hostname}")
        # print(f"port:{port}")
        # print(f"password:{password}")

        # 连接远程服务器
        client.connect(hostname=hostname, port=port, username=username, password=password)

        # 执行命令
        stdin, stdout, stderr = client.exec_command(command)

        # 获取命令执行结果
        output = stdout.read().decode()

        # 关闭连接
        client.close()

        return output
    except paramiko.AuthenticationException as e:
        logger.info("Authentication failed: %s" % str(e))
    except paramiko.SSHException as e:
        logger.info("SSH connection failed: %s" % str(e))
    except paramiko.BadHostKeyException as e:
        logger.info("Host key could not be verified: %s" % str(e))
    except Exception as e:
        logger.info("Error occurred: %s" % str(e))




##连接SSH 执行需要确认的命令
def execute_ssh_command_with_confirmation(hostname, command, confirmation_input):
    try:
        # SSH 连接配置
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 取到服务器相关信息
        server_data = get_db_server_data(hostname)

        username = server_data["username"].strip()
        port = server_data["port"].strip()
        password = guzi_decrypted_data(server_data["password"].strip())


        # 建立 SSH 连接
        ssh.connect(hostname, port=port, username=username, password=password)

        # 执行命令并处理确认提示
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        stdin.write(confirmation_input + "\n")
        stdin.flush()

        # 输出命令执行结果
        print(stdout.read().decode())

        # 关闭 SSH 连接
        ssh.close()

    except paramiko.AuthenticationException as auth_error:
        print("Authentication failed: ", str(auth_error))
    except paramiko.SSHException as ssh_error:
        print("SSH error: ", str(ssh_error))
    except Exception as e:
        print("Error: ", str(e))



#取到当前币种兑换价格
def crypto_to_usd(asset = 'ETH'):
    toDo = 0
    while toDo < 3:
        try:
            url = f'https://min-api.cryptocompare.com/data/price?fsym={asset}&tsyms=USDT'
            response = requests.get(url)
            result = [response.json()]
            price = result[0]['USDT']
            return float(price)
        except:
            time.sleep(5)
            toDo = toDo + 1
    # print("\033[31m{}".format('Core -> Instruments -> Balance -> crypto_to_usd(asset) ERROR'))
    # print("\033[0m{}".format(' '))
    # return 'ERROR'
    raise Exception('Getiing Market Data Error')

## 从文件中随机读取一行内容
def get_random_line_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if not lines:
                return ''
            return random.choice(lines).strip()
    except FileNotFoundError:
        return ''
    except ValueError as ve:
        return ''
    except Exception as e:
        return ''



def generate_invite_codes(count=10, length=20):
    chars = string.ascii_letters + string.digits  # 包含 a-zA-Z0-9
    return [''.join(random.choices(chars, k=length)) for _ in range(count)]


def get_countdown(sleep_time):
    while sleep_time > 0:
        logger.info(f"开始倒计时中，还剩: {sleep_time} 秒....")
        time.sleep(1)  # 每秒钟暂停一次
        sleep_time -= 1

#测算当前gas
def usd_to_zk_gas(usd=0.3):
    eth_price = crypto_to_usd('ETH')
    return int(Web3.to_wei(usd/eth_price,'ether')/250000000)

#查看tx状态
def check_tx_success(tx,rpc="https://mainnet.era.zksync.io"):
    toDo = 0
    while toDo < 6:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            txn = w3.eth.get_transaction_receipt(tx)
            status = txn['status']
            if status == 1:
                return True
            else:
                return False
        except:
            time.sleep(3)
            toDo = toDo + 1
    # print("\033[31m{}".format('Core -> Utils -> Tx -> check_tx_sucs(tx,rpc) ERROR'))
    # print("\033[37m{}".format(' '))
    raise Exception('Checking tx success Error')


#取到当前链上ETH的数量
def eth_zk_balance(address,rpc='https://mainnet.era.zksync.io' ):
    address = Web3.to_checksum_address(address)
    toDo = 0

    while toDo < 3:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            balance = w3.eth.get_balance(address)
            return balance
        except:
            toDo = toDo + 1
            time.sleep(5)
        # try:
        #     ZKSYNC_PROVIDER = "https://mainnet.era.zksync.io"
        #     zksync_web3 = ZkSyncBuilder.build(ZKSYNC_PROVIDER)
        #     zk_balance = zksync_web3.zksync.get_balance(address, EthBlockParams.LATEST.value)
        #     return zk_balance
        # except:
        #
        #     toDo = toDo + 1
        #     time.sleep(5)
    # print("\033[31m{}".format('Core -> Utils -> Balance -> eth_zk_balance(address) ERROR'))
    # print("\033[0m{}".format(' '))
    # return 'ERROR'
    raise Exception('ZkSync Eth Balance Error')
    # print(f"Balance: {zk_balance}")


#钱包里的钱是否够付这次交易费用
def check_if_ready(address,volume_to_swap,tx_costs,tx_how_many):
    balance = float(Web3.from_wei(eth_zk_balance(address),'ether'))*crypto_to_usd()

    balance = balance - volume_to_swap
    txs = (balance/tx_costs)/2

    if balance<0:
        return (False,0)
    if tx_how_many>txs:
        return (False,txs)
    if tx_how_many<=txs:
        return (True,txs)

#取到当前链上某个币种的数量
def check_token_balance(address,token_address='0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4',  rpc='https://mainnet.era.zksync.io', ABI = None):
    toDo = 0
    while toDo<3:
        try:
            if ABI == None:

                with open('src/abi/erc20abi.json') as jsonabi:
                    ABI = json.load(jsonabi)
                    # print(ABI)

            if True:
                web3 = Web3(Web3.HTTPProvider(rpc))
                token = web3.eth.contract(address=web3.to_checksum_address(token_address), abi=ABI)
                token_balance = token.functions.balanceOf(web3.to_checksum_address(address)).call()
                return token_balance

        except:
            time.sleep(5)
            toDo = toDo + 1
    raise Exception('ERC20 Token Balance Error')


