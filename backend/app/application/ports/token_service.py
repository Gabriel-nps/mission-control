from typing import Optional, Protocol

class TokenService(Protocol):
    def create_token(self, subject: str) -> str:
        ...
    def verify_token(self, token: str) -> Optional[str]:
        ...
        