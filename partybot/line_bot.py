import asyncio
import datetime
import logging

from partybot.line_bot_flex_msg import *

import fastapi
from google.cloud import firestore
from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
    ApiException,
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    FlexMessage,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    ImageMessageContent,
    FollowEvent,
    PostbackEvent,
    MessageEvent,
    TextMessageContent,
    VideoMessageContent,
)

_WEDDING_INFO_ALT_TEXT = '''婚禮資訊
2024/12/08 孫立人將軍官邸
10:30 雞尾酒派對
11:00 戶外證婚
12:18 喜宴開始
'''

class FirestoreClient:
    def __init__(self, project_id):
        self._client = firestore.AsyncClient(project=project_id)
        self._tasks = set()

    def write_doc(self, collection, document, value):
        doc = self._client.collection(collection).document(document)
        task = asyncio.create_task(doc.set(value))
        # Add task to the set. This creates a strong reference.
        self._tasks.add(task)
        # To prevent keeping references to finished tasks forever,
        # make each task remove its own reference from the set after
        # completion:
        task.add_done_callback(self._tasks.discard)


class LineBot:
    def __init__(self, configuration: Configuration):
        self._configuration = configuration
        self._line_bot_api_cache = None
        self._cmds = {
            '座位查詢': self._where_is_my_seat,
            '婚禮資訊': self._share_wedding_info,
        }
        self._firestore_client = FirestoreClient('stimim-wedding-bot')

    @property
    def _line_bot_api(self):
        if self._line_bot_api_cache is None:
            async_api_client = AsyncApiClient(self._configuration)
            self._line_bot_api_cache = AsyncMessagingApi(async_api_client)
        return self._line_bot_api_cache
    
    async def handle_event(self, event):
        handler = self.__get_handler(event)
        if handler is not None:
            return await handler(event)
        
    def __get_handler(self, event):
        match event:
            case MessageEvent():
                match event.message:
                    case ImageMessageContent():
                        return self._handle_image_message
                    case TextMessageContent():
                        return self._handle_text_message
                    case VideoMessageContent():
                        return self._handle_video_message
            case FollowEvent():
                return self._handle_follow_event
            case PostbackEvent():
                pass
        return None
    
    async def _handle_follow_event(self, event: MessageEvent):
        await self._line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    FlexMessage.from_dict({
                        'type': 'flex',
                        'altText': '感謝將我們的機器人加入好友！',
                        'contents': FLEX_MSG_GREETING,
                    })
                ]
            )
        )

    async def _handle_image_message(self, event: MessageEvent):
        logging.info('_handle_image_message: %r', event.message)
        if event.message.content_provider.type != 'line':
            return
        self._firestore_client.write_doc(
            'image_message',
            event.message.id,
            {
                'image_set': event.message.image_set,
                'timestamp': datetime.datetime.now().timestamp(),
            })

    async def _handle_video_message(self, event: MessageEvent):
        logging.info('_handle_video_message: %r', event.message)
        if event.message.content_provider.type != 'line':
            return
        self._firestore_client.write_doc(
            'video_message',
            event.message.id,
            {
                'timestamp': datetime.datetime.now().timestamp(),
            })

    async def _handle_text_message(self, event: MessageEvent):
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
                        'altText': _WEDDING_INFO_ALT_TEXT,
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


