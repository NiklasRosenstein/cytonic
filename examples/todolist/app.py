
from fastapi import FastAPI

from skye.api.server.fastapi import SkyeAPIRouter

from .impl import TodoListServiceAsyncImpl

app = FastAPI()
app.include_router(SkyeAPIRouter(TodoListServiceAsyncImpl))
