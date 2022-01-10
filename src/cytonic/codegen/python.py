
"""
A code generator for Python code from Cytonic YAML configs. This module can be called as a CLI as
`cytonic-codegen-python` or `python -m cytonic.codegen.python`. The generator can be used to generate code
in three different formats:

* A single Python module file (using the `--module` option)
* A Python package or subpackage (using the `--package` option)
* A Python project with a `pyproject.toml` using Flit as a build system (using the `--installable` option)
"""

import abc
import argparse
import builtins
import contextlib
import dataclasses
import re
import sys
import textwrap
import typing as t
from pathlib import Path

from nr.util.singleton import NotSet

from cytonic import __version__
from cytonic.model import AuthenticationConfig, EndpointConfig, ErrorConfig, ModuleConfig, Project, TypeConfig


def _format_docstrings(level: int, indent: str, docs: str, width: int = 119) -> str:
  width -= level * len(indent)
  prefix = level * indent
  lines = list(textwrap.wrap(docs, width))
  if len(lines) == 1 and len(lines[0]) < (width - 2):
    line = lines[0].replace(r"\"", r"\\\"")
    return f'{prefix}" {line} "\n'
  else:
    return '\n'.join([f'{prefix}"""'] + [prefix + l for l in lines] + [f'{prefix}"""']) + '\n'


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
    fp.write('# Do not edit; this file was automatically generated with cytonic.codegen.python.\n\n')
    _DocstringBlock(self.docs).render(level, indent, fp)

    if self.module_imports:
      fp.write('\n')
      for name in sorted(self.module_imports):
        fp.write(f'import {name}\n')
    if self.member_imports:
      fp.write('\n')
      import itertools
      for group_key, values in itertools.groupby(sorted(self.member_imports), lambda s: s.rpartition('.')[0]):
        members = [x.rpartition('.')[-1] for x in values]
        fp.write(f'from {group_key} import {", ".join(members)}\n')
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
class _StaticCode(_Rendererable):
  code: str

  def render(self, level: int, indent: str, fp: t.TextIO) -> None:
    for line in self.code.splitlines():
      fp.write(level * indent + line + '\n')


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
      for member in self.members:
        fp.write('\n')
        member.render(level + 1, indent, fp)


@dataclasses.dataclass
class _FileWriter:

  stdout: bool = False

  @contextlib.contextmanager
  def open(self, filename: Path | str) -> t.Generator[t.TextIO, None, None]:
    if self.stdout:
      print('#', filename)
      yield sys.stdout
    else:
      filename = Path(filename)
      filename.parent.mkdir(parents=True, exist_ok=True)
      print('Write', filename)
      with filename.open('w') as fp:
        yield fp


