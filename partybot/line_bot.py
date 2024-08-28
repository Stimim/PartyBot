import logging
import fastapi

from linebot.v3.webhook import WebhookParser, WebhookHandler
from linebot.v3.messaging import (
    ApiException,
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    FlexMessage,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

# https://github.com/line/line-bot-sdk-python/blob/master/examples/flask-kitchensink/app.py
WEDDING_INFO_ALT_TEXT = '''婚禮資訊
2024/12/08 孫立人將軍官邸
10:30 雞尾酒派對
11:00 戶外證婚
12:18 喜宴開始
'''

FLEX_MSG_WEDDING_INFO = {
  "type": "bubble",
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "日期",
            "flex": 1
          },
          {
            "type": "text",
            "text": "📅 2024/12/08 (日)",
            "flex": 2
          }
        ]
      },
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "地點",
            "flex": 1,
          },
          {
            "type": "text",
            "text": "📍 孫立人將軍官邸",
            "flex": 2,
          }
        ]
      },
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "時間",
            "flex": 1
          },
          {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "text",
                "text": "🍸 10:30 雞尾酒派對",
              },
              {
                "type": "text",
                "text": "💍 11:00 戶外證婚",
              },
              {
                "type": "text",
                "text": "🍽️ 12:18 喜宴開始",
              }
            ],
            "flex": 2,
          }
        ]
      },
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "button",
            "action": {
              "type": "uri",
              "label": "邀請函",
              "uri": "https://forms.gle/pbjZzYWJsP6EfHEe9"
            }
          },
          {
            "type": "button",
            "action": {
              "type": "uri",
              "label": "地圖",
              "uri": "https://maps.app.goo.gl/nB27agtpkfzGtzwT9"
            }
          }
        ]
      }
    ],
    "spacing": "xl"
  }
}


class LineBot:
    def __init__(self, configuration: Configuration):
        self._configuration = configuration
        self._line_bot_api_cache = None
        self._cmds = {
            '座位查詢': self._where_is_my_seat,
            '婚禮資訊': self._share_wedding_info,
        }

    @property
    def _line_bot_api(self):
        if self._line_bot_api_cache is None:
            async_api_client = AsyncApiClient(self._configuration)
            self._line_bot_api_cache = AsyncMessagingApi(async_api_client)
        return self._line_bot_api_cache

    async def handle_event(self, event):
        match event:
            case MessageEvent():
                match event.message:
                    case TextMessageContent():
                        return await self.handle_text_message(event)

    async def handle_text_message(self, event: MessageEvent):
        text = event.message.text
        if text[0] != '!':
            return

        cmd, _, params = text.partition(' ')
        cmd = cmd[1:]

        if cmd in self._cmds:
            return await self._cmds[cmd](event, cmd, params)

        await self._line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f'{cmd=} {params=}')]
            )
        )

    async def _share_wedding_info(self, event: MessageEvent, cmd: str, params: str):
        del cmd
        del params
        return await self._line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    FlexMessage.from_dict({
                        'type': 'flex',
                        'altText': WEDDING_INFO_ALT_TEXT,
                        'contents': FLEX_MSG_WEDDING_INFO
                    })
                ]
            )
        )

    async def _where_is_my_seat(self, event: MessageEvent, cmd: str, params: str):
        if not params:
            return await self._line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text=f'座位表製作中，敬請期待......'),
                        # TextMessage(text=f'使用 !{cmd} 姓名 查詢你的座位'),
                    ]
                )
            )

        name = params
        return await self._line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text=f'{name} 座位表製作中，敬請期待.....'),
                ]
            )
        )


def setup(app: fastapi.FastAPI, channel_secret: str, channel_access_token: str):
    configuration = Configuration(
        access_token=channel_access_token
    )
    # TODO: to use gunicorn, we need to get the async loop set up by UvicornWorker.
    parser = WebhookParser(channel_secret)
    line_bot = LineBot(configuration)

    @app.post("/linebot/webhook")
    async def handle_callback(request: fastapi.Request):
        signature = request.headers['X-Line-Signature']

        # get request body as text
        body = await request.body()
        body = body.decode()

        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            raise fastapi.HTTPException(status_code=400, detail="Invalid signature")

        for event in events:
            await line_bot.handle_event(event)

        return 'OK'


