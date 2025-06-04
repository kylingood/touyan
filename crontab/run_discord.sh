#!/bin/bash
cd /home/touyan || exit 1
PYTHONPATH=. /www/server/pyporject_evn/versions/3.13.3/bin/python crontab/discord.py