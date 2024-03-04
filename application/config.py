import os

class Config:
    """Base configuration"""


class ProdConfig(Config):
    """Production configuration"""


class DevConfig(Config):
    """Development configuration"""
    # POSTGRES_HOST: str = "localhost"
    # POSTGRES_PORT: int = 5433
    # POSTGRES_USER: str = "postgres"
    # POSTGRES_PASSWORD: str = "postgres"
    # POSTGRES_APPLICATION_DB: str = "test"


class TestConfig(Config):
    """Test configuration"""

    TESTING = True

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_APPLICATION_DB: str = "test"

    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_USER: str = "mongo"
    MONGO_PASSWORD: str = "mongo"
    MONGO_APPLICATION_DB: str = "test"


def get_config(name: str) -> Config:
    if name == "prod":
        return ProdConfig()
    if name == "dev":
        return DevConfig()
    if name == "test":
        return TestConfig()
    raise Exception(f"Invalid Config Name: {name}")