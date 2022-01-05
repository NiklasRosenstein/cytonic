
import dataclasses
import types

from ._authentication import AuthenticationAnnotation, AuthenticationMethod
from ._endpoint import EndpointAnnotation
from ._utils import get_annotation, get_annotations


@dataclasses.dataclass
class Endpoint:
  """ Represents a single endpoint. """

  name: str
  method: str
  path: str
  # args
  # return_type
  authentication_methods: list[AuthenticationMethod]


@dataclasses.dataclass
class Service:
  """ Represents the compiled information about a service from a class definition. """

  authentication_methods: list[AuthenticationMethod]
  endpoints: list[Endpoint]

  @staticmethod
  def from_class(cls: type) -> 'Service':
    service = Service([], [])

    for annotation in get_annotations(cls, AuthenticationAnnotation):
      service.authentication_methods.append(annotation.get())

    for key in dir(cls):
      value = getattr(cls, key)
      if isinstance(value, types.FunctionType) and (annotation := get_annotation(value, EndpointAnnotation)):
        service.endpoints.append(Endpoint(
          name=key,
          method=annotation.method,
          path=annotation.path,
          # args
          # return_type
          authentication_methods=[ann.get() for ann in get_annotations(value, AuthenticationAnnotation)],
        ))

    return service
