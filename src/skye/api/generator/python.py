
import abc
import argparse
import builtins
import dataclasses
import re
import textwrap
import typing as t
from pathlib import Path

from ..model import AuthenticationConfig, EndpointConfig, ErrorConfig, ModuleConfig, Project, TypeConfig


def _format_docstrings(level: int, indent: str, docs: str, width: int = 119) -> str:
  width -= level * len(indent)
  prefix = level * indent
  lines = list(textwrap.wrap(docs, width))
  if len(lines) == 1 and len(lines[0]) < (width - 2):
    line = lines[0].replace(r"\"", r"\\\"")
    return f'{prefix}" {line} "'
  else:
    return '\n'.join([f'{prefix}"""'] + [prefix + l for l in lines] + [f'{prefix}"""'])


class _Rendererable(abc.ABC):
  @abc.abstractmethod
  def render(self, level: int, indent: str, fp: t.TextIO) -> None:
    ...


@dataclasses.dataclass
class _PythonModule(_Rendererable):
  coding: str | None = None
  docs: str | None = None
  module_imports: set[str] = dataclasses.field(default_factory=set)
  member_imports: set[str] = dataclasses.field(default_factory=set)
  members: list[_Rendererable] = dataclasses.field(default_factory=list)

  def render(self, level: int, indent: str, fp: t.TextIO) -> None:
    if self.coding:
      fp.write(f'# -*- coding: {self.coding} -*-\n')
    fp.write('# Do not edit; this file was automatically generated with skye-api-python.\n\n')
    _DocstringBlock(self.docs).render(level, indent, fp)
    if self.module_imports:
      fp.write('\n')
      for name in sorted(self.module_imports):
        fp.write(f'import {name}\n')
    if self.member_imports:
      fp.write('\n')
      for name in sorted(self.member_imports):
        assert '.' in name, repr(name)
        from_, part = name.rpartition('.')[::2]
        fp.write(f'from {from_} import {part}\n')
    if self.members:
      for member in self.members:
        fp.write('\n')
        fp.write('\n')
        member.render(level, indent, fp)


@dataclasses.dataclass
class _DocstringBlock(_Rendererable):
  docs: str | None

  def render(self, level: int, indent: str, fp: t.TextIO) -> None:
    if self.docs:
      fp.write(_format_docstrings(level, indent, self.docs))


@dataclasses.dataclass
class _PythonFunction(_Rendererable):
  name: str
  args: list[str]
  body: list[str]
  return_type: str | None = None
  docs: str | None = None
  decorators: list[str] = dataclasses.field(default_factory=list)
  async_: bool = False

  def render(self, level: int, indent: str, fp: t.TextIO) -> None:
    prefix = level * indent
    for decorator in self.decorators:
      fp.write(prefix + decorator + '\n')
    fp.write(prefix)
    if self.async_:
      fp.write('async ')
    fp.write(f'def {self.name}({", ".join(self.args)})')
    if self.return_type:
      fp.write(f' -> {self.return_type}')
    fp.write(':\n')
    _DocstringBlock(self.docs).render(level + 1, indent, fp)
    for line in self.body:
      fp.write(f'{prefix}{indent}{line}')
    fp.write('\n')


@dataclasses.dataclass
class _PythonClassField(_Rendererable):
  name: str
  type_hint: str | None
  value: str | None
  docs: str | None

  def render(self, level: int, indent: str, fp: t.TextIO) -> None:
    prefix = level * indent
    fp.write(f'{prefix}{self.name}')
    if self.type_hint:
      fp.write(f': {self.type_hint}')
    if self.value:
      fp.write(f' = {self.value}')
    fp.write('\n')
    _DocstringBlock(self.docs).render(level, indent, fp)


@dataclasses.dataclass
class _PythonClass(_Rendererable):
  name: str
  docs: str | None = None
  decorators: list[str] = dataclasses.field(default_factory=list)
  bases: list[str] = dataclasses.field(default_factory=list)
  fields: list[_PythonClassField] = dataclasses.field(default_factory=list)
  members: list[_Rendererable] = dataclasses.field(default_factory=list)

  def render(self, level: int, indent: str, fp: t.TextIO) -> None:
    prefix1 = (level + 0) * indent
    for decorator in self.decorators:
      fp.write(prefix1 + decorator + '\n')
    fp.write(f'{prefix1}class {self.name}')
    if self.bases:
      fp.write(f'({", ".join(self.bases)})')
    fp.write(':\n')
    _DocstringBlock(self.docs).render(level + 1, indent, fp)
    if self.fields:
      if self.docs:
        fp.write('\n')
      for field in self.fields:
        field.render(level + 1, indent, fp)
    if self.members:
      if self.docs or self.fields:
        fp.write('\n')
      for member in self.members:
        fp.write('\n')
        member.render(level + 1, indent, fp)


