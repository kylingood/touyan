from flask import Flask, render_template, request, g,jsonify
from web3_auth import web3_auth  # 导入我们刚才创建的 web3_auth Blueprint
from category import category
from twitter import twitter
from discord import discord

from util.db import *
from web3_auth import require_login  # 导入 require_login 装饰器
from auth import require_user
app = Flask(__name__)


# 注册 web3_auth Blueprint
app.register_blueprint(web3_auth)
# 注册 category Blueprint
app.register_blueprint(category)

# 注册 twitter Blueprint
app.register_blueprint(twitter)

# 注册 twitter Blueprint
app.register_blueprint(discord)

@app.route("/")
def index():

    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True)
