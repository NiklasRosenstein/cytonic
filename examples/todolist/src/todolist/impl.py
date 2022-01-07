
import datetime

from skye.api.runtime.auth import Credentials, BearerToken
from skye.api.runtime.exceptions import UnauthorizedError

from .generated import TodoItem, TodoList, TodoListNotFoundError, TodoListServiceAsync, UserNotFoundError, User, UsersServiceAsync

_users = {
  'eY123.123': User('0', 'john.wick@example.org'),
}

_users_by_id = {u.id: u for u in _users.values()}

_lists = {
  '0': TodoList('0', 'My todolist', _users_by_id['0'], datetime.datetime.now()),
  '1': TodoList('1', 'Work stuff', _users_by_id['0'], datetime.datetime.now()),
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

  async def get_lists(self, auth: Credentials) -> list[TodoList]:
    await self._users.me(auth)
    return list(_lists.values())

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

  async def get_user(self, auth: Credentials, user_id: str) -> User:
    self.me(auth)
    if user_id not in _users_by_id:
      raise UserNotFoundError(user_id)
    return _users_by_id[user_id]

  async def me(self, auth: Credentials) -> User:
    token = auth.cast(BearerToken)
    if token.value not in _users:
      raise UnauthorizedError('invalid token')
    return _users[token.value]
