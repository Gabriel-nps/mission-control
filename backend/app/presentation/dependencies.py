import os

from app.infrastructure.repositories.in_memory_mission_repository import InMemoryMissionRepository
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.kafka.producer import KafkaEventPublisher
from app.application.use_cases.authenticate_user import AuthenticateUser
from app.application.use_cases.create_mission import CreateMission
from app.application.use_cases.get_mission import GetMission
from app.application.use_cases.list_missions import ListMissions
from app.presentation.auth_dependency import create_auth_dependency

# Configuração via ambiente, com defaults voltados ao desenvolvimento local.
# Em produção, JWT_SECRET deve ser sempre definido por variável de ambiente.
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-insecure-secret")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

_mission_repository = InMemoryMissionRepository()
_token_service = JWTService(secret=JWT_SECRET)
_event_publisher = KafkaEventPublisher(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

get_current_user = create_auth_dependency(_token_service)

def get_authenticate_user() -> AuthenticateUser:
    return AuthenticateUser(token_service=_token_service)

def get_create_mission() -> CreateMission:
    return CreateMission(repository=_mission_repository, publisher=_event_publisher)

def get_get_mission() -> GetMission:
    return GetMission(repository=_mission_repository)

def get_list_missions() -> ListMissions:
    return ListMissions(repository=_mission_repository)
