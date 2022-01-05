
import dataclasses
import datetime

from skye.api.runtime import authentication, endpoint, query, service, Credentials
from skye.api.runtime.exceptions import NotFoundError


@dataclasses.dataclass
class TodoListNotFoundError(NotFoundError):
  ERROR_NAME = 'TodoList:TodoListNotFound'
  list_id: str

  def __post_init__(self) -> None:
    super().__init__()


@dataclasses.dataclass
class TodoList:
  id: str
  name: str
  created_at: datetime.datetime


@dataclasses.dataclass
class TodoItem:
  text: str
  created_at: datetime.datetime


@service('TodoList')
@authentication('oauth2_bearer')
class TodoListServiceAsync:

  @endpoint('GET /lists', args=dict(reversed_=query(name='reversed')))
  async def get_lists(self, auth: Credentials, reversed_: bool) -> list[TodoList]:
    raise NotImplementedError('TodolistServerAsync.get_lists()')

  @endpoint('GET /lists/{list_id}/items')
  async def get_items(self, auth: Credentials, list_id: str) -> list[TodoItem]:
    raise NotImplementedError('TodolistServerAsync.get_items()')

  @endpoint('POST /lists/{list_id}/items')
  async def set_items(self, auth: Credentials, list_id: str, items: list[TodoItem]) -> None:
    raise NotImplementedError('TodolistServerAsync.get_items()')
