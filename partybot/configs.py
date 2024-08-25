import os

from google.cloud import secretmanager

class PartyBotConfig:
    def __init__(self):
        self._load()

    def _load(self):
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'stimim-wedding-bot')
        client = secretmanager.SecretManagerServiceClient()

        def load_secret(secret_name: str):
            path = client.secret_version_path(project_id, secret_name, 'latest')
            response = client.access_secret_version(request={'name': path})
            return response.payload.data.decode('utf-8')

        self._linebot_secret = load_secret('linebot_channel_secret')
        self._linebot_access_token = load_secret('linebot_channel_access_token')

    @property
    def linebot_secret(self):
        return self._linebot_secret
    
    @property
    def linebot_access_token(self):
        return self._linebot_access_token