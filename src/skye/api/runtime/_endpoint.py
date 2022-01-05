
import dataclasses
import typing as t

from ._utils import add_annotation, T_Annotateable


@dataclasses.dataclass
class EndpointAnnotation:
  """ Holds the endpoint details added with the #endpoint() decorator. """
  method: str
  path: str


def endpoint(http: str) -> t.Callable[[T_Annotateable], T_Annotateable]:
  """
  Decorator for methods on a service class to mark them as endpoints to be served/accessible via the specified
  HTTP method and parametrized path.
  """

  method, path = http.split(maxsplit=2)

  def _decorator(obj: T_Annotateable) -> T_Annotateable:
    add_annotation(obj, EndpointAnnotation, EndpointAnnotation(method, path), front=True)
    return obj

  return _decorator
