
import abc
import base64
import dataclasses
import typing as t

from starlette.requests import Request

from ._utils import Annotateable, T, add_annotation
from .exceptions import UnauthorizedError


@dataclasses.dataclass
class AuthenticationAnnotation:
  """ Holds the authentication mode details added to a class or function with the #authentication() decorator. """
  authentication_method: str
  options: dict[str, t.Any]

  def get(self) -> 'AuthenticationMethod':
    return authorization_methods[self.authentication_method](**self.options)


def authentication(authentication_method: str, **options: t.Any) -> t.Callable[[T], T]:
  """
  Decorator for classes that describe an API service to specify one or more types of authentication usable with all
  of the endpoints. Multiple authentication methods can be specified per service or endpoint.
  """

  def _decorator(obj: T) -> T:
    add_annotation(
      t.cast(Annotateable, obj),
      AuthenticationAnnotation,
      AuthenticationAnnotation(authentication_method, options),
      front=True
    )
    return obj

  return _decorator


@dataclasses.dataclass
class BearerToken:
  value: str


@dataclasses.dataclass
class BasicAuth:
  username: str
  password: str


@dataclasses.dataclass(frozen=True)
class Authorization:
  value: t.Any | None

  def cast(self, of_type: t.Type[T]) -> T:
    if isinstance(self.value, of_type):
      return self.value
    raise RuntimeError(f'{type(self.value).__name__} is not of type {of_type.__name__}')


class AuthenticationMethod(abc.ABC):
  """
  Interface for authentication methods that must extract credentials from a request.
  """

  @abc.abstractmethod
  async def extract_credentials(self, request: Request) -> Authorization | None:
    """
    Extract the credentials from the request. Raise an #UnauthorizedError if no credentials are provided.
    It is not the responsibility of this method to ensure the validity of the provided credentials, only
    the form in which they are provided.
    """


@dataclasses.dataclass
class OAuth2BearerAuthenticationMethod(AuthenticationMethod):
  """
  Extracts a #BearerToken from the request.
  """

  def __init__(self, header_name: str = 'Authorization') -> None:
    self.header_name = header_name

  async def extract_credentials(self, request: Request) -> Authorization | None:
    header_value: str | None = request.headers.get(self.header_name)
    if not header_value:
      raise UnauthorizedError('missing Authorization header')
    scheme, header_value, *_ = header_value.split(maxsplit=2) + ['']
    if scheme.lower() != 'bearer':
      raise UnauthorizedError('bad Authorization scheme')
    return Authorization(BearerToken(header_value))


@dataclasses.dataclass
class BasicAuthenticationMethod(AuthenticationMethod):
  """
  Extracts HTTP Basic authentication credentials from the request.
  """

  async def extract_credentials(self, request: Request) -> Authorization | None:
    header_value: str | None = request.headers.get("Authorization")
    if not header_value:
      raise UnauthorizedError('missing Authorization header')
    scheme, header_value, *_ = header_value.split(maxsplit=2) + ['']
    if scheme.lower() != 'basic':
      raise UnauthorizedError('bad Authorization scheme')
    try:
      decoded = base64.b64decode(header_value).decode('ascii')
      if decoded.count(':') != 1:
        raise ValueError
    except (ValueError, UnicodeDecodeError):
      raise UnauthorizedError('bad Authorization header value')
    username, password = decoded.split(':')
    return Authorization(BasicAuth(username, password))


@dataclasses.dataclass
class NoAuthenticationMethod(AuthenticationMethod):

  async def extract_credentials(self, request: Request) -> Authorization | None:
    return None


authorization_methods = {
  'oauth2_bearer': OAuth2BearerAuthenticationMethod,
  'basic': BasicAuthenticationMethod,
  'none': NoAuthenticationMethod,
}
