
import dataclasses

from cytonic.model import AuthenticationConfig, NoAuth, OAuth2Bearer, BasicAuth as _BasicAuth


@dataclasses.dataclass
class BearerToken:
  value: str


@dataclasses.dataclass
class BasicAuth:
  username: str
  password: str


@dataclasses.dataclass(frozen=True)
class Credentials:
  """ Container for authentication credentials. """

  config: AuthenticationConfig
  value: BearerToken | BasicAuth | None

  def __bool__(self) -> bool:
    return self.value is not None

  def get_bearer_token(self) -> str:
    if not isinstance(self.value, BearerToken):
      raise RuntimeError('credential contains no BearerToken')
    return self.value.value

  def get_basic(self) -> BasicAuth:
    if not isinstance(self.value, BasicAuth):
      raise RuntimeError('credential contains no BasicAuth')
    return self.value

  @classmethod
  def empty(cls, config: NoAuth) -> 'Credentials':
    return cls(config, None)

  @classmethod
  def of_bearer_token(cls, config: OAuth2Bearer, token: str) -> 'Credentials':
    return cls(config, BearerToken(token))

  @classmethod
  def of_basic_auth(cls, config: _BasicAuth, username: str, password: str) -> 'Credentials':
    return cls(config, BasicAuth(username, password))
