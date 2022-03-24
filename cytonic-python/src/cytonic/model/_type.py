
from __future__ import annotations
import typing as t
import dataclasses
import itertools

from databind.core import Context
from databind.json.annotations import with_custom_json_converter
from nr.util.parsing import Scanner
from nr.util.singleton import NotSet


def parse_type_string(type_string: str) -> tuple[str, list[str] | None]:
  """
  Parses a type string into its components, returning a tuple of the type name and a list of its parameters, if any.
  """

  scanner = Scanner(type_string)

  type_name = scanner.getmatch(r'[^\[]+', 0)
  if not type_name:
    raise ValueError(f'bad type string: {type_string!r}')

  if not scanner:
    return type_name, None

  assert scanner.char == '['

  parameters = []
  while scanner and scanner.char != ']':
    scanner.next()
    open_parens = 0
    start = scanner.pos
    while scanner and (scanner.char != ',' or open_parens > 0):
      if scanner.char == '[':
        open_parens += 1
      elif scanner.char == ']':
        if open_parens == 0:
          break
        open_parens -= 1
      scanner.next()
    if open_parens != 0:
      raise ValueError(f'bad type string: {type_string!r}')
    if start == scanner.pos:
      break
    parameters.append(type_string[start.offset:scanner.pos.offset])

  if scanner.char != ']':
    raise ValueError(f'bad type string: {type_string!r}')

  return type_name, parameters


@dataclasses.dataclass
class BadDatatypeFormatError(ValueError):
  error: str
  value: str


@with_custom_json_converter()
@dataclasses.dataclass
class Datatype:
  """
  Represents a datatype reference as specified in a Cytonic YAML configuration. A reference is usually just the
  name of a type, except for generic types. Generic type parameters are enclosed with brackets and separated by
  commas. Examples for datatype references are `User`, `list[Book]`, `set[string]`, `map[string, set[Author]]`.
  """

  name: str
  parameters: list[Datatype] | None = None

  def __repr__(self) -> str:
    return f'Datatype({str(self)!r})'

  def __str__(self) -> str:
    if self.parameters:
      return f'{self.name}[{", ".join(map(str, self.parameters))}]'
    else:
      return self.name

  @classmethod
  def _convert_json(cls, ctx: Context) -> t.Any:
    if ctx.direction.is_deserialize() and isinstance(ctx.value, str):
      return cls.parse(ctx.value)
    elif ctx.direction.is_serialize() and isinstance(ctx.value, Datatype):
      return str(ctx.value)
    return NotImplemented

  @classmethod
  def parse(cls, type_string: str) -> 'Datatype':
    try:
      type_name, parameters_strings = parse_type_string(type_string)
    except ValueError as exc:
      raise BadDatatypeFormatError('bad type string', type_string)
    try:
      parameters = [
        Datatype.parse(x.strip())
        for x in parameters_strings
      ] if parameters_strings is not None else None
    except BadDatatypeFormatError as exc:
      exc.value = type_string
      raise
    return cls(type_name, parameters)


@with_custom_json_converter()
@dataclasses.dataclass
class FieldConfig:
  type: str
  docs: str | None = None
  default: t.Any = NotSet.Value

  @classmethod
  def _convert_json(cls, ctx: Context) -> t.Any:
    if ctx.direction.is_deserialize() and isinstance(ctx.value, str):
      return cls(ctx.value, None)
    return NotImplemented


@dataclasses.dataclass
class ValueConfig:
  name: str
  docs: str | None = None


@dataclasses.dataclass
class TypeConfig:

  #: If set, the type defines an enumeration of the specified values.
  values: list[ValueConfig] | None = None

  #: The name of a type that this type extends.
  extends: str | None = None

  #: If set, the type defines a structure of the specified values.
  fields: dict[str, FieldConfig] | None = None

  #: If set, the type defines a union of the specified types.
  union: dict[str, str] | None = None

  docs: str | None = None

  def validate(self) -> None:
    groups = [('values',), ('extends', 'fields'), ('union',)]
    for group1, group2 in itertools.permutations(groups, 2):
      if any(getattr(self, n) is not None for n in group1) and any(getattr(self, n) is not None for n in group2):
        raise ValueError(f'TypeConfig {group1} cannot be mixed with {group2}')
