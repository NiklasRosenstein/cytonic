# skye-api

Define APIs and generated Pythonic client/server code.

## Quickstart

Check out the [examples/todolist](examples/todolist) folder.

APIs are defined as YAML files:

```yml
name: TodoList
description: A simple todo list API.
authentication: oauth2_bearer
endpoints:
  get_lists:
    http: GET /lists
    return: list[TodoList]
  get_items:
    http: GET /lists/{list_id}/items
    args:
      list_id: string
    return: list[TodoItem]
  set_items:
    http: POST /lists/{list_id}/items
    args:
      list_id: string
      request: list[TodoItem]
types:
  TodoList:
    fields:
      id: string
      name: string
      created_at: datetime
  TodoItem:
    fields:
      text: string
      created_at: datetime
errors:
  TodoListNotFound:
    base: NOT_FOUND
    args:
      list_id: string
```

And can be used to generated Python code:

    $ python -m skye.api todolist-api/src/*.yml --prefix todolist/src --module todolist.generated
    Generated todolist/src/todolist/generated/__init__.py
    Generated todolist/src/todolist/generated/todolist_service.py
    Generated todolist/src/todolist/generated/todolist_types.py

Producing code that like this: (see [examples/todolist/generated/todolist.py](examples/todolist/generated/todolist.py))
