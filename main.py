import uvicorn
from application.app import create_app


app = create_app("test")


if __name__ == "__main__":
    uvicorn.run(app="main:app")