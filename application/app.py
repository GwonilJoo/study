from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_config, Config
from .endpoint import room_router


class App(FastAPI):
    def __init__(self, config: Config):
        super().__init__()
        self._config = config
        
        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.include_router(room_router, tags=["Room"])


def create_app(config_name: str) -> FastAPI:
    config = get_config(config_name)
    app = App(config)
    return app