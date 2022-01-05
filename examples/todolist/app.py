
from fastapi import FastAPI
from skye.api.server.fastapi import SkyeAPIRouter
from .impl.todolist import TodoListServiceAsyncImpl

app = FastAPI()
app.include_router(SkyeAPIRouter(TodoListServiceAsyncImpl))
