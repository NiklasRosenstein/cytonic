# -*- coding: utf-8 -*-
# Do not edit; this file was automatically generated with skye-api-python.


import abc
import dataclasses
import datetime

from cytonic.description import authentication, endpoint, service
from cytonic.model import OAuth2Bearer
from cytonic.runtime import Credentials, NotFoundError
from todolist.generated.users import User


@dataclasses.dataclass
class TodoListNotFoundError(NotFoundError):
  list_id: str

  def __post_init__(self):
    super().__init__()


@dataclasses.dataclass
class TodoList:
  id: str
  name: str
  owner: User
  created_at: datetime.datetime


@dataclasses.dataclass
class TodoItem:
  text: str
  created_at: datetime.datetime


@service('TodoList')
@authentication(OAuth2Bearer())
class TodoListServiceBlocking(abc.ABC):
  " A simple todo list API. "

  @endpoint("GET /lists")
  @abc.abstractmethod
  def get_lists(self, auth: Credentials) -> list[TodoList]:
    pass

  @endpoint("GET /lists/{list_id}/items")
  @abc.abstractmethod
  def get_items(self, auth: Credentials, list_id: str) -> list[TodoItem]:
    pass

  @endpoint("POST /lists/{list_id}/items")
  @abc.abstractmethod
  def set_items(self, auth: Credentials, list_id: str, items: list[TodoItem]) -> None:
    pass


@service('TodoList')
@authentication(OAuth2Bearer())
class TodoListServiceAsync(abc.ABC):
  " A simple todo list API. "

  @endpoint("GET /lists")
  @abc.abstractmethod
  async def get_lists(self, auth: Credentials) -> list[TodoList]:
    pass

  @endpoint("GET /lists/{list_id}/items")
  @abc.abstractmethod
  async def get_items(self, auth: Credentials, list_id: str) -> list[TodoItem]:
    pass

  @endpoint("POST /lists/{list_id}/items")
  @abc.abstractmethod
  async def set_items(self, auth: Credentials, list_id: str, items: list[TodoItem]) -> None:
    pass
