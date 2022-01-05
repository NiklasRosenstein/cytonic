
import datetime

from skye.api.runtime import ServerMixin
from ..generated.todolist import TodoListServiceAsync, TodoListNotFoundError, TodoList, TodoItem


class TodoListServiceAsyncImpl(TodoListServiceAsync, ServerMixin):

  _lists = {
    '0': TodoList('0', 'My todolist', datetime.datetime.now()),
  }

  _items = {
    '0': [
      TodoItem('Take out trash', datetime.datetime.now()),
      TodoItem('Do stuff', datetime.datetime.now()),
    ]
  }

  async def get_lists(self) -> list[TodoList]:
    return list(self._lists.valus())

  async def get_items(self, list_id: str) -> list[TodoItem]:
    if list_id in self._lists:
      return self._items[list_id]
    raise TodoListNotFoundError(list_id)

  async def set_items(self, list_id: str, items: list[TodoItem]) -> None:
    if list_id in self._lists:
      self._items[list_id] = items
      return
    raise TodoListNotFoundError(list_id)
