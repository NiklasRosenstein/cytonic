
import dataclasses

from cytonic.model import AuthenticationConfig


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
