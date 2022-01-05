
import dataclasses
import inspect
import types
import typing as t

from nr.pylang.utils.singletons import NotSet

from ._authentication import AuthenticationAnnotation, AuthenticationMethod, Credentials
from ._endpoint import EndpointAnnotation, Param, ParamKind, Path
from ._utils import Annotateable, add_annotation, get_annotation, get_annotations

T = t.TypeVar('T')


@dataclasses.dataclass
class ServiceAnnotation:
  """ Annotation for service classes. """
  name: str


def service(name: str) -> t.Callable[[T], T]:
  """ Decorator for service classes. """

  def _decorator(obj: T) -> T:
    add_annotation(
      t.cast(Annotateable, obj),
      ServiceAnnotation,
      ServiceAnnotation(name),
      front=True,
    )
    return obj

  return _decorator


@dataclasses.dataclass
class Argument(Param):
  """ Represents an endpoint argument. """

  type: t.Any


@dataclasses.dataclass
class Endpoint:
  """ Represents a single endpoint. """

  name: str
  method: str
  path: Path
  args: dict[str, Argument]
  return_type: t.Any | None
  authentication_methods: list[AuthenticationMethod]


@dataclasses.dataclass
class Service:
  """ Represents the compiled information about a service from a class definition. """

  name: str
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
      other.name,
      list(authentication_methods.values()),
      list(endpoints.values()),
    )

  @staticmethod
  def from_class(cls: type, include_bases: bool = False) -> 'Service':
    service_annotation = get_annotation(cls, ServiceAnnotation)
    service = Service(service_annotation.name if service_annotation else cls.__name__, [], [])

    for auth_annotation in get_annotations(cls, AuthenticationAnnotation):
      service.authentication_methods.append(auth_annotation.get())

    for key in dir(cls):
      value = getattr(cls, key)
      if isinstance(value, types.FunctionType) and (endpoint := get_annotation(value, EndpointAnnotation)):
        endpoint_name = f'{cls.__name__}.{key}'
        args, return_type = parse_type_hints(t.get_type_hints(value), inspect.signature(value), endpoint, endpoint_name)
        authentication_methods = [ann.get() for ann in get_annotations(value, AuthenticationAnnotation)]
        if authentication_methods and 'auth' not in args:
          raise ValueError(f'missing "auth" parameter in endpoint {endpoint.__pretty__()}')
        service.endpoints.append(Endpoint(
          name=key,
          method=endpoint.method,
          path=endpoint.path,
          args=args,
          return_type=return_type,
          authentication_methods=authentication_methods,
        ))

    if include_bases:
      for base in reversed(cls.__bases__):
        service = Service.from_class(base).update(service)

    return service


def parse_type_hints(
  type_hints: dict[str, t.Any],
  signature: inspect.Signature,
  endpoint: EndpointAnnotation,
  endpoint_name: str,
) -> tuple[dict[str, Argument], t.Any]:
  """ Parses evaluated type hints to a list of arguments and the return type. """

  args = {}

  unknown_args = endpoint.args.keys() - type_hints.keys()
  if unknown_args:
    raise ValueError(
      f'some args in {endpoint.__pretty__()} annotation for {endpoint_name!r} are not accepted by '
      f'the endpoint argument list: {unknown_args}'
    )

  unknown_path_params = endpoint.path.parameters.keys() - type_hints.keys()
  if unknown_path_params:
    raise ValueError(
      f'some path parameters in the {endpoint.__pretty__()} annotation for {endpoint_name!r} are not accepted '
      f'by the endpoint argument list: {unknown_path_params}'
    )

  def _get_default(k) -> t.Any | NotSet:
    param = endpoint.args.get(k)
    if param and param.default is not NotSet.Value:
      return param.default
    value = signature.parameters[k].default
    if value is not inspect._empty:
      return value
    return NotSet.Value

  delayed: dict[str, t.Any] = {}
  for k, v in type_hints.items():
    if k == 'return':
      continue
    param = endpoint.args.get(k)
    if param:
      args[k] = Argument(param.kind, _get_default(k), param.name, v)
    elif k in endpoint.path.parameters:
      args[k] = Argument(ParamKind.path, _get_default(k), None, v)
    else:
      delayed[k] = v

  body_args = {k for k, v in args.items() if v.kind == ParamKind.body}
  if len(body_args) > 1:
    raise ValueError(f'multiple body arguments found in {endpoint.__pretty__()}: {body_args}')

  # Now automatically assign parameter kinds for the ones that are not explicitly defined.
  for k, v in delayed.items():
    if v == Credentials:
      kind = ParamKind.auth
    elif not body_args:
      kind = ParamKind.body
      body_args.add(k)
    else:
      kind = ParamKind.query
    sig_default = signature.parameters[k].default
    if sig_default is inspect._empty:
      sig_default = NotSet.Value
    args[k] = Argument(kind, sig_default, None, v)

  return_ = type_hints.get('return')
  if return_ is type(None):
    return_ = None

  print(args)
  return args, return_
