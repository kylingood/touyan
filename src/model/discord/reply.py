import asyncio
import time
import os
import sys
from dataclasses import dataclass
from loguru import logger
import random
from curl_cffi.requests import AsyncSession

import json
from datetime import datetime

from src.model.discord.utils import calculate_nonce
from src.utils.config_rumble import Config_Rumble
from src.model.gpt import ask_chatgpt
from src.model.gpt.prompts import (
    BATCH_MESSAGES_SYSTEM_PROMPT as GPT_BATCH_MESSAGES_SYSTEM_PROMPT,
    REFERENCED_MESSAGES_SYSTEM_PROMPT as GPT_REFERENCED_MESSAGES_SYSTEM_PROMPT,
)
from src.model.deepseek.deepseek import ask_deepseek
from src.model.deepseek.prompts import (
    BATCH_MESSAGES_SYSTEM_PROMPT as DEEPSEEK_BATCH_MESSAGES_SYSTEM_PROMPT,
    REFERENCED_MESSAGES_SYSTEM_PROMPT as DEEPSEEK_REFERENCED_MESSAGES_SYSTEM_PROMPT,
)
from src.utils.constants_rumble import Account
from src.model.discord.get_account_info import get_account_info



@dataclass
class ReceivedMessage:
    """Represents a message received from Discord"""

    type: int
    content: str
    message_id: str
    channel_id: str
    author_id: str
    author_username: str
    referenced_message_content: str
    referenced_message_author_id: str


