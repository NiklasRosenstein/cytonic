# skye-api/examples/todolist

A simple todo list API example using `skye-api`.

To regenerate the API code form the YAML definition, run

    $ cd examples/todolist
    $ python -m skye.api api/*.yml --prefix todolist/src --module todolist.generated
    Generated todolist/src/todolist/generated/__init__.py
    Generated todolist/src/todolist/generated/todolist_service.py
    Generated todolist/src/todolist/generated/todolist_types.py

Then to start the example, run

    $ cd examples/todolist
    $ uvicorn todolist.app:app
