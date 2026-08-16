from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt


class JWTService:
    def __init__(self, secret: str, expiration_minutes: int = 60):
        self._secret = secret
        self._expiration_minutes = expiration_minutes

    def create_token(self, subject: str) -> str:
        payload = {
            "sub": subject,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self._expiration_minutes),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
            return payload.get("sub")
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
            return None
