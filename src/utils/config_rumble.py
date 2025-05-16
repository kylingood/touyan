from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import yaml
from pathlib import Path
import asyncio

from src.utils.constants_rumble import DataForTasks


@dataclass
class SettingsConfig:
    DISCORD_TOKEN_FOR_PARSING: str
    PROXY_FOR_PARSING: str
    THREADS: int
    ATTEMPTS: int
    SHUFFLE_ACCOUNTS: bool
    ACCOUNTS_RANGE: Tuple[int, int]
    EXACT_ACCOUNTS_TO_USE: List[int]
    PAUSE_BETWEEN_ATTEMPTS: Tuple[int, int]
    RANDOM_PAUSE_BETWEEN_ACCOUNTS: Tuple[int, int]
    RANDOM_PAUSE_BETWEEN_ACTIONS: Tuple[int, int]
    RANDOM_INITIALIZATION_PAUSE: Tuple[int, int]
    RANDOM_PROFILE_PICTURES: bool

    TASK: str
    DATA_FOR_TASKS: DataForTasks

@dataclass
class ChatterConfig:
    GUILD_ID: str
    CHANNEL_ID: str
    ANSWER_PERCENTAGE: int
    REPLY_PERCENTAGE: int
    MESSAGES_TO_SEND_PER_ACCOUNT: Tuple[int, int]
    PAUSE_BETWEEN_MESSAGES: Tuple[int, int]
    PAUSE_BEFORE_MESSAGE: Tuple[int, int]


@dataclass
class ReplyConfig:
    GUILD_ID: str
    CHANNEL_ID: str
    ANSWER_PERCENTAGE: int
    REPLY_PERCENTAGE: int
    MESSAGES_TO_SEND_PER_ACCOUNT: Tuple[int, int]
    PAUSE_BETWEEN_MESSAGES: Tuple[int, int]
    PAUSE_BEFORE_MESSAGE: Tuple[int, int]

@dataclass
class RumbleConfig:
    GUILD_ID: str
    CHANNEL_ID: str
    RUMBLE_TEXT: str
    RUMBLE_EMOJI_ID: str
    RUMBLE_EMOJI_NAME: str
    ANSWER_PERCENTAGE: int
    REPLY_PERCENTAGE: int
    MESSAGES_TO_SEND_PER_ACCOUNT: Tuple[int, int]
    PAUSE_BETWEEN_MESSAGES: Tuple[int, int]
    PAUSE_BEFORE_MESSAGE: Tuple[int, int]

class UsernameConfig:
    GUILD_ID: str
    CHANNEL_ID: str
    ANSWER_PERCENTAGE: int
    REPLY_PERCENTAGE: int
    MESSAGES_TO_SEND_PER_ACCOUNT: Tuple[int, int]
    PAUSE_BETWEEN_MESSAGES: Tuple[int, int]
    PAUSE_BEFORE_MESSAGE: Tuple[int, int]



@dataclass
class MessageSenderConfig:
    GUILD_ID: str
    CHANNEL_ID: str
    DELETE_MESSAGE_INSTANTLY: bool
    SEND_MESSAGES_RANDOMLY: bool
    NUMBER_OF_MESSAGES_TO_SEND: int
    PAUSE_BETWEEN_MESSAGES: Tuple[int, int]

@dataclass
class ChatGPTConfig:
    API_KEYS: List[str]
    MODEL: str
    PROXY_FOR_CHAT_GPT: str

@dataclass
class DeepSeekConfig:
    API_KEYS: List[str]
    MODEL: str
    PROXY_FOR_DEEPSEEK: str


