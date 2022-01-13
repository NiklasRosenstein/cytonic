
import dataclasses
import re
import typing as t

from databind.core import Context
from databind.json.annotations import with_custom_json_converter


@with_custom_json_converter()
@dataclasses.dataclass(repr=False, init=False)
class HttpPath:
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

  def __init__(self, path: str) -> None:
    self._parts = []
    offset = 0
    for match in re.finditer(r'\{([A-Za-z][A-Za-z0-9_]*(:[A-Za-z][A-Za-z0-9_]*)?)\}', path):
      if prefix := path[offset:match.start()]:
        self._parts.append(HttpPath._Str(prefix))
      param_name = match.group(1)
      hint: str | None = None
      if ':' in param_name:
        param_name, hint = param_name.partition(':')[::2]
      self._parts.append(HttpPath._Param(param_name, hint))
      offset = match.end()
    if offset < len(path):
      self._parts.append(HttpPath._Str(path[offset:]))
    self._parameters = {x.name: x.hint for x in self._parts if isinstance(x, HttpPath._Param)}
    assert str(self) == path

  def __str__(self) -> str:
    return ''.join(map(str, self._parts))

  def __repr__(self) -> str:
    return f'Path({str(self)!r})'

  @property
  def parameters(self) -> dict[str, str | None]:
    return self._parameters

  @classmethod
  def _convert_json(cls, ctx: 'Context') -> t.Any:
    if ctx.direction.is_deserialize() and isinstance(ctx.value, str):
      return cls(ctx.value)
    elif ctx.direction.is_serialize() and isinstance(ctx.value, HttpPath):
      return str(ctx.value)
    return NotImplemented
