# -*- coding: utf-8 -*-

# 数据库配置信息

CONFIG = {
    0: {
        #"host": '192.168.60.2',
        #"user": 'root',
        #"password": 'Guzi@123',
        #"database": 'twitter',
        "host": '127.0.0.1',
        "user": 'guzi',  # 可选，默认root
        "password": 'J8s2e88y2xLeFRC2',  # 必选
        "database": 'guzi',  # 必选
        'port': 3306,
        'dbms': 'mysql',
        'charset': 'utf8mb4',
        'DB_DEBUG': True,
        'autocommit': True,
        'connect_timeout': 1800
    },
    '1': {
        'database': 'db_name2',
    },
}
