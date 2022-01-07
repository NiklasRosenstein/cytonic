
import dataclasses
import typing as t

from databind.core.annotations import alias

from ..runtime.endpoint import ParamKind
from ._auth import AuthenticationConfig


@dataclasses.dataclass
class ArgumentConfig:
  type: str
  kind: ParamKind | None = None


@dataclasses.dataclass
class EndpointConfig:

  #: Parametrized HTTP method and path string for the endpoint/
  http: str

  #: Override the authentication method for this endpoint.
  auth: AuthenticationConfig | None = None

  #: Arguments for the endpoint.
  args: dict[str, ArgumentConfig] | None = None

  #: The return type of the endpoint.
  return_: t.Annotated[str | None, alias('return')] = None

  docs: str | None = None
