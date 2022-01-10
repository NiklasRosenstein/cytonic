# cytonic/examples/todolist

A simple todo list API example using Cytonic.

To regenerate the API code form the YAML definition, run

    $ cytonic-codegen-python $dir/src/cytonic/*.yml --prefix $dir/src/python/ --package todolist.api
    Write src/python/todolist/api/todolist.py
    Write src/python/todolist/api/users.py
    Write src/python/todolist/api/__init__.py

Then to start the example, run

    $ PYTHONPATH=src/python/ uvicorn todolist.app:app
