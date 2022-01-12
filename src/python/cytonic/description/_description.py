
import dataclasses
import inspect
import types
import typing as t

from nr.util.annotations import get_annotation, get_annotations
from nr.util.singleton import NotSet

from cytonic.model import AuthenticationConfig, HttpPath, ParamKind
from cytonic.runtime import Credentials
from ._decorators import AuthenticationAnnotation, EndpointAnnotation, EndpointArgsAnnotation, ServiceAnnotation


@dataclasses.dataclass
class ArgumentDescription:
  """ Represents additional information for a parameter. """

  #: The kind of HTTP parameter.
  kind: ParamKind

  #: The default value of the parameter. This is used if the parameter is not supplied. This is
  #: not supported for path parameters/
  default: t.Any | NotSet = NotSet.Value

  #: The parameter alias as it will need to be specified in the HTTP request. This needs to be used
  #: if the HTTP parameter name clashes with a Python keyword, or simply if the parameter name in code
  #: should be different from the HTTP parameter name.
  alias: str | None = None

  #: The type of the parameter. This is not usually set explicitly, but automatically determined from the
  #: type hint that the parameter is related to when using #Service.from_class().
  type: t.Any = None


@dataclasses.dataclass
class EndpointDescription:
  """ Represents a single endpoint. """

  #: The name of the endpoint, derived from the function name of which
  name: str
  method: str
  path: HttpPath
  args: dict[str, ArgumentDescription]
  return_type: t.Any | None
  authentication_methods: list[AuthenticationConfig]
  async_: bool


@dataclasses.dataclass
class ServiceDescription:
  """ Represents the compiled information about a service from a class definition. """

  name: str
  authentication_methods: list[AuthenticationConfig]
  endpoints: list[EndpointDescription]

  def update(self, other: 'ServiceDescription') -> 'ServiceDescription':
    authentication_methods = {
      **{type(a): a for a in self.authentication_methods},
      **{type(a): a for a in other.authentication_methods},
    }
    endpoints = {
      **{e.name: e for e in self.endpoints},
      **{e.name: e for e in other.endpoints},
    }
    return ServiceDescription(
      other.name,
      list(authentication_methods.values()),
      list(endpoints.values()),
    )

  @staticmethod
  def from_class(cls: type, include_bases: bool = False) -> 'ServiceDescription':
    service_annotation = get_annotation(cls, ServiceAnnotation)
    service = ServiceDescription(service_annotation.name if service_annotation else cls.__name__, [], [])

    for auth_annotation in get_annotations(cls, AuthenticationAnnotation):
      service.authentication_methods.append(auth_annotation.config)

    for key in dir(cls):
      value = getattr(cls, key)
      if isinstance(value, types.FunctionType) and (endpoint := get_annotation(value, EndpointAnnotation)):
        args, return_type = _parse_type_hints(
          type_hints=t.get_type_hints(value),
          signature=inspect.signature(value),
          endpoint=endpoint,
          args_annotation=get_annotation(value, EndpointArgsAnnotation) or EndpointArgsAnnotation({}),
          endpoint_name=f'{cls.__name__}.{key}'
        )
        authentication_methods = [ann.config for ann in get_annotations(value, AuthenticationAnnotation)]
        if authentication_methods and 'auth' not in args:
          raise ValueError(f'missing "auth" parameter in endpoint {endpoint.__pretty__()}')
        service.endpoints.append(EndpointDescription(
          name=key,
          method=endpoint.method,
          path=endpoint.path,
          args=args,
          return_type=return_type,
          authentication_methods=authentication_methods,
          async_=inspect.iscoroutinefunction(value),
        ))

    if include_bases:
      for base in reversed(cls.__bases__):
        service = ServiceDescription.from_class(base).update(service)

    return service


def _parse_type_hints(
  type_hints: dict[str, t.Any],
  signature: inspect.Signature,
  endpoint: EndpointAnnotation,
  args_annotation: EndpointArgsAnnotation,
  endpoint_name: str,
) -> tuple[dict[str, ArgumentDescription], t.Any]:
  """ Parses evaluated type hints to a list of arguments and the return type. """

  args = {}

  unknown_args = args_annotation.args.keys() - type_hints.keys()
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
    param = args_annotation.args.get(k)
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
    param = args_annotation.args.get(k)
    if param:
      args[k] = ArgumentDescription(param.kind, _get_default(k), param.alias, v)
    elif k in endpoint.path.parameters:
      args[k] = ArgumentDescription(ParamKind.path, _get_default(k), None, v)
    else:
      delayed[k] = v

  body_args = {k for k, v in args.items() if v.kind == ParamKind.body}
  if len(body_args) > 1:
    raise ValueError(f'multiple body arguments found in {endpoint.__pretty__()}: {body_args}')

  # Now automatically assign parameter kinds for the ones that are not explicitly defined.
  for k, v in delayed.items():
    if v == Credentials:
      kind = ParamKind.auth
    elif not body_args and endpoint.method not in ('GET', 'HEAD', 'OPTIONS'):
      kind = ParamKind.body
      body_args.add(k)
    else:
      kind = ParamKind.query
    sig_default = signature.parameters[k].default
    if sig_default is inspect._empty:
      sig_default = NotSet.Value
    args[k] = ArgumentDescription(kind, sig_default, None, v)

  return_ = type_hints.get('return')
  if return_ is type(None):
    return_ = None

  return args, return_


def cookie(default: t.Any | NotSet = NotSet.Value, alias: str | None = None) -> ArgumentDescription:
  return ArgumentDescription(ParamKind.cookie, default, alias)


def header(default: t.Any | NotSet = NotSet.Value, alias: str | None = None) -> ArgumentDescription:
  return ArgumentDescription(ParamKind.header, default, alias)


def path(default: t.Any | NotSet = NotSet.Value, alias: str | None = None) -> ArgumentDescription:
  return ArgumentDescription(ParamKind.path, default, alias)


def query(default: t.Any | NotSet = NotSet.Value, alias: str | None = None) -> ArgumentDescription:
  return ArgumentDescription(ParamKind.query, default, alias)
