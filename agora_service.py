"""
Agora Service for RTC (Voice) and Chat Integration
"""
import os
import time
import hmac
import hashlib
import base64
import struct
import requests
from typing import Dict, Any, Optional
from config import settings


class AgoraService:
    """
    Complete Agora service handling:
    - RTC token generation for voice calls
    - Chat token generation
    - Chat REST API operations
    - Conversational AI agent management
    """
    
    def __init__(self):
        self.app_id = settings.AGORA_APP_ID
        self.app_certificate = settings.AGORA_APP_CERTIFICATE
        self.chat_app_key = settings.AGORA_CHAT_APP_KEY
        self.chat_rest_api = settings.AGORA_CHAT_REST_API
        self.chat_websocket = settings.AGORA_CHAT_WEBSOCKET
        self._chat_token_cache: Optional[str] = None
        self._chat_token_expiry: float = 0
    
    # ============= RTC TOKEN GENERATION =============
    
    def generate_rtc_token(
        self,
        channel_name: str,
        uid: int = 0,
        role: int = 1,  # 1 = Publisher, 2 = Subscriber
        expiration_seconds: int = 3600
    ) -> str:
        """
        Generate Agora RTC Token using AccessToken2 format
        
        Args:
            channel_name: Channel name for the RTC session
            uid: User ID (0 for any user)
            role: 1 for publisher, 2 for subscriber
            expiration_seconds: Token validity duration
        
        Returns:
            RTC token string
        """
        if not self.app_certificate:
            # Development mode - return placeholder
            return f"dev_token_{channel_name}_{uid}_{int(time.time())}"
        
        return self._build_rtc_token(channel_name, uid, role, expiration_seconds)
    
    def _build_rtc_token(
        self,
        channel_name: str,
        uid: int,
        role: int,
        expiration: int
    ) -> str:
        """Build RTC token using Agora's algorithm"""
        try:
            from agora_token import RtcTokenBuilder, Role_Publisher, Role_Subscriber
            
            current_timestamp = int(time.time())
            privilege_expired_ts = current_timestamp + expiration
            
            agora_role = Role_Publisher if role == 1 else Role_Subscriber
            
            token = RtcTokenBuilder.buildTokenWithUid(
                self.app_id,
                self.app_certificate,
                channel_name,
                uid,
                agora_role,
                privilege_expired_ts
            )
            return token
        except ImportError:
            # Fallback if agora_token not installed
            print("Warning: agora_token package not installed. Using dev token.")
            return f"dev_token_{channel_name}_{uid}"
    
    # ============= CHAT TOKEN GENERATION =============
    
    def generate_chat_token(self, user_id: str, expiration_seconds: int = 86400) -> str:
        """
        Generate Agora Chat user token
        
        Args:
            user_id: Chat user identifier
            expiration_seconds: Token validity (default 24 hours)
        
        Returns:
            Chat token string
        """
        org_name, app_name = self.chat_app_key.split("#")
        
        # Token payload
        current_time = int(time.time())
        expire_time = current_time + expiration_seconds
        
        payload = {
            "org_name": org_name,
            "app_name": app_name,
            "user_name": user_id,
            "expire": expire_time
        }
        
        # Create signature
        signature_base = f"{org_name}/{app_name}/{user_id}:{expire_time}"
        signature = hmac.new(
            self.app_certificate.encode(),
            signature_base.encode(),
            hashlib.sha256
        ).hexdigest()
        
        token = f"{org_name}#{app_name}#{user_id}#{expire_time}#{signature}"
        return base64.b64encode(token.encode()).decode()
    
    # ============= CHAT REST API =============
    
    def get_app_token(self) -> str:
        """Get app-level token for Chat REST API calls"""
        if self._chat_token_cache and time.time() < self._chat_token_expiry:
            return self._chat_token_cache
        
        org_name, app_name = self.chat_app_key.split("#")
        url = f"{self.chat_rest_api}/{org_name}/{app_name}/token"
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.AGORA_CHAT_CLIENT_ID,
            "client_secret": settings.AGORA_CHAT_CLIENT_SECRET
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                self._chat_token_cache = data["access_token"]
                # Cache for 90% of expiration time
                self._chat_token_expiry = time.time() + (data["expires_in"] * 0.9)
                return self._chat_token_cache
        except Exception as e:
            print(f"Error getting app token: {e}")
        
        return ""
    
    def create_chat_user(self, user_id: str, password: str, nickname: str = "") -> Dict:
        """Create a new chat user"""
        org_name, app_name = self.chat_app_key.split("#")
        url = f"{self.chat_rest_api}/{org_name}/{app_name}/users"
        
        app_token = self.get_app_token()
        headers = {
            "Authorization": f"Bearer {app_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "username": user_id,
            "password": password,
            "nickname": nickname or user_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def send_chat_message(
        self,
        from_user: str,
        to_user: str,
        message: str,
        msg_type: str = "txt"
    ) -> Dict:
        """Send a chat message via REST API"""
        org_name, app_name = self.chat_app_key.split("#")
        url = f"{self.chat_rest_api}/{org_name}/{app_name}/messages"
        
        app_token = self.get_app_token()
        headers = {
            "Authorization": f"Bearer {app_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": from_user,
            "to": [to_user],
            "type": msg_type,
            "body": {
                "msg": message
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # ============= CHANNEL MANAGEMENT =============
    
    def generate_channel_name(self, user_id: int, language: str = "general") -> str:
        """Generate deterministic channel name"""
        sanitized_lang = language.lower().replace(" ", "-")
        date_part = time.strftime("%Y%m%d")
        return f"aurora_user-{user_id}_lang-{sanitized_lang}_{date_part}"[:80]
    
    def create_voice_session(self, user_id: int, language: str = "English") -> Dict[str, Any]:
        """
        Create a complete voice tutoring session
        
        Returns:
            {
                "channel_name": str,
                "rtc_token": str,
                "app_id": str,
                "uid": int,
                "chat_token": str,
                "websocket_url": str
            }
        """
        channel_name = self.generate_channel_name(user_id, language)
        rtc_token = self.generate_rtc_token(channel_name, user_id)
        chat_token = self.generate_chat_token(f"user_{user_id}")
        
        return {
            "channel_name": channel_name,
            "rtc_token": rtc_token,
            "app_id": self.app_id,
            "uid": user_id,
            "chat_token": chat_token,
            "websocket_url": self.chat_websocket,
            "language": language
        }
    
    # ============= CONVERSATIONAL AI AGENT =============
    
    def start_ai_agent(
        self,
        channel_name: str,
        language: str = "English",
        voice_config: Optional[Dict] = None
    ) -> Dict:
        """
        Start Agora Conversational AI Agent for voice tutoring
        
        Uses Agora's v2 API: /api/conversational-ai-agent/v2/projects/{appid}/join
        """
        if not settings.OPENAI_API_KEY:
            return {"error": "OpenAI API key not configured"}
        
        url = f"https://api.agora.io/api/conversational-ai-agent/v2/projects/{self.app_id}/join"
        
        # Language-specific prompts
        language_prompts = {
            "Spanish": "You are a helpful Spanish tutor. Help users learn Spanish through conversation. Speak naturally and correct mistakes gently.",
            "French": "You are a helpful French tutor. Help users learn French through conversation. Speak naturally and correct mistakes gently.",
            "Japanese": "You are a helpful Japanese tutor. Help users learn Japanese through conversation. Speak naturally and correct mistakes gently.",
            "English": "You are Aurora, an AI study companion. Help students understand concepts and practice conversation."
        }
        
        payload = {
            "channel": channel_name,
            "agentName": f"Aurora_{language}_Tutor",
            "properties": {
                "llm": {
                    "provider": "openai",
                    "model": "gpt-4-turbo-preview",
                    "api_key": settings.OPENAI_API_KEY,
                    "system_messages": [
                        language_prompts.get(language, language_prompts["English"])
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                "tts": voice_config.get("tts") if voice_config else {
                    "provider": "azure",
                    "params": {
                        "voice_name": "en-US-JennyNeural"
                    }
                },
                "stt": voice_config.get("stt") if voice_config else {
                    "provider": "azure"
                }
            }
        }
        
        try:
            # Note: Requires Agora API credentials
            # In production, add Authorization header with Basic auth
            response = requests.post(url, json=payload)
            return response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            return {"error": str(e)}
