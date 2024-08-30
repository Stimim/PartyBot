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
            '座位查詢': self._lookup_my_seat,
            '婚禮資訊': self._share_wedding_info,
            '上傳照片': self._upload_photo,
            '心情留言': self._leave_a_message,
        }
        self._firestore_client = FirestoreClient('stimim-wedding-bot')
        self._deferred_tasks = set()

    @property
    def _line_bot_api(self):
        if self._line_bot_api_cache is None:
            async_api_client = AsyncApiClient(self._configuration)
            self._line_bot_api_cache = AsyncMessagingApi(async_api_client)
        return self._line_bot_api_cache

    def handle_event(self, event):
        handler = self.__get_handler(event)
        if handler is not None:
            self._defer_task(handler(event))

    def _defer_task(self, future):
        task = asyncio.create_task(future)
        self._deferred_tasks.add(task)
        task.add_done_callback(self._on_task_done)

    def _on_task_done(self, task):
        if e := task.exception():
            logging.error('Task failed: ', exc_info=e)
        self._deferred_tasks.discard(task)

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
        if event.source and event.source.user_id:
            self._firestore_client.write_doc(
                'known_users',
                event.source.user_id,
                {}
            )
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

        image_data = {
            'image_set': event.message.image_set,
            'timestamp': datetime.datetime.now().timestamp(),
        }
        if event.source and event.source.user_id:
            image_data['user_id'] = event.source.user_id
        self._firestore_client.write_doc(
            'image_message',
            event.message.id,
            image_data)

    async def _handle_video_message(self, event: MessageEvent):
        logging.info('_handle_video_message: %r', event.message)
        if event.message.content_provider.type != 'line':
            return
        video_data = {
            'timestamp': datetime.datetime.now().timestamp(),
        }
        if event.source and event.source.user_id:
            video_data['user_id'] = event.source.user_id
        self._firestore_client.write_doc(
            'video_message',
            event.message.id,
            video_data)

    async def _handle_text_message(self, event: MessageEvent):
        text = event.message.text
        if text[0] != '!' and text[0] != '！':
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

    async def _lookup_my_seat(self, event: MessageEvent, cmd: str, params: str):
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

    async def _upload_photo(self, event: MessageEvent, cmd: str, params: str):
        del cmd
        del params
        return await self._line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text=(
                        '感謝您幫忙紀錄我們的婚禮，'
                        '麻煩將照片或影片直接上傳到這個 LINE 對話中')),
                ]
            )
        )

    async def _leave_a_message(self, event: MessageEvent, cmd: str, params: str):
        if not params:
            return await self._line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text='請使用 !心情留言 ... 來留言，例如：'),
                        TextMessage(text='!心情留言 新娘好漂亮!'),
                    ]
                )
            )
        message_data = {
            'text': params,
            'timestamp': datetime.datetime.now().timestamp(),
        }
        if event.source and event.source.user_id:
            message_data['user_id'] = event.source.user_id

        self._firestore_client.write_doc(
            'guestbook',
            event.message.id,
            message_data)
        return await self._line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text='感謝留言!'),
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
            line_bot.handle_event(event)

        return 'OK'


