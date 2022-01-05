
import dataclasses
import datetime
from skye.api.runtime import authentication, endpoint
from skye.api.runtime.exceptions import NotFoundError


@dataclasses.dataclass(frozen=True)
class TodoListNotFoundError(NotFoundError):
  ERROR_NAME = 'TodoList:TodoListNotFound'
  list_id: str


@dataclasses.dataclass
class TodoList:
  id: str
  name: str
  created_at: datetime.datetime


@dataclasses.dataclass
class TodoItem:
  text: str
  created_at: datetime.datetime


@authentication('oauth2_bearer')
class TodoListServiceAsync:

  @endpoint('GET /lists')
  async def get_lists(self) -> list[TodoList]:
    raise NotImplementedError('TodolistServerAsync.get_lists()')

  @endpoint('GET /lists/{list_id}/items')
  async def get_items(self, list_id: str) -> list[TodoItem]:
    raise NotImplementedError('TodolistServerAsync.get_items()')

  @endpoint('POST /lists/{list_id}/items')
  async def set_items(self, list_id: str, items: list[TodoItem]) -> None:
    raise NotImplementedError('TodolistServerAsync.get_items()')


@authentication('oauth2_bearer')
class TodoListServiceBlocking:

  @endpoint('GET /lists')
  def get_lists(self) -> list[TodoList]:
    raise NotImplementedError('TodolistServerAsync.get_lists()')

  @endpoint('GET /lists/{list_id}/items')
  def get_items(self, list_id: str) -> list[TodoItem]:
    raise NotImplementedError('TodolistServerAsync.get_items()')

  @endpoint('POST /lists/{list_id}/items')
  def set_items(self, list_id: str, items: list[TodoItem]) -> None:
    raise NotImplementedError('TodolistServerAsync.get_items()')
