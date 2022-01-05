
import dataclasses
import types
import typing as t

from ._authentication import AuthenticationAnnotation, AuthenticationMethod
from ._endpoint import EndpointAnnotation
from ._utils import get_annotation, get_annotations


@dataclasses.dataclass
class Argument:
  """ Represents an endpoint argument. """

  name: str
  kind: t.Literal['cookie', 'header', 'query', 'path', 'body']
  type: t.Any


@dataclasses.dataclass
class Endpoint:
  """ Represents a single endpoint. """

  name: str
  method: str
  path: str
  args: list[Argument]
  return_type: t.Any | None
  authentication_methods: list[AuthenticationMethod]


@dataclasses.dataclass
class Service:
  """ Represents the compiled information about a service from a class definition. """

  authentication_methods: list[AuthenticationMethod]
  endpoints: list[Endpoint]

  def update(self, other: 'Service') -> 'Service':
    authentication_methods = {
      **{type(a): a for a in self.authentication_methods},
      **{type(a): a for a in other.authentication_methods},
    }
    endpoints = {
      **{e.name: e for e in self.endpoints},
      **{e.name: e for e in other.endpoints},
    }
    return Service(
      list(authentication_methods.values()),
      list(endpoints.values()),
    )

  @staticmethod
  def from_class(cls: type, include_bases: bool = False) -> 'Service':
    service = Service([], [])

    for annotation in get_annotations(cls, AuthenticationAnnotation):
      service.authentication_methods.append(annotation.get())

    for key in dir(cls):
      value = getattr(cls, key)
      if isinstance(value, types.FunctionType) and (annotation := get_annotation(value, EndpointAnnotation)):
        type_hints = t.get_type_hints(value)
        service.endpoints.append(Endpoint(
          name=key,
          method=annotation.method,
          path=annotation.path,
          args=[Argument(k, 'path' if f'{{{k}}}' in annotation.path else 'body', v) for k, v in type_hints.items() if k != 'return'],
          return_type=type_hints.get('return'),
          authentication_methods=[ann.get() for ann in get_annotations(value, AuthenticationAnnotation)],
        ))

    if include_bases:
      for base in reversed(cls.__bases__):
        service = Service.from_class(base).update(service)

    return service
