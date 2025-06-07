# -*- coding: utf-8 -*-
from quart import Quart, render_template, request,  g, Blueprint
from src.web3_auth import web3_auth  # 导入我们刚才创建的 web3_auth Blueprint
from src.category import category
from src.twitter import twitter
from src.discord import discord
from src.member import member
from src.website import website
# Flask:
#app = Flask(__name__)
# Quart:
app = Quart(__name__)

# 注册 web3_auth Blueprint
app.register_blueprint(web3_auth)
# 注册 category Blueprint
app.register_blueprint(category)

# 注册 twitter Blueprint
app.register_blueprint(twitter)

# 注册 discord Blueprint
app.register_blueprint(discord)

# 注册 member Blueprint
app.register_blueprint(member)

# 注册 member Blueprint
app.register_blueprint(website)

@app.route("/")
async  def index():

    return await  render_template("index.html")

@app.route('/error')
async  def error():

    return await  render_template("error.html")


import asyncio

if __name__ == "__main__":
    #asyncio.run(app.run_task(debug=True))
    #asyncio.run(app.run_task(host="127.0.0.1", port=8080, debug=True))
    #asyncio.run(app.run_task(host="0.0.0.0", port=8080, debug=True))
    asyncio.run(app.run_task(host="127.0.0.1", port=8080))