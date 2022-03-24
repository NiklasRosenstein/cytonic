
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

  def resolve_arg_kinds(self) -> None:
    """ Ensures that the #ArgumentConfig.kind is set for all arguments in the endpoint. Infers the types of args
    for which the kind is not set based on the #http path parameters and HTTP method (the first unspecified
    parameter kind that is not a path parameter is considered a body argument for POST/PUT). All other args
    default to query. """

    if not self.args:
      return

    path_parameters = {arg_name for arg_name, arg in self.args.items() if arg.kind == ParamKind.path}
    unknown_path_params = path_parameters - self.http.parameters.keys()
    if unknown_path_params:
      raise ValueError(
        f'some parameters in {self.http} marked as path parameters but do not appear in the path: {unknown_path_params}'
      )

    num_body_args = sum(1 for a in self.args.values() if a.kind == ParamKind.body)
    needs_body_arg = self.http.method in ('PUT', 'POST')
    body_arg_names = ('body', 'request')
    has_named_body_arg = any(k in self.args for k in body_arg_names)

    if num_body_args > 1:
      raise ValueError('endpoint cannot have multiple body parameters')

    for arg_name, arg in self.args.items():
      if arg.kind is not None:
        continue
      if arg_name in self.http.parameters:
        arg.kind = ParamKind.path
      elif (num_body_args == 0 and not has_named_body_arg and needs_body_arg) \
          or (has_named_body_arg and arg_name in body_arg_names):
        arg.kind = ParamKind.body
        num_body_args = 1
      else:
        arg.kind = ParamKind.query
