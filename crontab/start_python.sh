#!/bin/bash

# 查找 main.py 的进程 ID
PID=$(ps -ef | grep "main.py" | grep -v "grep" | awk '{print $2}')

# 如果找到进程，则杀掉
if [ -n "$PID" ]; then
  echo "找到进程 PID: $PID，准备结束进程..."
  kill -9 $PID
  echo "进程已结束。"
else
  echo "未找到 main.py 进程，跳过 kill。"
fi

# 启动新的进程
echo "启动 main.py..."
nohup /www/server/pyporject_evn/versions/3.13.3/bin/python /home/touyan/main.py > /home/touyan/main.log 2>&1 &

# 等待 1 秒再检查
sleep 1

# 再次查找进程确认是否启动成功
NEW_PID=$(ps -ef | grep "main.py" | grep -v "grep" | awk '{print $2}')

if [ -n "$NEW_PID" ]; then
  echo "✅ main.py 启动成功，PID: $NEW_PID"
else
  echo "❌ 启动失败，未检测到 main.py 进程"
fi
