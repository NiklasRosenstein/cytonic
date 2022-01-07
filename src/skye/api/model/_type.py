
import dataclasses
import itertools


@dataclasses.dataclass
class FieldConfig:
  type: str
  docs: str | None = None


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

  #: Specify that the type is a reference to a type defined in another module.
  #: The value should be a relative or absolute module ID. For example, if the
  #: type is to be referenced from a module defined in `users.yml` in the same
  #: project, the reference string would be `.users`.
  ref: str | None = None

  docs: str | None = None

  def validate(self) -> None:
    groups = [('values',), ('extends', 'fields'), ('union',), ('ref',)]
    for group1, group2 in itertools.permutations(groups, 2):
      if any(getattr(self, n) is not None for n in group1) and any(getattr(self, n) is not None for n in group2):
        raise ValueError(f'TypeConfig {group1} cannot be mixed with {group2}')
