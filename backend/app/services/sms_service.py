pythonimport httpx
from typing import Optional

from app.core.config import settings


class SMSService:
    async def send_otp(self, mobile: str, otp: str) -> bool:
        """
        Send OTP code via SMS
        """
        if not settings.SMS_API_URL or not settings.SMS_API_KEY:
            # SMS service not configured
            print(f"SMS service not configured. Would send OTP {otp} to {mobile}")
            return True
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.SMS_API_URL,
                    headers={"Authorization": f"Bearer {settings.SMS_API_KEY}"},
                    json={
                        "to": mobile,
                        "text": f"Your verification code is: {otp}"
                    }
                )
                
                return response.status_code == 200
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return False