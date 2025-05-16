from curl_cffi.requests import AsyncSession

async def create_client(proxy: str) -> AsyncSession:
    # session = primp.AsyncClient(impersonate="chrome_131", verify=False)

    session = AsyncSession(
                impersonate="chrome131",
                verify=False,
                timeout=60,
            )
    # if proxy:
    #     session.proxies.update({
    #         "http": "http://" + proxy,
    #         "https": "http://" + proxy,
    #     })

    if proxy:
        # 去掉前后的空格
        proxy = proxy.strip()

        # 处理 SOCKS5 代理
        if "socks5" in proxy.lower():
            if not proxy.startswith("socks5://"):
                proxy = f"socks5://{proxy}"  # 如果没有协议头则添加
            session.proxies.update({
                "socks5": proxy,  # SOCKS5 代理也可以用于 http 和 https
            })
        # 处理 HTTP 代理
        elif "http" in proxy.lower():
            if not proxy.startswith("http://"):
                proxy = f"http://{proxy}"  # 如果没有协议头则添加
            session.proxies.update({
                "http": proxy,
                "https": proxy,
            })

        else:
            # 默认处理为 HTTP 代理
            if not proxy.startswith("http://"):
                proxy = f"http://{proxy}"
            session.proxies.update({
                "http": proxy,
                "https": proxy,
            })

    session.headers.update(HEADERS)

    return session

HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,zh-TW;q=0.6,zh;q=0.5',
    'content-type': 'application/json',
    'priority': 'u=1, i',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}