class DiscordReply:
    def __init__(
            self,
            account: Account,
            client: AsyncSession,
            config: Config_Rumble,
    ):
        self.account = account
        self.client = client
        self.config = config

        self.my_account_id: str = ""
        self.my_account_username: str = ""
        self.my_replies_messages: list = []

    async def start_chatting(self) -> bool:

        number_of_messages_to_send = random.randint(
            self.config.AI_REPLY.MESSAGES_TO_SEND_PER_ACCOUNT[0],
            self.config.AI_REPLY.MESSAGES_TO_SEND_PER_ACCOUNT[1],
        )


        for message_index in range(number_of_messages_to_send):
            for retry_index in range(self.config.SETTINGS.ATTEMPTS):
                try:
                    message_sent = False
                    replied_to_me = False
                    ### 根据频道取到相关信息，这是新代码读取cvs的配置信息

                    #logger.info(self.account)
                    logger.info(f"guild_id:{self.account.guild_id}")
                    logger.info(f"channel_id:{self.account.channel_id}")


                    ### 单纯的回复或签到功能
                    if self.account.reply_txt_to_send:
                        last_messages = await self._get_last_chat_messages_edu(
                            self.account.guild_id, self.account.channel_id
                        )
                    else:
                        ### 回复抢白名单
                        last_messages = await self._get_last_chat_messages(
                            self.account.guild_id, self.account.channel_id
                        )

                    # ### 这是老代码，读取配置文件
                    # last_messages = await self._get_last_chat_messages(
                    #     self.config.AI_REPLY.GUILD_ID, self.config.AI_REPLY.CHANNEL_ID
                    # )


                    logger.info(
                        f"{self.account.index} | Last messages: {len(last_messages)} "
                    )
                    await get_account_info(self.account, self.config, self.client)

                    message_sent = True
                    if message_sent:
                        random_pause = random.randint(
                            self.config.AI_REPLY.PAUSE_BETWEEN_MESSAGES[0],
                            self.config.AI_REPLY.PAUSE_BETWEEN_MESSAGES[1],
                        )
                        logger.info(
                            f"{self.account.index} | Pausing for {random_pause} seconds before next message."
                        )
                        await asyncio.sleep(random_pause)
                        break

                    else:
                        random_pause = random.randint(
                            self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                            self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
                        )
                        logger.info(
                            f"{self.account.index} | No message send. Pausing for {random_pause} seconds before next try."
                        )
                        await asyncio.sleep(random_pause)

                except Exception as e:
                    logger.error(f"{self.account.index} | Error in start_chatting: {e}")
                    return False

    async def _send_message(
            self,
            message: str,
            channel_id: str,
            guild_id: str,
            reply_to_message_id: str = None,
    ) -> tuple[bool, dict]:
        try:
            headers = {
                "authorization": self.account.token,
                "content-type": "application/json",
                "origin": "https://discord.com",
                "referer": f"https://discord.com/channels/{guild_id}/{channel_id}",
                "x-debug-options": "bugReporterEnabled",
                "x-discord-locale": "en-US",
                "x-discord-timezone": "Etc/GMT-2",
                # 'x-super-properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InJ1IiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEzMi4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTMyLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiJodHRwczovL2Rpc2NvcmQuY29tLyIsInJlZmVycmluZ19kb21haW4iOiJkaXNjb3JkLmNvbSIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjozNjY5NTUsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGwsImhhc19jbGllbnRfbW9kcyI6ZmFsc2V9',
            }

            json_data = {
                "mobile_network_type": "unknown",
                "content": message,
                "nonce": calculate_nonce(),
                "tts": False,
                "flags": 0,
            }

            if reply_to_message_id:
                json_data["message_reference"] = {
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "message_id": reply_to_message_id,
                }

            response = await self.client.post(
                f"https://discord.com/api/v9/channels/{channel_id}/messages",
                headers=headers,
                json=json_data,
            )

            return response.status_code == 200, response.json()

        except Exception as e:
            logger.error(f"{self.account.index} | Error in send_message: {e}")
            return False, None

    def find_lines_get_content(self,file_path, content, is_lower=0):
        # 用于存储匹配内容的行
        matching_lines = []

        ##不区分大小写内容
        if is_lower == 1:
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



    async def _get_last_chat_messages_edu(
            self, guild_id: str, channel_id: str, quantity: int = 5
    ) -> list[str]:
        try:

            headers = {
                "authorization": self.account.token,
                "referer": f"https://discord.com/channels/{guild_id}/{channel_id}",
                "x-discord-locale": "en-US",
                "x-discord-timezone": "Etc/GMT-2",
                # 'x-super-properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InJ1IiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEzMi4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTMyLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiJodHRwczovL2Rpc2NvcmQuY29tLyIsInJlZmVycmluZ19kb21haW4iOiJkaXNjb3JkLmNvbSIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjozNjY5NTUsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGwsImhhc19jbGllbnRfbW9kcyI6ZmFsc2V9',
            }

            logger.info(f"timestamp:{self.account.timestamp}")
            logger.info(f"rumble_emoji_id:{self.account.rumble_emoji_id}")
            logger.info(f"rumble_emoji_name:{self.account.rumble_emoji_name}")
            logger.info(f"reply_txt_to_send:{self.account.reply_txt_to_send}")
            logger.info(f"remble_txt_to_send:{self.account.remble_txt_to_send}")


            # 获取当前时间（格式：YYYY-MM-DD HH:MM:SS）

            message_id = ''
            account_token = self.account.index
            channel_id = self.account.channel_id
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_time_log = datetime.now().strftime("%Y-%m-%d")
            #gpt_response = 'gblend'
            ### 取到回复的内容
            gpt_response = 'GM'
            if self.account.reply_txt_to_send:
                gpt_response = random.choice(self.account.reply_txt_to_send)

            timestamp = 864000
            if  self.account.timestamp:
                timestamp = self.account.timestamp

            # 获取当前时间的时间戳（以秒为单位）
            current_timestamp = int(time.time())
            logger.success(f"当前时间戳是: {current_timestamp}  ")
            # 转换为年月日时分秒格式
            current_time = datetime.fromtimestamp(current_timestamp).strftime(f'%Y-%m-%d %H:%M:%S  要回复的内容为: {gpt_response}')
            logger.success(f"当前时间是: {current_time}")

            ### 先查找这个地址有没有存在文件中
            log_file = f'send_message_record.txt'
            log_content = f"{current_time_log}----{account_token}----{channel_id}"
            result_content = self.find_lines_get_content(log_file, log_content)
            logger.info('***********')
            logger.info(result_content)
            logger.info('***********')
            is_flag = True
            for input_string in result_content:
                # 使用分号分割字符串
                parts = input_string.split("----")
                # 选择需要的时间元素
                stored_timestamp = int(parts[2])
                # 比较两个时间戳，判断是否超过 24 小时
                if current_timestamp - stored_timestamp >= int(timestamp):
                    logger.success(f"恭喜，可以回复信息：{message_id}...")
                    is_flag = True
                else:
                    logger.error(f"已回复信息,不用再回了...")
                    is_flag = False
                    break

            ###如果发现已回复，就不再回信息了
            if is_flag:
                ok, json_response = await self._send_message(
                    gpt_response,
                    channel_id,
                    guild_id,
                    message_id,
                )

                if ok:
                    logger.success(
                        f"{self.account.index} | Message with reply sent: {gpt_response}"
                    )

                    # 打开文件，以覆盖写入模式
                    with open(log_file, 'a') as file:
                        content = f"{current_time_log}----{account_token}----{channel_id}----{current_timestamp}----{current_time}"
                        file.write(content + '\n')  # 添加换行符来保证每个地址占一行
            else:
                logger.success(f"已回复过此条信息，{message_id}...")


            return []

        except Exception as e:
            logger.error(
                f"{self.account.index} | Error in _get_last_chat_messages: {e}"
            )
            return []


    async def _get_last_chat_messages(
            self, guild_id: str, channel_id: str, quantity: int = 5
    ) -> list[str]:
        try:

            headers = {
                "authorization": self.account.token,
                "referer": f"https://discord.com/channels/{guild_id}/{channel_id}",
                "x-discord-locale": "en-US",
                "x-discord-timezone": "Etc/GMT-2",
                # 'x-super-properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InJ1IiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEzMi4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTMyLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiJodHRwczovL2Rpc2NvcmQuY29tLyIsInJlZmVycmluZ19kb21haW4iOiJkaXNjb3JkLmNvbSIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjozNjY5NTUsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGwsImhhc19jbGllbnRfbW9kcyI6ZmFsc2V9',
            }

            logger.info(f"quantity:{self.account.quantity}")
            if self.account.quantity:
                quantity = int(self.account.quantity)

            params = {
                "limit": str(quantity),
            }

            response = await self.client.get(
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

            received_messages = []

            ##logger.info(response.json())

            for message in response.json():
                try:
                    #yeez000  robotcoin
                    if "yeez000" in message["author"]["username"] and  "gblend" in message["content"].lower() :
                        # 获取当前时间（格式：YYYY-MM-DD HH:MM:SS）
                        content = message.get('content')
                        message_id = message.get('id')
                        account_token = self.account.index
                        channel_id = self.account.channel_id
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        current_time_log = datetime.now().strftime("%Y-%m-%d")
                        dingding_message = f"🚨  【{current_time}】，当前账号:{account_token}， 信息内容:{content}，message_id:{message_id}"
                        logger.info(dingding_message)
                        #gpt_response = 'gblend'
                        arr = ['gblend', 'Gblend']
                        gpt_response = random.choice(arr)

                        # 获取当前时间的时间戳（以秒为单位）
                        current_timestamp = int(time.time())
                        logger.success(f"当前时间戳是: {current_timestamp}")
                        # 转换为年月日时分秒格式
                        current_time = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                        logger.success(f"当前时间是: {current_time}")

                        ### 先查找这个地址有没有存在文件中
                        log_file = f'send_message_record.txt'
                        log_content = f"{current_time_log}----{account_token}----{channel_id}"
                        result_content = self.find_lines_get_content(log_file, log_content)
                        logger.info('***********')
                        logger.info(result_content)
                        logger.info('***********')
                        is_flag = True
                        for input_string in result_content:
                            # 使用分号分割字符串
                            parts = input_string.split("----")
                            # 选择需要的时间元素
                            stored_timestamp = int(parts[2])
                            # 比较两个时间戳，判断是否超过 24 小时
                            if current_timestamp - stored_timestamp >= 76500:
                                logger.success(f"恭喜，可以回复信息：{message_id}...")
                                is_flag = True
                            else:
                                logger.error(f"已回复信息,不用再回了...")
                                is_flag = False
                                break

                        ###如果发现已回复，就不再回信息了
                        if is_flag:
                            ok, json_response = await self._send_message(
                                gpt_response,
                                channel_id,
                                guild_id,
                                message_id,
                            )

                            if ok:
                                logger.success(
                                    f"{self.account.index} | Message with reply sent: {gpt_response}"
                                )

                                # 打开文件，以覆盖写入模式
                                with open(log_file, 'a') as file:
                                    content = f"{current_time_log}----{account_token}----{channel_id}----{current_timestamp}----{current_time}"
                                    file.write(content + '\n')  # 添加换行符来保证每个地址占一行
                        else:
                            logger.success(f"已回复过此条信息，{message_id}...")

                    message_data = ReceivedMessage(
                        type=message["type"],
                        content=message["content"],
                        message_id=message["id"],
                        channel_id=message["channel_id"],
                        author_id=message["author"]["id"],
                        author_username=message["author"]["username"],
                        referenced_message_content=(
                            ""
                            if message.get("referenced_message") in ["None", None]
                            else message.get("referenced_message", {}).get(
                                "content", ""
                            )
                        ),
                        referenced_message_author_id=(
                            ""
                            if message.get("referenced_message") in ["None", None]
                            else message.get("referenced_message", {})
                            .get("author", {})
                            .get("id", "")
                        ),
                    )

                    received_messages.append(message_data)

                except Exception as e:
                    continue

            # print(received_messages)

            return received_messages

        except Exception as e:
            logger.error(
                f"{self.account.index} | Error in _get_last_chat_messages: {e}"
            )
            return []

    async def _gpt_referenced_messages(
            self, main_message_content: str, referenced_message_content: str
    ) -> str:
        """使用GPT生成对引用消息的回复"""
        try:
            user_message = f"""Previous message: "{referenced_message_content}"
                Reply to it: "{main_message_content}"
                Generate a natural response continuing this conversation.
            """

            ok, gpt_response = ask_chatgpt(
                random.choice(self.config.CHAT_GPT.API_KEYS),
                self.config.CHAT_GPT.MODEL,
                user_message,
                GPT_REFERENCED_MESSAGES_SYSTEM_PROMPT,
                proxy=self.config.CHAT_GPT.PROXY_FOR_CHAT_GPT,
            )

            if not ok:
                raise Exception(gpt_response)

            return gpt_response
        except Exception as e:
            logger.error(
                f"{self.account.index} | Error in chatter _gpt_referenced_messages: {e}"
            )
            raise e

    async def _deepseek_referenced_messages(
            self, main_message_content: str, referenced_message_content: str
    ) -> str:
        """使用DeepSeek生成对引用消息的回复，如果失败则使用ChatGPT"""
        try:
            api_key = random.choice(self.config.DEEPSEEK.API_KEYS)
            user_message = f"消息1: {referenced_message_content}\n消息2: {main_message_content}"

            success, response = await ask_deepseek(
                api_key=api_key,
                model=self.config.DEEPSEEK.MODEL,
                user_message=user_message,
                prompt=DEEPSEEK_REFERENCED_MESSAGES_SYSTEM_PROMPT,
                proxy=self.config.DEEPSEEK.PROXY_FOR_DEEPSEEK,
            )

            if not success:
                logger.warning(f"{self.account.index} | DeepSeek API失败，切换到ChatGPT: {response}")
                return
                # return await self._gpt_referenced_messages(main_message_content, referenced_message_content)

            return response
        except Exception as e:
            logger.warning(f"{self.account.index} | DeepSeek错误，切换到ChatGPT: {str(e)}")
            return
            # return await self._gpt_referenced_messages(main_message_content, referenced_message_content)

    async def _gpt_batch_messages(self, messages_contents: list[str]) -> str:
        """使用GPT基于聊天历史生成新消息"""
        try:
            user_message = f"""
                Chat history: {messages_contents}
            """

            ok, gpt_response = ask_chatgpt(
                random.choice(self.config.CHAT_GPT.API_KEYS),
                self.config.CHAT_GPT.MODEL,
                user_message,
                GPT_BATCH_MESSAGES_SYSTEM_PROMPT,
                proxy=self.config.CHAT_GPT.PROXY_FOR_CHAT_GPT,
            )

            if not ok:
                raise Exception(gpt_response)

            return gpt_response
        except Exception as e:
            logger.error(
                f"{self.account.index} | Error in chatter _gpt_batch_messages: {e}"
            )
            raise e

    async def _deepseek_batch_messages(self, messages_contents: str) -> str:
        """使用DeepSeek基于聊天历史生成新消息，如果失败则使用ChatGPT"""
        try:
            api_key = random.choice(self.config.DEEPSEEK.API_KEYS)

            success, response = await ask_deepseek(
                api_key=api_key,
                model=self.config.DEEPSEEK.MODEL,
                user_message=messages_contents,
                prompt=DEEPSEEK_BATCH_MESSAGES_SYSTEM_PROMPT,
                proxy=self.config.DEEPSEEK.PROXY_FOR_DEEPSEEK,
            )

            if not success:
                logger.warning(f"{self.account.index} | DeepSeek API失败，切换到ChatGPT: {response}")
                return
                # return await self._gpt_batch_messages(messages_contents)

            return response
        except Exception as e:
            logger.warning(f"{self.account.index} | DeepSeek错误，切换到ChatGPT: {str(e)}")
            return
            # return await self._gpt_batch_messages(messages_contents)
