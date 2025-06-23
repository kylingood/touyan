# -*- coding: utf-8 -*-
from quart import Blueprint, request, jsonify
import aiohttp

captcha = Blueprint('captcha', __name__)

@captcha.route('/captcha/api', methods=['POST'])
async def api():
    try:
        # 获取前端 JSON 数据
        client_data = await request.get_json()
        print("📥 Received POST data:", client_data)

        # 必要字段检查
        if "type" not in client_data or "websiteUrl" not in client_data:
            return jsonify({
                "code": 400,
                "message": "缺少必要参数: type 或 websiteUrl"
            }), 400

        # 构建 payload
        payload = {
            "type": client_data["type"],
            "websiteUrl": client_data["websiteUrl"]
        }

        # 可选字段
        for field in ["websiteKey", "pageAction", "method", "authToken", "proxy"]:
            if field in client_data:
                payload[field] = client_data[field]

        # 根据类型选择 URL
        captcha_type = client_data["type"]
        if captcha_type in ["cftoken", "cfcookie"]:
            solver_url = "http://localhost:3000/"
        else:
            solver_url = "http://localhost:3000/solve"

        headers = {
            "Content-Type": "application/json"
        }

        print(f"📤 Forwarding to {solver_url} with:", payload)

        # 使用 aiohttp 发起异步请求
        async with aiohttp.ClientSession() as session:
            async with session.post(solver_url, json=payload, headers=headers, timeout=300) as resp:
                result = await resp.json()

                if resp.status == 200 and result.get("code") == 200:
                    print("✅ 验证成功:", result)
                    return jsonify(result)
                else:
                    print("⚠️ 验证失败:", result)
                    return jsonify(result), resp.status

    except Exception as e:
        print("❌ 异常发生:", str(e))
        return jsonify({
            "code": 500,
            "message": f"服务器异常: {str(e)}"
        }), 500
