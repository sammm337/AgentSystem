from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://mongo:27017"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    VECTORDB: str = "qdrant"  # or chroma
    QDRANT_URL: str = "http://qdrant:6333"
    OLLAMA_URL: str = "http://host.docker.internal:11434"
    WHISPER_BIN: str = "/usr/local/bin/whisper"
    DB_NAME: str = "hyperlocal"

    class Config:
        env_file = ".env"

settings = Settings()
