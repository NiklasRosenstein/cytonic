
import abc
import dataclasses

from databind.core.annotations import union

from ..runtime.auth import AuthenticationMethod, BasicAuthenticationMethod, OAuth2BearerAuthenticationMethod


@union(style=union.Style.flat)
class AuthenticationConfig(abc.ABC):
  pass


@union.subtype(AuthenticationConfig, 'oauth2_bearer')
@dataclasses.dataclass
class OAuth2BearerAuthenticationConfig(AuthenticationConfig):
  header_name: str | None = None


@union.subtype(AuthenticationConfig, 'basic')
@dataclasses.dataclass
class BasicAuthenticationConfig(AuthenticationConfig):
  pass
