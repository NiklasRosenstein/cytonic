
import abc
import dataclasses

from databind.core.annotations import union
from ..runtime.auth import AuthenticationMethod, BasicAuthenticationMethod, OAuth2BearerAuthenticationMethod


@union({
  'oauth2_bearer': 'OAuth2BearerAuthenticationConfig',
  'basic': 'BasicAuthenticationConfig',
}, style=union.Style.flat)
class AuthenticationConfig(abc.ABC):

  @abc.abstractmethod
  def get_authentication_method(self) -> AuthenticationMethod:
    ...


@dataclasses.dataclass
class OAuth2BearerAuthenticationConfig(AuthenticationConfig):
  header_name: str

  def get_authentication_method(self) -> AuthenticationMethod:
    return OAuth2BearerAuthenticationMethod(self.header_name)


@dataclasses.dataclass
class BasicAuthenticationConfig(AuthenticationConfig):

  def get_authentication_method(self) -> AuthenticationMethod:
    return BasicAuthenticationMethod()
