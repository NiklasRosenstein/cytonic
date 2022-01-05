
import datetime

from skye.api.runtime import Credentials, BearerToken
from skye.api.runtime.exceptions import UnauthorizedError

from .generated import TodoItem, TodoList, TodoListNotFoundError, TodoListServiceAsync

_users = {
  'eY123.123': 'John Wick',
}

_lists = {
  '0': TodoList('0', 'My todolist', datetime.datetime.now()),
  '1': TodoList('1', 'Work stuff', datetime.datetime.now()),
}

_items = {
  '0': [
    TodoItem('Take out trash', datetime.datetime.now()),
    TodoItem('Do stuff', datetime.datetime.now()),
  ],
  '1': []
}


class TodoListServiceAsyncImpl(TodoListServiceAsync):

  def validate_user(self, auth: Credentials) -> str:
    token = auth.cast(BearerToken)
    if token.value not in _users:
      raise UnauthorizedError('invalid token')
    return _users[token.value]

  async def get_lists(self, auth: Credentials, reversed_: bool) -> list[TodoList]:
    self.validate_user(auth)
    result = list(_lists.values())
    if reversed_:
      result.reverse()
    return result

  async def get_items(self, auth: Credentials, list_id: str) -> list[TodoItem]:
    self.validate_user(auth)
    if list_id in _lists:
      return _items[list_id] + [TodoItem(self.user, datetime.datetime.now())]
    raise TodoListNotFoundError(list_id)

  async def set_items(self, auth: Credentials, list_id: str, items: list[TodoItem]) -> None:
    self.validate_user(auth)
    if list_id in _lists:
      _items[list_id] = items
      return
    raise TodoListNotFoundError(list_id)
