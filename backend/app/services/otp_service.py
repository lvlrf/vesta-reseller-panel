# backend/app/services/otp_service.py
import redis
import json
from datetime import timedelta
from typing import Optional

from app.core.config import settings
from app.core.security import generate_otp

class OTPService:
    def __init__(self):
        # Use Redis for OTP storage in production, dict for development
        self.redis_client = None
        try:
            if settings.REDIS_HOST:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=int(settings.REDIS_PORT),
                    decode_responses=True
                )
        except:
            pass
        
        # Fallback storage (not for production)
        self.temp_storage = {}
    
    def save_otp(self, mobile: str, otp: str, expires_in: int = 300) -> bool:
        """Save OTP with expiration (5 minutes default)"""
        key = f"otp:{mobile}"
        
        if self.redis_client:
            try:
                return self.redis_client.setex(
                    key, expires_in, otp
                )
            except:
                pass
        
        # Fallback storage
        import time
        self.temp_storage[key] = {
            "otp": otp,
            "expires_at": time.time() + expires_in
        }
        return True
    
    def verify_otp(self, mobile: str, otp: str) -> bool:
        """Verify OTP and remove it"""
        key = f"otp:{mobile}"
        
        if self.redis_client:
            try:
                stored_otp = self.redis_client.get(key)
                if stored_otp and stored_otp == otp:
                    self.redis_client.delete(key)
                    return True
                return False
            except:
                pass
        
        # Fallback storage
        import time
        if key in self.temp_storage:
            stored = self.temp_storage[key]
            if stored["expires_at"] > time.time() and stored["otp"] == otp:
                del self.temp_storage[key]
                return True
            elif stored["expires_at"] <= time.time():
                del self.temp_storage[key]
        
        return False