@dataclass
class Config_Rumble:
    SETTINGS: SettingsConfig
    AI_REPLY: ReplyConfig
    AI_RUMBLE: RumbleConfig
    MESSAGE_SENDER: MessageSenderConfig
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @classmethod
    def load(cls, path: str = "config_rumble.yaml") -> "Config_Rumble":
        """Load configuration from yaml file"""
        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        return cls(
            SETTINGS=SettingsConfig(
                DISCORD_TOKEN_FOR_PARSING=data["SETTINGS"]["DISCORD_TOKEN_FOR_PARSING"],
                PROXY_FOR_PARSING=data["SETTINGS"]["PROXY_FOR_PARSING"],
                THREADS=data["SETTINGS"]["THREADS"],
                ATTEMPTS=data["SETTINGS"]["ATTEMPTS"],
                SHUFFLE_ACCOUNTS=data["SETTINGS"]["SHUFFLE_ACCOUNTS"],
                ACCOUNTS_RANGE=tuple(data["SETTINGS"]["ACCOUNTS_RANGE"]),
                EXACT_ACCOUNTS_TO_USE=data["SETTINGS"]["EXACT_ACCOUNTS_TO_USE"],
                PAUSE_BETWEEN_ATTEMPTS=tuple(
                    data["SETTINGS"]["PAUSE_BETWEEN_ATTEMPTS"]
                ),
                RANDOM_PAUSE_BETWEEN_ACCOUNTS=tuple(
                    data["SETTINGS"]["RANDOM_PAUSE_BETWEEN_ACCOUNTS"]
                ),
                RANDOM_PAUSE_BETWEEN_ACTIONS=tuple(
                    data["SETTINGS"]["RANDOM_PAUSE_BETWEEN_ACTIONS"]
                ),
                RANDOM_INITIALIZATION_PAUSE=tuple(
                    data["SETTINGS"]["RANDOM_INITIALIZATION_PAUSE"]
                ),
                RANDOM_PROFILE_PICTURES=data["SETTINGS"]["RANDOM_PROFILE_PICTURES"],
                TASK="",
                DATA_FOR_TASKS=None,
            ),
            AI_RUMBLE=RumbleConfig(
                GUILD_ID=data["AI_RUMBLE"]["GUILD_ID"],
                CHANNEL_ID=data["AI_RUMBLE"]["CHANNEL_ID"],
                RUMBLE_TEXT=data["AI_RUMBLE"]["RUMBLE_TEXT"],
                RUMBLE_EMOJI_ID=data["AI_RUMBLE"]["RUMBLE_EMOJI_ID"],
                RUMBLE_EMOJI_NAME=data["AI_RUMBLE"]["RUMBLE_EMOJI_NAME"],
                ANSWER_PERCENTAGE=data["AI_RUMBLE"]["ANSWER_PERCENTAGE"],
                REPLY_PERCENTAGE=data["AI_RUMBLE"]["REPLY_PERCENTAGE"],
                MESSAGES_TO_SEND_PER_ACCOUNT=tuple(
                    data["AI_RUMBLE"]["MESSAGES_TO_SEND_PER_ACCOUNT"]
                ),
                PAUSE_BETWEEN_MESSAGES=tuple(data["AI_RUMBLE"]["PAUSE_BETWEEN_MESSAGES"]),
                PAUSE_BEFORE_MESSAGE=tuple(data["AI_RUMBLE"]["PAUSE_BEFORE_MESSAGE"]),
            ),
            AI_REPLY=ReplyConfig(
                GUILD_ID=data["AI_REPLY"]["GUILD_ID"],
                CHANNEL_ID=data["AI_REPLY"]["CHANNEL_ID"],
                ANSWER_PERCENTAGE=data["AI_REPLY"]["ANSWER_PERCENTAGE"],
                REPLY_PERCENTAGE=data["AI_REPLY"]["REPLY_PERCENTAGE"],
                MESSAGES_TO_SEND_PER_ACCOUNT=tuple(
                    data["AI_REPLY"]["MESSAGES_TO_SEND_PER_ACCOUNT"]
                ),
                PAUSE_BETWEEN_MESSAGES=tuple(data["AI_REPLY"]["PAUSE_BETWEEN_MESSAGES"]),
                PAUSE_BEFORE_MESSAGE=tuple(data["AI_REPLY"]["PAUSE_BEFORE_MESSAGE"]),
            ),
            MESSAGE_SENDER=MessageSenderConfig(
                GUILD_ID=data["MESSAGE_SENDER"]["GUILD_ID"],
                CHANNEL_ID=data["MESSAGE_SENDER"]["CHANNEL_ID"],
                DELETE_MESSAGE_INSTANTLY=data["MESSAGE_SENDER"]["DELETE_MESSAGE_INSTANTLY"],
                SEND_MESSAGES_RANDOMLY=data["MESSAGE_SENDER"]["SEND_MESSAGES_RANDOMLY"],
                NUMBER_OF_MESSAGES_TO_SEND=data["MESSAGE_SENDER"]["NUMBER_OF_MESSAGES_TO_SEND"],
                PAUSE_BETWEEN_MESSAGES=tuple(data["MESSAGE_SENDER"]["PAUSE_BETWEEN_MESSAGES"]),
            )
        )
# Singleton pattern
def get_config_rumble() -> Config_Rumble:
    """Get configuration singleton"""
    if not hasattr(get_config_rumble, "_config"):
        get_config_rumble._config = Config_Rumble.load()
    return get_config_rumble._config
