# appfire-api-spec

Define APIs and generated Pythonic client/server code.

## Quickstart

APIs are defined as YAML files:

```yml
name: todolist
description: A simple todo list API.
authentication: oauth2_bearer
endpoints:
  get_lists:
    http: GET /lists
    return: list[TodoList]
  get_items:
    http: GET /lists/{list_name}/items
    args:
      list_name: string
    return: list[TodoItem]
  set_items:
    http: POST /lists/{list_name}/items
    args:
      list_name: string
      request: list[TodoItem]
types:
  TodoList:
    fields:
      name: string
      created_at: datetime
  TodoItem:
    fields:
      text: string
      created_at: datetime
```

And can be used to generated Python code:

    $ python -m appfire.api.spec todolist-api/src/*.yml --prefix todolist/src --package todolist.generated
    Generated todolist/src/todolist/generated/__init__.py
    Generated todolist/src/todolist/generated/todolist_service.py
    Generated todolist/src/todolist/generated/todolist_types.py

Producing code that like this:

```py
# todolist_service.py
from appfire.api.spec.runtime import authentication, endpoint
from todolist.generated.todolist_types import TodoList, TodoItem


@authentication('oauth2_bearer')
class TodolistServiceAsync:

  @endpoint('GET /lists')
  async def get_list(self) -> list[TodoList]:
    raise NotImplementedError('TodolistServerAsync.get_list()')

  @endpoint('GET /lists/{list_name}/items')
  async def get_items(self, list_name: str) -> list[TodoItem]:
    raise NotImplementedError('TodolistServerAsync.get_items()')

  @endpoint('POST /lists/{list_name}/items')
  async def set_items(self, list_name: str, items: list[TodoItem]) -> None:
    raise NotImplementedError('TodolistServerAsync.get_items()')


@authentication('oauth2_bearer')
class TodolistServiceBlocking:

  @endpoint('GET /lists')
  def get_list(self) -> list[TodoList]:
    raise NotImplementedError('TodolistServerAsync.get_list()')

  @endpoint('GET /lists/{list_name}/items')
  def get_items(self, list_name: str) -> list[TodoItem]:
    raise NotImplementedError('TodolistServerAsync.get_items()')

  @endpoint('POST /lists/{list_name}/items')
  def set_items(self, list_name: str, items: list[TodoItem]) -> None:
    raise NotImplementedError('TodolistServerAsync.get_items()')
```

```py
# todolist_types.py
import dataclasses
import datetime


@dataclasses.dataclass
class TodoList:
  name: str
  created_at: datetime.datetime


@dataclasses.dataclass
class TodoItem:
  text: str
  created_at: datetime.datetime
```
