from configparser import ConfigParser
from typing import Dict, Any

from pydantic import BaseModel, SecretStr


def parse_config_file(config_file: str) -> Dict[str, Dict[str, Any]]:
    config = ConfigParser()
    config.read(config_file)

    config_data = {}

    for section in config.sections():
        main_section = section.split('.')[0]

        if section != main_section:
            secondary_section = section.split('.')[1]
            if main_section in config_data.keys():
                config_data[main_section][secondary_section] = dict(config.items(section))
            else:
                config_data[main_section] = {}
                config_data[main_section][secondary_section] = dict(config.items(section))
        else:
            config_data[section] = dict(config.items(section))

    return config_data


class BotConfig(BaseModel):
    token: SecretStr


class DatabaseConfig(BaseModel):
    username: str
    password: SecretStr
    ip: str
    port: int
    db: str


class Config(BaseModel):
    DATABASE: DatabaseConfig
    BOT: BotConfig


config = Config(**parse_config_file("config.ini"))
