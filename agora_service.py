from agora_token_builder import RtcTokenBuilder
from config import settings
import time
import random
import string

class AgoraService:
    @staticmethod
    def generate_token(channel_name: str, uid: int = 0) -> dict:
        expiration_time = 3600  # 1 hour
        current_timestamp = int(time.time())
        privilege_expired_ts = current_timestamp + expiration_time
        
        token = RtcTokenBuilder.buildTokenWithUid(
            settings.AGORA_APP_ID,
            settings.AGORA_APP_CERTIFICATE,
            channel_name,
            uid,
            1,  # Role: Publisher
            privilege_expired_ts
        )
        
        return {
            "token": token,
            "channel_name": channel_name,
            "uid": uid,
            "app_id": settings.AGORA_APP_ID,
            "expiration": privilege_expired_ts
        }
    
    @staticmethod
    def generate_channel_name(user_id: int, language: str) -> str:
        random_suffix = ''.join(random.choices(
            string.ascii_lowercase + string.digits, k=8
        ))
        return f"aurora_{language}_{user_id}_{random_suffix}"
