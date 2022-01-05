
import datetime
import typing as t

from starlette.requests import Request
from starlette.responses import Response

from skye.api.runtime import HandlerMixin, Authorization, BearerToken
from skye.api.runtime.exceptions import UnauthorizedError
from ..generated.todolist import TodoListServiceAsync, TodoListNotFoundError, TodoList, TodoItem

_users = {
  'eY123.123': 'John Wick',
}

_lists = {
  '0': TodoList('0', 'My todolist', datetime.datetime.now()),
}

_items = {
  '0': [
    TodoItem('Take out trash', datetime.datetime.now()),
    TodoItem('Do stuff', datetime.datetime.now()),
  ]
}


class TodoListServiceAsyncImpl(TodoListServiceAsync, HandlerMixin):

  async def before_request(self, request: Request, authorization: Authorization | None) -> Response | None:
    assert authorization
    token = authorization.cast(BearerToken)
    if token.value not in _users:
      raise UnauthorizedError()
    self.user = _users[token.value]
    return None

  async def get_lists(self, reversed_: bool) -> list[TodoList]:
    result = list(_lists.values())
    if reversed_:
      result.reverse()
    return result

  async def get_items(self, list_id: str) -> list[TodoItem]:
    if list_id in _lists:
      return _items[list_id] + [TodoItem(self.user, datetime.datetime.now())]
    raise TodoListNotFoundError(list_id)

  async def set_items(self, list_id: str, items: list[TodoItem]) -> None:
    if list_id in _lists:
      _items[list_id] = items
      return
    raise TodoListNotFoundError(list_id)