@dataclasses.dataclass
class PythonGenerator:
  """ A class to render Python code from a Skye-API definition. """

  prefix: Path | str
  modules: dict[str, list[ModuleConfig]] = dataclasses.field(default_factory=dict)

  BUILTIN_TYPES = {
    'string': 'str',
    'integer': 'int',
    'float': 'float',
    'double': 'float',
    'boolean': 'bool',
    'datetime': 'datetime.datetime',
    'decimal': 'decimal.Decimal',
  }

  PARAMETRIZED_TYPES = {
    'list': 'list[?]',
    'set': 'set[?]',
    'map': 'dict[?, ?]',
    'optional': '? | None',
  }

  BUILTIN_NAMES = dir(builtins) + ['request', 'auth']

  def write(self, stdout: bool = False, indent: str = '  ') -> None:
    """ Writes the contents of one or more modules into a Python module with the specified name. """

    import sys
    for name, value in self.modules.items():
      filename = Path(self.prefix) / (name.replace('.', '/') + '.py')
      self._current = name  # TODO (@nrosenstein): Dirty hack to check the current module in get_field_type()
      module = self._build_python_module(value)
      if stdout:
        print('#', filename)
        module.render(0, indent, sys.stdout)
      else:
        print('Write', filename)
        with filename.open('w') as fp:
          module.render(0, '  ', fp)

  def _build_python_module(self, modules: list[ModuleConfig]) -> _PythonModule:
    python_module = _PythonModule(coding='utf-8')
    python_module.module_imports.add('dataclasses')
    python_module.member_imports.add('skye.api.runtime.service.service')

    for module in modules:
      for error_name, error in module.errors.items():
        self.add_error_type(error_name, error, python_module)
      for type_name, type_ in module.types.items():
        self.add_type(type_name, type_, python_module)

      python_module.members.append(_PythonClass(
        name=f'{module.name}ServiceAsync',
        docs=module.docs,
        decorators=[f'@service({module.name!r})'] + self.get_auth_decorators(module.auth, python_module),
        members=[self.get_endpoint_definition(k, e, module.auth, python_module) for k, e in module.endpoints.items()]
      ))

    return python_module

  def _make_python_class(self, name: str, config: ErrorConfig | TypeConfig, module: _PythonModule) -> _PythonClass:
    return _PythonClass(
      name=name,
      docs=config.docs,
      decorators=['@dataclasses.dataclass'],
      fields=[
        _PythonClassField(k, self.get_field_type(f.type, module), None, f.docs) for k, f in config.fields.items()
      ] if config.fields else []
    )

  def add_error_type(self, name: str, error: ErrorConfig, module: _PythonModule) -> None:
    class_ = self._make_python_class(name + 'Error', error, module)
    class_.members.append(_PythonFunction('__post_init__', ['self'], body=['super().__init__()']))
    class_.bases.append(self.get_error_base_type(error.error_code, module))
    module.members.append(class_)

  def add_type(self, name: str, type_: TypeConfig, module: _PythonModule) -> None:
    module.members.append(self._make_python_class(name, type_, module))

  def get_error_base_type(self, error_code: str, module: _PythonModule) -> str:
    if error_code == 'NOT_FOUND':
      module.member_imports.add('skye.api.runtime.exceptions.NotFoundError')
      return 'NotFoundError'
    elif error_code == 'UNAUTHORIZED':
      module.member_imports.add('skye.api.runtime.exceptions.UnauthorizedError')
      return 'UnauthorizedError'
    elif error_code == 'CONFLICT':
      module.member_imports.add('skye.api.runtime.exceptions.ConflictError')
      return 'ConflictError'
    else:
      raise ValueError(f'unknown error_code: {error_code}')

  def get_field_type(self, type_: str, module: _PythonModule) -> str:
    match = re.match(r'(\w+)(?:\[([^\]]+)\])?', type_)
    if not match:
      raise ValueError(f'what\'s dis? {type_!r}')
    type_, parameters = match.groups()
    if python_type := self.BUILTIN_TYPES.get(type_):
      if parameters:
        raise ValueError(f'type {type_} cannot be parametrized')
      if '.'in python_type:
        module.module_imports.add(python_type.rpartition('.')[0])
      return python_type
    if python_type := self.PARAMETRIZED_TYPES.get(type_):
      split_parameters = [x.strip() for x in parameters.split(',')]
      num_params = python_type.count('?')
      if len(split_parameters) != num_params:
        raise ValueError(f'type {type_} requires {num_params} parameters, got {len(split_parameters)}')
      split_parameters = [self.get_field_type(x, module) for x in split_parameters]
      return python_type.replace('?', '{}').format(*split_parameters)
    # Try to resolve the type in the available modules.
    for module_name, modules in self.modules.items():
      for module_cfg in modules:
        if type_ in module_cfg.types:
          if self._current != module_name:
            module.member_imports.add(module_name + '.' + type_)
          return type_
    raise ValueError(f'unknown type: {type_}')

  def get_auth_decorators(self, auth: AuthenticationConfig | None, module: _PythonModule) -> list[str]:
    from ..model._auth import BasicAuthenticationConfig, OAuth2BearerAuthenticationConfig
    if auth is None:
      return []
    module.member_imports.add('skye.api.runtime.auth.authentication')
    if isinstance(auth, OAuth2BearerAuthenticationConfig):
      module.member_imports.add('skye.api.runtime.auth.OAuth2Bearer')
      if auth.header_name:
        method = f'OAuth2Bearer({auth.header_name!r})'
      else:
        method = 'OAuth2Bearer()'
    elif isinstance(auth, BasicAuthenticationConfig):
      module.member_imports.add('skye.api.runtime.auth.Basic')
      method = 'Basic()'
    else:
      raise ValueError(f'unexpected auth type: {type(auth).__name__}')
    return [f'@authentication({method})']

  def get_endpoint_definition(self, name: str, endpoint: EndpointConfig, auth: AuthenticationConfig | None, module: _PythonModule) -> _PythonFunction:
    module.member_imports.add('skye.api.runtime.endpoint.endpoint')
    decorators = [f'@endpoint({endpoint.http!r})']
    args = ['self'] + [f'{k}: {self.get_field_type(a.type, module)}' for k, a in (endpoint.args or {}).items()]
    if auth:
      module.member_imports.add('skye.api.runtime.auth.Credentials')
      args.insert(1, 'auth: Credentials')

    # NOTE (@nrosenstein): For now we just trigger an error if an argument name that collides with a Python
    #   builtin is used, but in a future version we should rename the in-Python code function argument name
    #   (e.g. by suffixing it with an underscore) and specify the alias in the HTTP context via the Skye
    #   @args() decorator.
    for arg_name in (endpoint.args or {}):
      if arg_name in self.BUILTIN_NAMES:
        raise ValueError(f'argument name {arg_name!r} on endpoint {name!r} collides with built-in')

    return _PythonFunction(
      name=name,
      args=args,
      return_type=self.get_field_type(endpoint.return_, module) if endpoint.return_ else 'None',
      docs=endpoint.docs,
      decorators=decorators,
      body=['pass'],
      async_=True,
    )


