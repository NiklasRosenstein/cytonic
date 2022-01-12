
import enum
import dataclasses
import typing as t

from databind.core import Context
from databind.core.annotations import alias
from databind.json.annotations import with_custom_json_converter

from ._auth import AuthenticationConfig
from ._http_path import HttpPath


class ParamKind(enum.Enum):
  auth = 'auth'
  body = 'body'
  cookie = 'cookie'
  header = 'header'
  path = 'path'
  query = 'query'


@with_custom_json_converter()
@dataclasses.dataclass
class ArgumentConfig:
  type: str
  kind: ParamKind | None = None

  def __post_init__(self) -> None:
    if self.kind == ParamKind.auth:
      raise ValueError('`ArgumentConfig.kind` cannot be `ParamKind.auth`, the `auth` parameter is auto generated')

  @classmethod
  def _convert_json(cls, ctx: 'Context') -> t.Any:
    if ctx.direction.is_deserialize() and isinstance(ctx.value, str):
      return cls(ctx.value, None)
    return NotImplemented


@dataclasses.dataclass
class EndpointConfig:

  #: Parametrized HTTP method and path string for the endpoint/
  http: HttpPath

  #: Override the authentication method for this endpoint.
  auth: AuthenticationConfig | None = None

  #: Arguments for the endpoint.
  args: dict[str, ArgumentConfig] | None = None

  #: The return type of the endpoint.
  return_: t.Annotated[str | None, alias('return')] = None

  docs: str | None = None
