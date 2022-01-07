
from fastapi import FastAPI

from skye.api.ext.fastapi import SkyeAPIServiceRouter

from .impl import TodoListServiceAsyncImpl, UsersServiceAsyncImpl

users = UsersServiceAsyncImpl()
todolist = TodoListServiceAsyncImpl(users)

app = FastAPI()
app.include_router(SkyeAPIServiceRouter(users))
app.include_router(SkyeAPIServiceRouter(todolist))
