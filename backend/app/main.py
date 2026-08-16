from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.kafka.consumer import KafkaStatusConsumer
from app.infrastructure.repositories.in_memory_mission_repository import InMemoryMissionRepository
from app.presentation.api.auth import router as auth_router
from app.presentation.api.missions import router as missions_router
from app.presentation.dependencies import KAFKA_BOOTSTRAP_SERVERS, _mission_repository

kafka_consumer = KafkaStatusConsumer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    repository=_mission_repository,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: inicia o consumer Kafka em background
    kafka_consumer.start()
    yield
    # Shutdown: para o consumer
    kafka_consumer.stop()
    

app = FastAPI(title="Kafka Mission Control", lifespan=lifespan)

# CORS (permite o frontend Angular acessar a API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(missions_router)