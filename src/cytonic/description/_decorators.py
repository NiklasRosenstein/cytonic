
import dataclasses
import typing as t

from nr.util.annotations import add_annotation
from nr.util.generic import T

from cytonic.model import AuthenticationConfig, HttpPath

if t.TYPE_CHECKING:
  from ._description import ArgumentDescription


@dataclasses.dataclass
class AuthenticationAnnotation:
  """ Holds the authentication mode details added to a class or function with the #authentication() decorator. """

  config: AuthenticationConfig


@dataclasses.dataclass
class EndpointAnnotation:
  """ Holds the endpoint details added with the #endpoint() decorator. """
  method: str
  path: HttpPath

  def __pretty__(self) -> str:
    return f'@endpoint("{self.method} {self.path}")'


@dataclasses.dataclass
class EndpointArgsAnnotation:
  """ Holds additional argument details. """
  args: dict[str, 'ArgumentDescription']


@dataclasses.dataclass
class ServiceAnnotation:
  """ Annotation for service classes. """

  name: str


def authentication(config: AuthenticationConfig | type[AuthenticationConfig]) -> t.Callable[[T], T]:
  """
  Decorator for classes that describe an API service to specify one or more types of authentication usable with all
  of the endpoints. Multiple authentication methods can be specified per service or endpoint.
  """

  if isinstance(config, type):
    config = config()

  def _decorator(obj: T) -> T:
    annotation = AuthenticationAnnotation(t.cast(AuthenticationConfig, config))
    add_annotation(obj, AuthenticationAnnotation, annotation, front=True)
    return obj

  return _decorator


def endpoint(http: str) -> t.Callable[[T], T]:
  """
  Decorator for methods on a service class to mark them as endpoints to be served/accessible via the specified
  HTTP method and parametrized path.
  """

  method, path = http.split(maxsplit=2)

  def _decorator(obj: T) -> T:
    add_annotation(obj, EndpointAnnotation, EndpointAnnotation(method, HttpPath(path)), front=True)
    return obj

  return _decorator


def endpoint_args(**args: 'ArgumentDescription') -> t.Callable[[T], T]:
  """ Decorator for endpoint methods to attach additional #Param information to an endpoint argument. """

  def _decorator(obj: T) -> T:
    add_annotation(obj, EndpointArgsAnnotation, EndpointArgsAnnotation(args), front=True)
    return obj

  return _decorator


def service(name: str) -> t.Callable[[T], T]:
  """ Decorator for service classes. """

  def _decorator(obj: T) -> T:
    add_annotation(obj, ServiceAnnotation, ServiceAnnotation(name), front=True)
    return obj

  return _decorator
