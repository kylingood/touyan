import asyncio
from dataclasses import dataclass
import random
from loguru import logger
from curl_cffi.requests import AsyncSession 



@dataclass
class AccountInfo:
    id: str
    username: str
    global_name: str
    email: str
    verified: bool
    phone: str
    bio: str


@dataclass
class ChannelInfo:
    id: str
    type: bool
    last_message_id: str
    flags: bool
    guild_id: str
    name: str
    parent_id: str
    guild_name:str
    guild_description:str
    guild_icon:str

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


async def get_channel_info(token,guild_id,channel_id, session: AsyncSession
) -> ChannelInfo | None:
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
                f"https://discord.com/api/v9/channels/{channel_id}", headers=headers
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get account info: {response.status_code} | {response.text}"
                )

            data = response.json()

            response = await session.get(
                f"https://discord.com/api/v9/guilds/{guild_id}", headers=headers
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to get account info: {response.status_code} | {response.text}"
                )

            guild_data = response.json()

            account_info = ChannelInfo(
                id=data["id"],
                type=data["type"],
                last_message_id=data["last_message_id"],
                flags=data["flags"],
                guild_id=data["guild_id"],
                guild_name=guild_data["name"],
                guild_description=guild_data["description"],
                guild_icon=guild_data["icon"],
                name=data["name"],
                parent_id=data["parent_id"],
            )
            RED = "\033[31m"
            GREEN = "\033[32m"
            RESET = "\033[0m"

            logger.success(f"获取 服务器名: {RED}{account_info.guild_name}{RESET}  | 频道名: {RED}{account_info.name}{RESET} ID: {RED}{account_info.id}{RESET}   token: {GREEN}{token}{RESET} ")

            # logger.success(
            #     f"[{account.index}] | Got account info for {account_info.username}"
            # )
            return account_info

        except Exception as e:
            random_pause = random.randint(1,3)
            logger.error(f"[{token}] | Error in get_account_info: {e}. Pausing for {random_pause} seconds.")
            await asyncio.sleep(random_pause)

    return None


async def get_discord_message(token, guild_id,channel_id,quantity, session: AsyncSession
) -> AccountInfo | None:
    for retry in range(3):
        try:

            headers = {
                "authorization": token,
                "referer": f"https://discord.com/channels/{guild_id}/{channel_id}",
                "x-discord-locale": "en-US",
                "x-discord-timezone": "Etc/GMT-2",
            }

            params = {
                "limit": str(quantity),
            }

            response = await session.get(
                f"https://discord.com/api/v9/channels/{channel_id}/messages",
                params=params,
                headers=headers,
            )

            logger.info(f"https://discord.com/api/v9/channels/{channel_id}/messages")
            if response.status_code != 200:
                logger.error(
                    f"Error in _get_last_chat_messages: {response.status_code} ---- {response.text}"
                )
                return []

            data = response.json()


            return data

        except Exception as e:
            random_pause = random.randint(1,3)
            logger.error(f"[{token}] | Error in get_account_info: {e}. Pausing for {random_pause} seconds.")
            await asyncio.sleep(random_pause)

    return None