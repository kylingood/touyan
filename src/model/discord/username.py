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


@dataclass
class AccountInfo:
    id: str
    username: str
    global_name: str
    email: str
    verified: bool
    phone: str
    bio: str

class DiscordUsername:
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

        for message_index in range(1):
            for retry_index in range(self.config.SETTINGS.ATTEMPTS):
                try:
                    await get_account_info(self.account, self.config, self.client)
                    break
                except Exception as e:
                    logger.error(f"{self.account.index} | Error in start_chatting: {e}")
                    return False

