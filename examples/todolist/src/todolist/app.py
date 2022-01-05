
from fastapi import FastAPI

from skye.api.server.fastapi import SkyeAPIRouter

from .impl import TodoListServiceAsyncImpl, UsersServiceAsyncImpl

users = UsersServiceAsyncImpl()
todolist = TodoListServiceAsyncImpl(users)

app = FastAPI()
app.include_router(SkyeAPIRouter(users))
app.include_router(SkyeAPIRouter(todolist))
