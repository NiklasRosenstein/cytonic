
import abc
import base64
import dataclasses
import typing as t

from starlette.requests import Request
from .exceptions import UnauthorizedError
from ._utils import add_annotation, T


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
    add_annotation(obj, AuthenticationAnnotation, AuthenticationAnnotation(authentication_method, options), front=True)
    return obj

  return _decorator


@dataclasses.dataclass
class BearerToken:
  value: str


@dataclasses.dataclass
class BasicAuth:
  username: str
  password: str


class AuthenticationMethod(abc.ABC):
  """
  Interface for authentication methods that must extract credentials from a request.
  """

  @abc.abstractmethod
  async def extract_credentials(self, request: Request) -> t.Any | None:
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

  async def extract_credentials(self, request: Request) -> t.Any | None:
    header_value: str | None = request.headers.get(self.header_name)
    if not header_value:
      raise UnauthorizedError('missing Authorization header')
    scheme, header_value, *_ = header_value.split(maxsplit=2) + ['']
    if scheme.lower() != 'bearer':
      raise UnauthorizedError('bad Authorization scheme')
    return BearerToken(header_value)


@dataclasses.dataclass
class BasicAuthenticationMethod(AuthenticationMethod):
  """
  Extracts HTTP Basic authentication credentials from the request.
  """

  async def extract_credentials(self, request: Request) -> t.Any | None:
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
    return BasicAuth(username, password)


@dataclasses.dataclass
class NoAuthenticationMethod(AuthenticationMethod):

  async def extract_credentials(self, request: Request) -> t.Any | None:
    return None


authorization_methods = {
  'oauth2_bearer': OAuth2BearerAuthenticationMethod,
  'basic': BasicAuthenticationMethod,
  'none': NoAuthenticationMethod,
}