@dataclasses.dataclass
class CodeGenerator:
  """ A class to render Python code from a Skye-API definition. """

  prefix: Path | str
  package: str | None = None
  modules: dict[str, list[ModuleConfig]] = dataclasses.field(default_factory=dict)

  BUILTIN_TYPES = {
    'any': 'typing.Any',
    'string': 'str',
    'integer': 'int',
    'float': 'float',
    'double': 'float',
    'boolean': 'bool',
    'datetime': 'datetime.datetime',
    'decimal': 'decimal.Decimal',
  }

  PARAMETRIZED_TYPES = {
    'list': 'typing.List[?]',
    'set': 'typing.Set[?]',
    'map': 'typing.Dict[?, ?]',
    'optional': 'typing.Optional[?]',
  }

  PYTHON_KEYWORDS = ['from', 'import', 'as', 'with', 'for', 'in', 'while', 'try', 'except', 'finally']
  BUILTIN_NAMES = PYTHON_KEYWORDS + dir(builtins) + ['request', 'auth']

  _current_module_name: str = t.cast(t.Any, None)
  _curernt_module: ModuleConfig = t.cast(t.Any, None)
  _current_types_already_rendered: set[str] = t.cast(t.Any, None)

  def write(self, stdout: bool = False, indent: str = '  ') -> None:
    """ Writes the contents of one or more modules into a Python module with the specified name. """

    writer = _FileWriter(stdout)
    for name, module in self.modules.items():
      self._current_module_name = name
      self._current_module = module
      self._current_types_already_rendered = set()
      python_module = self._build_python_module(module)
      with writer.open(Path(self.prefix) / (name.replace('.', '/') + '.py')) as fp:
        python_module.render(0, indent, fp)

    if self.package:
      with writer.open(Path(self.prefix) / self.package.replace('.', '/') / '__init__.py') as fp:
        for module_name in self.modules:
          fp.write(f'from {module_name} import *\n')

  def _build_python_module(self, modules: list[ModuleConfig]) -> _PythonModule:
    python_module = _PythonModule(coding='utf-8')
    python_module.module_imports.add('dataclasses')
    python_module.member_imports.add('cytonic.description.service')

    for module in modules:
      for error_name, error in module.errors.items():
        self.add_error_type(error_name, error, python_module)
      for type_name, type_ in module.types.items():
        self.add_type(type_name, type_, python_module)

      self.add_service_definition(module, python_module, async_=False)
      self.add_service_definition(module, python_module, async_=True)

    return python_module

  def _make_python_class(self, name: str, config: ErrorConfig | TypeConfig, module: _PythonModule) -> _PythonClass:
    return _PythonClass(
      name=name,
      docs=config.docs,
      decorators=['@dataclasses.dataclass'],
      fields=[
        _PythonClassField(k, self.get_field_type(f.type, module), repr(f.default) if f.default is not NotSet.Value else None, f.docs) for k, f in config.fields.items()
      ] if config.fields else []
    )

  def add_error_type(self, name: str, error: ErrorConfig, module: _PythonModule) -> None:
    class_ = self._make_python_class(name + 'Error', error, module)
    class_.members.append(_PythonFunction('__post_init__', ['self'], body=['super().__init__()']))
    class_.bases.append(self.get_error_base_type(error.error_code, module))
    module.members.append(class_)

  def add_type(self, name: str, type_: TypeConfig, module: _PythonModule) -> None:
    type_.validate()

    if type_.union:
      module.module_imports.add('typing')
      module.module_imports.add('databind.core.annotations')

      # TODO (@NiklasRosenstein): Add support for alternate union styles in TypeConfig?
      code = '\n'.join([
        f'{name} = typing.Annotated[',
        '  ' + ' | '.join(v for v in type_.union.values()) + ',',
        '  databind.core.annotations.union({',
        *(f'    {k!r}: {v},' for k, v in type_.union.items()),
        '  })',
        ']',
      ])

      module.members.append(_StaticCode(code))
      return

    if type_.values:
      class_ = _PythonClass(name, type_.docs)
      module.module_imports.add('enum')
      for value in type_.values:
        class_.fields.append(_PythonClassField(value.name, None, 'enum.auto()', value.docs))
      class_.bases = ['enum.Enum']
    else:
      class_ = self._make_python_class(name, type_, module)

    if type_.extends:
      # TODO (@nrosenstein): Ensure that the type being extended is available in the curernt module.
      class_.bases = [self.get_field_type(type_.extends, module)]

    self._current_types_already_rendered.add(name)
    module.members.append(class_)

  def add_service_definition(self, module: ModuleConfig, python_module: _PythonModule, async_: bool) -> None:
    python_module.module_imports.add('abc')
    python_module.members.append(_PythonClass(
      name=f'{module.name}ServiceAsync' if async_ else f'{module.name}ServiceBlocking',
      docs=module.docs,
      bases=['abc.ABC'],
      decorators=[f'@service({module.name!r})'] + self.get_auth_decorators(module.auth, python_module),
      members=[self.get_endpoint_definition(k, e, module.auth, python_module, async_) for k, e in module.endpoints.items()]
    ))

  def get_error_base_type(self, error_code: str, module: _PythonModule) -> str:
    if error_code == 'NOT_FOUND':
      module.member_imports.add('cytonic.runtime.NotFoundError')
      return 'NotFoundError'
    elif error_code == 'UNAUTHORIZED':
      module.member_imports.add('cytonic.runtime.UnauthorizedError')
      return 'UnauthorizedError'
    elif error_code == 'CONFLICT':
      module.member_imports.add('cytonic.runtime.ConflictError')
      return 'ConflictError'
    elif error_code == 'ILLEGAL_ARGUMENT':
      module.member_imports.add('cytonic.runtime.IllegalArgumentError')
      return 'IllegalArgumentError'
    else:
      raise ValueError(f'unknown error_code: {error_code}')

  def get_field_type(
    self,
    type_: str,
    module: _PythonModule,
    collect_custom_types_to: list[tuple[str, str]] | None = None,
    add_imports: bool = True,
  ) -> str:
    """
    Gets the Python type name for the given type name in the YAML configuration.

    :param collect_custom_types_to: Custom types found in the *type_* are added to this list if given.
    :param add_imports: Add imports to the *module* (default: true).
    """

    match = re.match(r'(\w+)(?:\[(.+)\])?', type_)
    if not match:
      raise ValueError(f'what\'s dis? {type_!r}')

    type_, parameters = match.groups()

    if python_type := self.BUILTIN_TYPES.get(type_):
      if parameters:
        raise ValueError(f'type {type_} cannot be parametrized')
      if '.'in python_type and add_imports:
        module.module_imports.add(python_type.rpartition('.')[0])
      return python_type

    if python_type := self.PARAMETRIZED_TYPES.get(type_):
      split_parameters = [x.strip() for x in parameters.split(',')] if parameters else []
      num_params = python_type.count('?')
      if len(split_parameters) != num_params:
        raise ValueError(f'type {type_} requires {num_params} parameters, got {len(split_parameters)}')

      custom_types_in_parameters: list[tuple[str, str]] = []
      split_parameters = [self.get_field_type(x, module, custom_types_in_parameters) for x in split_parameters]

      code = python_type.replace('?', '{}').format(*split_parameters)
      if code.startswith('typing.'):
        module.module_imports.add('typing')

      return code

    # Try to resolve the type in the available modules.
    for module_name, modules in self.modules.items():
      for module_cfg in modules:
        if type_ in module_cfg.types:
          available = (type_ in self._current_types_already_rendered)
          if self._current_module_name != module_name and add_imports:
            module.member_imports.add(module_name + '.' + type_)
            available = True
          if collect_custom_types_to is not None:
            collect_custom_types_to.append((module_name, type_))
          return repr(type_) if not available else type_

    raise ValueError(f'unknown type: {type_}')

  def get_auth_decorators(self, auth: AuthenticationConfig | None, module: _PythonModule) -> list[str]:
    if auth is None:
      return []
    module.member_imports.add('cytonic.description.authentication')
    module.member_imports.add(f'cytonic.model.{type(auth).__name__}')
    method = repr(auth)
    return [f'@authentication({method})']

  def get_endpoint_definition(self, name: str, endpoint: EndpointConfig, auth: AuthenticationConfig | None, module: _PythonModule, async_: bool) -> _PythonFunction:
    module.member_imports.add('cytonic.description.endpoint')
    decorators = [f'@endpoint("{endpoint.http}")'] + self.get_auth_decorators(endpoint.auth, module)
    args = ['self']
    for arg_name, arg in (endpoint.args or {}).items():
      arg_code = f'{arg_name}: {self.get_field_type(arg.type, module)}'
      if arg.type.startswith('optional['):
        arg_code += ' = None'
      args.append(arg_code)

    if auth or endpoint.auth:
      module.member_imports.add('cytonic.runtime.Credentials')
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
      decorators=decorators + ['@abc.abstractmethod'],
      body=['pass'],
      async_=async_,
    )


