import asyncio
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


class DiscordRumble:
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
            self.config.AI_RUMBLE.MESSAGES_TO_SEND_PER_ACCOUNT[0],
            self.config.AI_RUMBLE.MESSAGES_TO_SEND_PER_ACCOUNT[1],
        )

        for message_index in range(number_of_messages_to_send):
            for retry_index in range(self.config.SETTINGS.ATTEMPTS):
                try:
                    message_sent = False
                    replied_to_me = False

                    logger.info(f"guild_id:{self.account.guild_id}")
                    logger.info(f"channel_id:{self.account.channel_id}")
                    if not self.account.remble_txt_to_send:
                        logger.info("请在 accounts_rumble.csv 表格配置：RUMBLE_TEXT 特征值！")
                        return False

                    if not self.account.rumble_emoji_id:
                        logger.info("请在 accounts_rumble.csv 表格配置：RUMBLE_EMOJI_ID 特征值！")
                        return False

                    if not self.account.rumble_emoji_name :
                        logger.info("请在 accounts_rumble.csv 表格配置：RUMBLE_EMOJI_NAME 特征值！")
                        return False


                    last_messages = await self._get_last_chat_messages(
                        self.account.guild_id, self.account.channel_id
                    )

                    ### 这是老代码，读取配置文件
                    # last_messages = await self._get_last_chat_messages(
                    #     self.config.AI_RUMBLE.GUILD_ID, self.config.AI_RUMBLE.CHANNEL_ID
                    # )


                    logger.info(
                        f"{self.account.index} | Last messages: {len(last_messages)} "
                    )
                    await get_account_info(self.account, self.config, self.client)

                    message_sent = True
                    if message_sent:
                        random_pause = random.randint(
                            self.config.AI_RUMBLE.PAUSE_BETWEEN_MESSAGES[0],
                            self.config.AI_RUMBLE.PAUSE_BETWEEN_MESSAGES[1],
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



    # 发送钉钉通知
    async def send_dingding_message(self,message):
        headers = {"Content-Type": "application/json"}
        data = {
            "msgtype": "text",
            "text": {"content": message}
        }
        # 钉钉机器人 Webhook（替换为你的 webhook 地址）
        dingding_webhook = "https://oapi.dingtalk.com/robot/send?access_token=e2b65fe211cf18a"
        response = await self.client.post(dingding_webhook, data=json.dumps(data), headers=headers)
        return response.json()

    async def _get_last_chat_messages(
        self, guild_id: str, channel_id: str, quantity: int = 10
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

            if response.status_code != 200:
                logger.error(
                    f"Error in _get_last_chat_messages: {response.status_code} ---- {response.text}"
                )
                return []

            received_messages = []
            message_data = response.json()
            contents = [item['content'] for item in message_data]

            logger.success(contents)

            for message in response.json():
                try:

                    # if "quillsully" in message["author"]["username"] and "top 5 gets fucfs" in message["content"].lower():
                    #     # 获取当前时间（格式：YYYY-MM-DD HH:MM:SS）
                    #     current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    #     dingding_message = f"🚨  【{current_time}】，大逃杀开始了"
                    #     logger.info(dingding_message)
                    #     await self.send_dingding_message(dingding_message)

                    # 要搜索的文本（转换为小写）
                    #search_text = "click the emoji below to join"
                    #search_text = self.config.AI_RUMBLE.RUMBLE_TEXT
                    search_text = "click the emoji below to join"

                    logger.info(f"rumble_emoji_id:{self.account.rumble_emoji_id}")
                    logger.info(f"rumble_emoji_name:{self.account.rumble_emoji_name}")
                    logger.info(f"remble_txt_to_send:{self.account.remble_txt_to_send}")
                    if self.account.remble_txt_to_send:
                        search_text = random.choice(self.account.remble_txt_to_send)

                    logger.info(search_text)

                    # 遍历 embeds，忽略大小写匹配
                    found = any(search_text in embed.get('description', '').lower() for embed in message.get('embeds', []))

                    if found:

                        message_id = message.get('id')

                        # 提取 reactions 里面的 emoji ID 和 name
                        reactions = message.get("reactions", [])
                        #emoji_id = 1351300894087581807
                        #emoji_name = 'Swrd552'
                        # ## 旧代码
                        # emoji_id= self.config.AI_RUMBLE.RUMBLE_EMOJI_ID
                        # emoji_name= self.config.AI_RUMBLE.RUMBLE_EMOJI_NAME

                        emoji_id = self.account.rumble_emoji_id
                        emoji_name = self.account.rumble_emoji_name

                        # 提取第一个 reaction 的 emoji ID 和 name
                        if message.get("reactions"):
                            first_reaction = message["reactions"][0]
                            emoji_id = first_reaction["emoji"].get("id")
                            emoji_name = first_reaction["emoji"].get("name")

                        # 打印结果
                        logger.success(f"Found! ID:{message_id} Emoji ID:{emoji_id} Emoji Name:{emoji_name}")

                        for _ in range(3):
                            url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/{emoji_name}%3A{emoji_id}/%40me?location=Message%20Inline%20Button&type=0",
                            logger.success(url)
                            response = await self.client.put(
                                f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/{emoji_name}%3A{emoji_id}/%40me?location=Message%20Inline%20Button&type=0",
                                params=params,
                                headers=headers,
                            )
                            logger.info(response)
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            dingding_message = f"🚨  【{current_time}】，最新监控代码生效，开始参加{message_id}的大逃杀"
                            logger.success(dingding_message)

                    else:
                        logger.info("Not Found  message_id")


                    # if "Rumble Royale" in message["author"]["username"] and message["type"]==20:
                    #     # 获取当前时间（格式：YYYY-MM-DD HH:MM:SS）
                    #     message_id = message["id"]
                    #     for _ in range(3):
                    #         response = await self.client.put(
                    #             f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/Swrd442%3A1348369538441281688/%40me?location=Message%20Inline%20Button&type=0",
                    #             params=params,
                    #             headers=headers,
                    #         )
                    #         logger.info(response)
                    #         current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    #         dingding_message = f"🚨  【{current_time}】，开始参加{message_id}的大逃杀"
                    #         logger.success(dingding_message)


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

            #print(received_messages)

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