def get_argument_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser()
  parser.add_argument(
    'files',
    nargs='+',
    metavar='FILE',
    help='One or more YAML files to generate Python API bindings for.',
  )
  parser.add_argument(
    '--prefix',
    metavar='PATH',
    help='Generate files starting from the specified directory (defaults to cwd).',
    required=True,
  )
  parser.add_argument(
    '--stdout',
    action='store_true',
    help='Print the generated code to stdout instead.'
  )
  parser.add_argument(
    '--async',
    action='store_true',
    help='Generate async API bindings.',
  )
  parser.add_argument(
    '--sync', '--blocking',
    action='store_true',
    help='Generate blocking API bindings.',
  )
  parser.add_argument(
    '--package',
    metavar='PACKAGE_NAME',
    help='Generate the code in a package (directory format) with the specified name.',
  )
  parser.add_argument(
    '--module',
    metavar='MODULE_NAME',
    help='Generate the code in a single module with the specified name.',
  )
  return parser


def main():
  parser = get_argument_parser()
  args = parser.parse_args()

  if args.module and args.package:
    parser.error('--module and --package cannot be mixed')
  if not args.module and not args.package:
    parser.error('one of --module or --package must be specified')

  project = Project()
  for filename in map(Path, args.files):
    project.add(filename.stem, filename)

  generator = PythonGenerator(args.prefix)

  if args.module:
    generator.modules = {args.module: list(project.items.values())}
  else:
    generator.modules = {args.package + '.' + k: [m] for k, m in project.modules.items()}

  generator.write(stdout=args.stdout)


if __name__ == '__main__':
  main()
