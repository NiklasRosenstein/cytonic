
import dataclasses
import typing as t

from databind.core.annotations import alias

from ..runtime.endpoint import ParamKind


@dataclasses.dataclass
class ArgumentConfig:
  type: str
  kind: ParamKind | None = None


@dataclasses.dataclass
class EndpointConfig:

  #: Parametrized HTTP method and path string for the endpoint/
  http: str

  #: Arguments for the endpoint.
  args: dict[str, ArgumentConfig] | None = None

  #: The return type of the endpoint.
  return_: t.Annotated[str | None, alias('return')] = None

  docs: str | None = None
