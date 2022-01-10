
""" Mount Cytonic service implementations in a FastAPI app. """

import base64
import logging
import textwrap
import typing as t

import databind.json
import fastapi
from nr.util.safearg import Safe
from nr.util.singleton import NotSet
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from cytonic.description import EndpointDescription, ServiceDescription
from cytonic.model import ParamKind, AuthenticationConfig, OAuth2Bearer, BasicAuth, NoAuth
from cytonic.runtime import Credentials, ServiceException, UnauthorizedError

logger = logging.getLogger(__name__)

# TODO (@nrosenstein): If FastAPI request parameter validation fails, it returns some JSON that indicates
#   the error details. We should try to catch this error payload and wrap it into a ServiceException to
#   ensure that a consistent error format is returned to clients.


async def _get_oauth2_credentials(request: Request, config: OAuth2Bearer) -> Credentials:
  header_value: str | None = request.headers.get(config.header_name or 'Authorization')
  if not header_value:
    raise UnauthorizedError(Safe('missing Authorization header'))
  scheme, header_value, *_ = header_value.split(maxsplit=2) + ['']
  if scheme.lower() != 'bearer':
    raise UnauthorizedError(Safe('bad Authorization scheme'))
  return Credentials.of_bearer_token(config, header_value)


async def _get_basic_auth_credentials(request: Request, config: BasicAuth) -> Credentials:
  header_value: str | None = request.headers.get("Authorization")
  if not header_value:
    raise UnauthorizedError(Safe('missing Authorization header'))
  scheme, header_value, *_ = header_value.split(maxsplit=2) + ['']
  if scheme.lower() != 'basic':
    raise UnauthorizedError(Safe('bad Authorization scheme'))
  try:
    decoded = base64.b64decode(header_value).decode('ascii')
    if decoded.count(':') != 1:
      raise ValueError
  except (ValueError, UnicodeDecodeError):
    raise UnauthorizedError(Safe('bad Authorization header value'))
  username, password = decoded.split(':')
  return Credentials.of_basic_auth(config, username, password)


async def _get_credentials(
  authentication_methods: t.Sequence[AuthenticationConfig],
  request: Request,
) -> Credentials:
  """ Helper function to extract the first matching of a list of authentication methods."""

  unauthorized_errors = []
  for method in authentication_methods:
    try:
      if isinstance(method, OAuth2Bearer):
        return await _get_oauth2_credentials(request, method)
      elif isinstance(method, BasicAuth):
        return await _get_basic_auth_credentials(request, method)
      elif isinstance(method, NoAuth):
        return Credentials.empty(method)
      else:
        raise RuntimeError(f'unsupported authorization method: {method!r}')
    except UnauthorizedError as exc:
      unauthorized_errors.append(exc)

  if len(unauthorized_errors) == 1:
    raise unauthorized_errors[0]

  raise UnauthorizedError(
    Safe('no valid authentication method satisfied'),
    authentication_errors=Safe([str(x) for x in unauthorized_errors]),
  )


class CytonicServiceRouter(fastapi.APIRouter):
  """ Router for service implementations defined with the Skye runtime API. """

  def __init__(self, handler: t.Any, service_description: ServiceDescription | None = None, **kwargs: t.Any) -> None:
    super().__init__(**kwargs)
    if service_description is None:
      service_description = ServiceDescription.from_class(type(handler), True)
    self._handler = handler
    self._service_description = service_description
    self._init_router()

  def _serialize_value(self, value: t.Any, type_: t.Any | None) -> t.Any:
    """ Internal. Serializes *value* to the specified type using databind. """

    if type_ not in (None, type(None)):
      return databind.json.dump(value, type_)
    return value

  def _init_router(self) -> None:
    """ Internal. Initializes the API routes based on the service configuration."""

    for endpoint in self._service_description.endpoints:
      self.add_api_route(
        path=str(endpoint.path),
        endpoint=self._get_endpoint_handler(endpoint),
        methods=[endpoint.method],
        name=endpoint.name,
      )

  def _get_endpoint_handler(self, endpoint: EndpointDescription) -> t.Callable:
    """ Internal. Constructs a handler for the given endpoint. """

    # TODO (@nrosenstein): De-serialize parameters using databind.json instead of relying on the default?

    authentication_methods = self._service_description.authentication_methods + endpoint.authentication_methods

    async def _dispatcher(request: Request, **kwargs):
      try:
        if authentication_methods:
          kwargs['auth'] = await _get_credentials(authentication_methods, request)
        response = getattr(self._handler, endpoint.name)(**kwargs)
        # TODO (@nrosenstein): Better support for non-async endpoints.
        if endpoint.async_:
          response = await response
        response = self._serialize_value(response, endpoint.return_type)
      except ServiceException as exc:
        response = self._handle_exception(exc)
      except:
        logger.exception('Uncaught exception in %s', endpoint.name)
        response = self._handle_exception(ServiceException())

      return response

    # Generate code to to tell FastAPI which parameters this endpoint accepts.
    args = ', '.join(a for a in endpoint.args)
    kwargs = ', '.join(f'{a}={a}' for a in endpoint.args)
    scope = {'_dispatcher': _dispatcher}

    exec(textwrap.dedent(f'''
      from starlette.requests import Request
      async def _handler(request: Request, *, {args}):
        return await _dispatcher(request=request, {kwargs})
    '''), scope)
    _handler = scope['_handler']
    _handler.__annotations__.update({k: a.type for k, a in endpoint.args.items()})
    if endpoint.return_type:
      _handler.__annotations__['return'] = endpoint.return_type

    defaults = {}
    for arg_name, arg in endpoint.args.items():
      default = ... if arg.default is NotSet.Value else arg.default
      if arg.kind == ParamKind.body:
        value = fastapi.Body(default, alias=arg.alias)
      elif arg.kind == ParamKind.cookie:
        value = fastapi.Cookie(default, alias=arg.alias)
      elif arg.kind == ParamKind.query:
        value = fastapi.Query(default, alias=arg.alias)
      elif arg.kind == ParamKind.header:
        value = fastapi.Header(default, alias=arg.alias)
      elif arg.kind == ParamKind.auth:
        value = fastapi.Depends(lambda: None)  # Overwritten inside the handler
      else:
        continue
      defaults[arg_name] = value
    _handler.__kwdefaults__ = defaults  # type: ignore

    return _handler

  def _handle_exception(self, exc: ServiceException) -> Response:
    status_codes = {
      'UNAUTHORIZED': 403,
      'NOT_FOUND': 404,
      'CONFLICT': 409,
      'ILLEGAL_ARGUMENT': 400,
    }
    return JSONResponse(exc.safe_dict(), status_code=status_codes.get(exc.ERROR_CODE, 500))
