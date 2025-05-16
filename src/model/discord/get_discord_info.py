import asyncio
from dataclasses import dataclass
import random
from loguru import logger
from curl_cffi.requests import AsyncSession 
from src.utils.config import Config
from src.utils.constants_rumble import Account


@dataclass
class AccountInfo:
    id: str
    username: str
    global_name: str
    email: str
    verified: bool
    phone: str
    bio: str


async def get_discord_info(token, session: AsyncSession
) -> AccountInfo | None:
    for retry in range(3):
        try:
            headers = {
                "Authorization": token,
                "referer": "https://discord.com/channels/@me",
                "x-debug-options": "bugReporterEnabled",
                "x-discord-locale": "en-US",
                "x-discord-timezone": "Etc/GMT-2",
            }

            response = await session.get(
                "https://discord.com/api/v9/users/@me", headers=headers
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get account info: {response.status_code} | {response.text}"
                )

            data = response.json()

            account_info = AccountInfo(
                id=data["id"],
                username=data["username"],
                global_name=data["global_name"],
                email=data["email"],
                verified=data["verified"],
                phone=data["phone"],
                bio=data["bio"],
            )
            RED = "\033[31m"
            GREEN = "\033[32m"
            RESET = "\033[0m"

            logger.success(f"[{token}] | 获取账号信息，显示名: {RED}{account_info.global_name}{RESET} 账号: {RED}{account_info.username}{RESET}   token: {GREEN}{token}{RESET} ")

            # logger.success(
            #     f"[{account.index}] | Got account info for {account_info.username}"
            # )
            return account_info

        except Exception as e:
            random_pause = random.randint(1,3)
            logger.error(f"[{token}] | Error in get_account_info: {e}. Pausing for {random_pause} seconds.")
            await asyncio.sleep(random_pause)

    return None
