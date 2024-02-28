class Config:
    """Base configuration"""


class ProdConfig(Config):
    """Base configuration"""


class DevConfig(Config):
    """Base configuration"""


class TestConfig(Config):
    """Base configuration"""

    TESTING = True


def get_config(name: str) -> Config:
    if name == "prod":
        return ProdConfig()
    if name == "dev":
        return DevConfig()
    if name == "test":
        return TestConfig()
    raise Exception(f"Invalid Config Name: {name}")