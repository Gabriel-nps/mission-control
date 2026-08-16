from app.application.ports.token_service import TokenService

class InvalidCredentialsError(Exception):
    pass

class AuthenticateUser:
    def __init__(self, token_service: TokenService):
        self._token_service = token_service
    def execute(self, username: str, password: str) -> str:
        if username != "admin" or password != "mudar@123":
            raise InvalidCredentialsError("Invalid credentials")
        return self._token_service.create_token(subject=username)