@dataclasses.dataclass
class ProjectGenerator:

  prefix: Path | str
  codegen: CodeGenerator
  module: str | None = None
  package: str | None = None
  version: str | None = None
  description: str | None = None
  dist_name: str | None = None

  def write(self, stdout: bool = False) -> None:
    assert self.package or self.module

    writer = _FileWriter(stdout)
    prefix = Path(self.prefix)

    if not self.version:
      self.version = '0.0.0'
    if not self.description:
      self.description = 'Auto-generated API bindings.'

    if self.package:
      with writer.open(prefix / 'src' / self.package.replace('.', '/') / 'py.typed'): ...

    with writer.open(prefix / 'pyproject.toml') as fp:
      fp.write('\n'.join([
        '[build-system]',
        'requires = ["flit_core >=3.2,<4"]',
        'build-backend = "flit_core.buildapi"',
        '',
        '[project]',
        f'name = {self.dist_name or self.module or self.package!r}',
        f'version = {self.version!r}',
        'authors = []',
        f'description = {self.description!r}',
        'dependencies = [',
        f'  "cytonic ~={__version__}",',
        ']',
        '',
      ]))
      if self.dist_name:
        fp.write('\n'.join([
          '',
          '[tool.flit.module]',
          f'name = {self.module or self.package!r}',
          '',
        ]))


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
    help='Generate files starting from the specified directory.',
    type=Path,
  )
  parser.add_argument(
    '--installable',
    metavar='PATH',
    help='Generate a fully installable Pyhon project at the specified location. Cannot be mixed with --prefix',
    type=Path,
  )
  parser.add_argument(
    '--dist-name',
    metavar='NAME',
    help='The distribution name (only with --installable).',
  )
  parser.add_argument(
    '--version',
    metavar='VERSION',
    help='The version number to write into the generated project (only with --installable).',
  )
  parser.add_argument(
    '--description',
    metavar='TEXT',
    help='The description to write into the generated project (only with --installable).',
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

  if args.installable and args.prefix:
    parser.error('--installable and --prefix cannot be mixed')
  if not args.installable and not args.prefix:
    parser.error('one of --installable or --prefix must be specified')

  if args.module and args.package:
    parser.error('--module and --package cannot be mixed')
  if not args.module and not args.package:
    parser.error('one of --module or --package must be specified')

  if args.version and not args.installable:
    parser.error('--version can only be used with --installable')
  if args.description and not args.installable:
    parser.error('--description can only be used with --installable')

  # Load the configuration files into a project.
  project = Project()
  for filename in map(Path, args.files):
    project.add(filename.stem, filename)

  # Configure the code generator.
  if args.installable:
    args.prefix = args.installable / 'src'

  codegen = CodeGenerator(args.prefix, args.package)
  if args.module:
    codegen.modules = {args.module: list(project.modules.values())}
  else:
    codegen.modules = {args.package + '.' + k: [m] for k, m in project.modules.items()}
  codegen.write(stdout=args.stdout)

  if args.installable:
    projectgen = ProjectGenerator(args.installable, codegen, args.module, args.package, args.version, args.description, args.dist_name)
    projectgen.write(args.stdout)


if __name__ == '__main__':
  main()
