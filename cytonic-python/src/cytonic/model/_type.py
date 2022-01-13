
import typing as t
import dataclasses
import itertools

from databind.core import Context
from databind.json.annotations import with_custom_json_converter
from nr.util.singleton import NotSet


@with_custom_json_converter()
@dataclasses.dataclass
class FieldConfig:
  type: str
  docs: str | None = None
  default: t.Any = NotSet.Value

  @classmethod
  def _convert_json(cls, ctx: 'Context') -> t.Any:
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
