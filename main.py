import sys

from fastapi import FastAPI

from partybot import line_bot
from partybot import configs

bot_configs = configs.PartyBotConfig()

# get channel_secret and channel_access_token from your environment variable
channel_secret = bot_configs.linebot_secret
channel_access_token = bot_configs.linebot_access_token

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

app = FastAPI()

line_bot.setup(app, channel_secret, channel_access_token)