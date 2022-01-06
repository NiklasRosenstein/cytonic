
import datetime

from skye.api.runtime.auth import Credentials, BearerToken
from skye.api.runtime.exceptions import UnauthorizedError

from .generated import TodoItem, TodoList, TodoListNotFoundError, TodoListServiceAsync, UserNotFound, User, UsersServiceAsync

_users = {
  'eY123.123': User('0', 'john.wick@example.org'),
}

_users_by_id = {u.id: u for u in _users.values()}

_lists = {
  '0': TodoList('0', 'My todolist', datetime.datetime.now()),
  '1': TodoList('1', 'Work stuff', datetime.datetime.now()),
}

_items: dict[str, list[TodoItem]] = {
  '0': [
    TodoItem('Take out trash', datetime.datetime.now()),
    TodoItem('Do stuff', datetime.datetime.now()),
  ],
  '1': []
}


class TodoListServiceAsyncImpl(TodoListServiceAsync):

  def __init__(self, users: UsersServiceAsync) -> None:
    self._users = users

  async def get_lists(self, auth: Credentials, reversed_: bool) -> list[TodoList]:
    await self._users.me(auth)
    result = list(_lists.values())
    if reversed_:
      result.reverse()
    return result

  async def get_items(self, auth: Credentials, list_id: str) -> list[TodoItem]:
    await self._users.me(auth)
    if list_id in _lists:
      return _items[list_id]
    raise TodoListNotFoundError(list_id)

  async def set_items(self, auth: Credentials, list_id: str, items: list[TodoItem]) -> None:
    await self._users.me(auth)
    if list_id in _lists:
      _items[list_id] = items
      return
    raise TodoListNotFoundError(list_id)


class UsersServiceAsyncImpl(UsersServiceAsync):

  async def get_user(self, auth: Credentials, id_: str) -> User:
    self.me(auth)
    if id_ not in _users_by_id:
      raise UserNotFound(id_)
    return _users_by_id[id_]

  async def me(self, auth: Credentials) -> User:
    token = auth.cast(BearerToken)
    if token.value not in _users:
      raise UnauthorizedError('invalid token')
    return _users[token.value]
