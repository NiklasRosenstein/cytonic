
import abc
import dataclasses

from databind.core.annotations import union
from ..runtime.auth import AuthenticationMethod, BasicAuthenticationMethod, OAuth2BearerAuthenticationMethod


@union({
  'oauth2_bearer': lambda: OAuth2BearerAuthenticationConfig,
  'basic': lambda: BasicAuthenticationConfig,
}, style=union.Style.flat)
class AuthenticationConfig(abc.ABC):
  pass


@dataclasses.dataclass
class OAuth2BearerAuthenticationConfig(AuthenticationConfig):
  header_name: str | None = None


@dataclasses.dataclass
class BasicAuthenticationConfig(AuthenticationConfig):
  pass
