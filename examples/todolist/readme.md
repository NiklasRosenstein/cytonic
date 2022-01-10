# cytonic/examples/todolist

A simple todo list API example using `skye-api`.

To regenerate the API code form the YAML definition, run

    $ cd examples/todolist
    $ skye-api-python api/*.yml --prefix todolist/src --package todolist.generated
    Generated src/todolist/generated/__init__.py
    Generated src/todolist/generated/todolist.py
    Generated src/todolist/generated/users.py

Then to start the example, run

    $ cd examples/todolist
    $ uvicorn todolist.app:app
