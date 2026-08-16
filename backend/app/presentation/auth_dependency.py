from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.ports.token_service import TokenService

security_scheme = HTTPBearer()

def create_auth_dependency(token_service: TokenService):
    """Factory that creates the auth dependency with the token service injected."""
    
    def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    ) -> str:
        token = credentials.credentials
        subject = token_service.verify_token(token)
        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return subject
    
    return get_current_user
