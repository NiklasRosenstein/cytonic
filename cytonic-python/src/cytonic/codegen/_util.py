
import abc
import contextlib
import dataclasses
import re
import sys
import typing as t
from pathlib import Path

from nr.util.generic import T
from cytonic.model import Project


@dataclasses.dataclass
class FileOpener:

  stdout: bool = False
  open_stdout: t.Optional[t.Callable[[str], t.Any]] = None
  open_fs: t.Optional[t.Callable[[str, t.TextIO], t.Any]] = None

  @contextlib.contextmanager
  def open(self, filename: Path | str) -> t.Generator[t.TextIO, None, None]:
    if self.stdout:
      if self.open_stdout:
        self.open_stdout(filename)
      yield sys.stdout
    else:
      filename = Path(filename)
      filename.parent.mkdir(parents=True, exist_ok=True)
      with filename.open('w') as fp:
        if self.open_fs:
          self.open_fs(str(filename), fp)
        yield fp

  @staticmethod
  def with_indicator(stdout: bool, stdout_indicator: str, fs_indicator: str = 'Writing ') -> None:
    return FileOpener(
      stdout,
      lambda fn: print(f'\n{stdout_indicator} {fn}'),
      lambda fn, fp: print(f'{fs_indicator} {fn}'),
    )


class TypeConverter(t.Generic[T]):
  """
  A helper class to convert type strings as defined in the YAML specification to other forms of representation.
  The type parameter *T* is the data type which represents the type in its new form.
  """

  def convert_type_string(self, type_string: str) -> T:
    match = re.match(r'(\w+)(?:\[(.+)\])?', type_string)
    if not match:
      raise ValueError(f'what\'s dis? {type_string!r}')

    type_name, parameters_string = match.groups()
    parameters = None if parameters_string is None else [x.strip() for x in parameters_string.split(',')]

    return self.create_type(type_name, parameters)

  @abc.abstractmethod
  def create_type(self, type_name: str, parameters: list[str]) -> T:
    ...


@dataclasses.dataclass
class DefaultTypeConverter(TypeConverter[str]):
  """
  A helper class for type conversion. To create a new type converter for a language, follow these steps:

  1. fill the #TYPE_TEMPLATES mapping with key-value pairs for the built-in types in Cytonic
  2. implement the #get_module_id() and #do_import_type() methods
  """

  project: Project
  TYPE_TEMPLATES: t.ClassVar[dict[str, str]] = {}

  BUILTIN_TYPES = [
    'any',
    'string',
    'integer',
    'double',
    'boolean',
    'datetime',
    'decimal',
    'list',
    'set',
    'map',
    'optional',
  ]

  def __init_subclass__(cls) -> None:
    missing_templates = set(cls.BUILTIN_TYPES) - cls.TYPE_TEMPLATES.keys()
    if missing_templates:
      raise RuntimeError(f'missing type templates in {cls.__name__}: {missing_templates}')

  def __post_init__(self) -> None:
    self.imported_types: set[str] = set()

  def create_type(self, type_name: str, parameters: list[str] | None) -> str:
    if type_name in self.TYPE_TEMPLATES:
      type_template = self.TYPE_TEMPLATES[type_name]
      num_parameters = type_template.count('?')
      parameters = parameters or []
      if num_parameters != len(parameters):
        raise ValueError(f'type {type_name} requires {num_parameters} but got {len(parameters)}')
      parameters = [self.convert_type_string(s) for s in parameters]
      final_type = type_template.replace('?', '{}').format(*parameters)
      return self.visit_type(final_type, None)

    type_locator = self.project.find_type(type_name)
    if type_locator:
      self.imported_types.add(type_name)
      type_name = self.visit_type(type_name, type_locator)
      return type_name

    raise ValueError(f'type {type_name} does not exist')

  def visit_type(self, rendered_type: str, type_locator: Project.TypeLocator | None) -> str:
    return rendered_type
