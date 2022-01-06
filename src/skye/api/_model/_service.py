
import dataclasses

from ._auth import AuthenticationConfig
from ._endpoint import EndpointConfig
from ._error import ErrorConfig
from ._type import TypeConfig


@dataclasses.dataclass
class ServiceConfig:

  #: The name of the service; this is used in several places in the generated code.
  name: str

  # Docstring for the service.
  docs: str | None = None

  #: The endpoints in the service.
  endpoints: dict[str, EndpointConfig] = dataclasses.field(default_factory=dict)

  #: A definition of types for this service.
  types: dict[str, TypeConfig] = dataclasses.field(default_factory=dict)

  #: Definition of error types.
  errors: dict[str, ErrorConfig] = dataclasses.field(default_factory=dict)

  #: Authentication configuration.
  auth: AuthenticationConfig | None = None
