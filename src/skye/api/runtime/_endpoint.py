
import dataclasses
import enum
import re
import typing as t

from beartype import beartype
from nr.pylang.utils.singletons import NotSet

from ._utils import Annotateable, T, add_annotation


@dataclasses.dataclass(repr=False)
class Path:
  """ Represents a parametrized HTTP path. """

  @dataclasses.dataclass
  class _Str:
    value: str
    def __str__(self) -> str: return self.value

  @dataclasses.dataclass
  class _Param:
    name: str
    hint: str | None
    def __str__(self) -> str: return f'{{{self.name}:{self.hint}}}' if self.hint else f'{{{self.name}}}'

  _parts: list[_Str | _Param]
  _parameters: dict[str, str | None]

  @beartype
  def __init__(self, path: str) -> None:
    self._parts = []
    offset = 0
    for match in re.finditer(r'\{([A-Za-z][A-Za-z0-9_]*(:[A-Za-z][A-Za-z0-9_]*)?)\}', path):
      if prefix := path[offset:match.start()]:
        self._parts.append(Path._Str(prefix))
      param_name = match.group(1)
      hint: str | None = None
      if ':' in param_name:
        param_name, hint = param_name.partition(':')[::2]
      self._parts.append(Path._Param(param_name, hint))
      offset = match.end()
    if offset < len(path):
      self._parts.append(Path._Str(path[offset:]))
    self._parameters = {x.name: x.hint for x in self._parts if isinstance(x, Path._Param)}
    assert str(self) == path

  def __str__(self) -> str:
    return ''.join(map(str, self._parts))

  def __repr__(self) -> str:
    return f'Path({str(self)!r})'

  @property
  def parameters(self) -> dict[str, str | None]:
    return self._parameters


class ParamKind(enum.Enum):
  body = 'body'
  cookie = 'cookie'
  header = 'header'
  path = 'path'
  query = 'query'


@dataclasses.dataclass
class Param:
  """ Represents additional information for a parameter. """

  kind: ParamKind
  default: t.Any | NotSet
  name: str | None


def cookie(default: t.Any | NotSet = NotSet.Value, name: str | None = None) -> Param:
  return Param(ParamKind.cookie, default, name)


def header(default: t.Any | NotSet = NotSet.Value, name: str | None = None) -> Param:
  return Param(ParamKind.header, default, name)


def path(default: t.Any | NotSet = NotSet.Value, name: str | None = None) -> Param:
  return Param(ParamKind.path, default, name)


def query(default: t.Any | NotSet = NotSet.Value, name: str | None = None) -> Param:
  return Param(ParamKind.query, default, name)


@dataclasses.dataclass
class EndpointAnnotation:
  """ Holds the endpoint details added with the #endpoint() decorator. """
  method: str
  path: Path
  args: dict[str, Param]

  def __pretty__(self) -> str:
    return f'@endpoint("{self.method} {self.path}")'


def endpoint(http: str, args: dict[str, Param] | None = None) -> t.Callable[[T], T]:
  """
  Decorator for methods on a service class to mark them as endpoints to be served/accessible via the specified
  HTTP method and parametrized path.
  """

  method, path = http.split(maxsplit=2)

  def _decorator(obj: T) -> T:
    add_annotation(
      t.cast(Annotateable, obj),
      EndpointAnnotation,
      EndpointAnnotation(method, Path(path), args or {}),
      front=True
    )
    return obj

  return _decorator
