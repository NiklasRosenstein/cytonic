
from fastapi import FastAPI

from cytonic.contrib.fastapi import CytonicServiceRouter

from .impl import TodoListServiceAsyncImpl, UsersServiceAsyncImpl

users = UsersServiceAsyncImpl()
todolist = TodoListServiceAsyncImpl(users)

app = FastAPI()
app.include_router(CytonicServiceRouter(users))
app.include_router(CytonicServiceRouter(todolist))
