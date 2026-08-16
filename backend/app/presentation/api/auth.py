from fastapi import APIRouter, Depends, HTTPException, status

from app.application.use_cases.authenticate_user import AuthenticateUser, InvalidCredentialsError
from app.presentation.schemas.auth import LoginRequest, LoginResponse
from app.presentation.dependencies import get_authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    use_case: AuthenticateUser = Depends(get_authenticate_user)
):
    try:
        token = use_case.execute(request.username, request.password)
        return LoginResponse(access_token=token)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
