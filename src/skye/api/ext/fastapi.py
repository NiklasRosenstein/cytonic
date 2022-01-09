
import logging
import textwrap
import typing as t

import databind.json
import fastapi
from nr.pylang.utils.singletons import NotSet
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ..runtime.auth import AuthenticationMethod, Credentials
from ..runtime.endpoint import ParamKind
from ..runtime.exceptions import ServiceException, UnauthorizedError
from ..runtime.service import Endpoint, Service

logger = logging.getLogger(__name__)

# TODO (@nrosenstein): If FastAPI request parameter validation fails, it returns some JSON that indicates
#   the error details. We should try to catch this error payload and wrap it into a ServiceException to
#   ensure that a consistent error format is returned to clients.


async def extract_authorization(
  authentication_methods: t.Iterable[AuthenticationMethod],
  request: Request,
) -> Credentials:
  if not authentication_methods:
    return Credentials(None, None)
  unauthorized_errors = []
  for method in authentication_methods:
    try:
      return await method.extract_credentials(request)
    except UnauthorizedError as exc:
      unauthorized_errors.append(exc)
  if len(unauthorized_errors) == 1:
    raise unauthorized_errors[0]
  raise UnauthorizedError('no valid authentication method satisfied', authentication_errors=[str(x) for x in unauthorized_errors])


class SkyeAPIServiceRouter(fastapi.APIRouter):
  """ Router for service implementations defined with the Skye runtime API. """

  def __init__(self, handler: t.Any, service_config: Service | None = None, **kwargs: t.Any) -> None:
    super().__init__(**kwargs)
    if service_config is None:
      service_config = Service.from_class(type(handler), True)
    self._handler = handler
    self._service_config = service_config
    self._init_router()

  def _serialize_value(self, value: t.Any, type_: t.Any | None) -> t.Any:
    """ Internal. Serializes *value* to the specified type using databind. """

    if type_ not in (None, type(None)):
      return databind.json.dump(value, type_)
    return value

  def _init_router(self) -> None:
    """ Internal. Initializes the API routes based on the service configuration."""

    for endpoint in self._service_config.endpoints:
      self.add_api_route(
        path=str(endpoint.path),
        endpoint=self._get_endpoint_handler(endpoint),
        methods=[endpoint.method],
        name=endpoint.name,
      )

  def _get_endpoint_handler(self, endpoint: Endpoint):
    """ Internal. Constructs a handler for the given endpoint. """

    # TODO (@nrosenstein): De-serialize parameters using databind.json instead of relying on the default?

    # TODO (@nrosenstein): Support non-async handlers?

    authorization_methods = self._service_config.authentication_methods + endpoint.authentication_methods

    async def _dispatcher(request: Request, **kwargs):
      try:
        response = await getattr(self._handler, endpoint.name)(**kwargs)
        response = self._serialize_value(response, endpoint.return_type)
      except ServiceException as exc:
        response = self._handle_exception(exc)
      except:
        logger.exception('Uncaught exception in %s', endpoint.name)
        response = self._handle_exception(ServiceException())

      return response

    async def _get_credentials(request: Request) -> Credentials:
      return await extract_authorization(authorization_methods, request)

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
        value = fastapi.Body(default, alias=arg.name)
      elif arg.kind == ParamKind.cookie:
        value = fastapi.Cookie(default, alias=arg.name)
      elif arg.kind == ParamKind.query:
        value = fastapi.Query(default, alias=arg.name)
      elif arg.kind == ParamKind.header:
        value = fastapi.Header(default, alias=arg.name)
      elif arg.kind == ParamKind.auth:
        value = fastapi.Depends(_get_credentials)
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
    }
    return JSONResponse(exc.safe_dict(), status_code=status_codes.get(exc.ERROR_CODE, 500))
