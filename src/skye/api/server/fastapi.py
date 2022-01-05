
import databind.json
import logging
import sys
import textwrap
import typing as t
from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from skye.api.runtime.exceptions import ServiceException, UnauthorizedError
from ..runtime import HandlerMixin, Service, Endpoint, AuthenticationMethod

logger = logging.getLogger(__name__)
HandlerFactory = t.Callable[[], HandlerMixin] | t.Type[HandlerMixin]


async def extract_authorization(
  authentication_methods: t.Iterable[AuthenticationMethod],
  request: Request,
) -> t.Any | None:
  for method in authentication_methods:
    return await method.extract_credentials(request)


class SkyeAPIRouter(APIRouter):
  """ Router for service implementations defined with the Skye runtime API. """

  def __init__(self, handler_factory: HandlerFactory, service_config: Service | None = None, **kwargs: t.Any) -> None:
    super().__init__(**kwargs)
    self._handler_factory = handler_factory
    self._service_config = handler_factory.service_config if isinstance(handler_factory, type) else service_config
    if self._service_config is None:
      raise RuntimeError('missing service_config when factory function is provided')
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
        path=endpoint.path,
        endpoint=self._get_endpoint_handler(endpoint),
        methods=[endpoint.method],
        name=endpoint.name,
      )

  def _get_endpoint_handler(self, endpoint: Endpoint):
    """ Internal. Constructs a handler for the given endpoint. """

    # TODO (@nrosenstein): De-serialize parameters using databind.json instead of relying on the default?

    authorization_methods = self._service_config.authentication_methods + endpoint.authentication_methods

    async def _dispatcher(request: Request, **kwargs):
      authorization = await extract_authorization(authorization_methods, request)
      handler = self._handler_factory()
      try:
        response = await handler.before_request(request, authorization)
        if response is None:
          # TODO (@nrosenstein): Automatically convert to a response
          response = await getattr(handler, endpoint.name)(**kwargs)
          response = self._serialize_value(response, endpoint.return_type)
        response = await handler.after_request(response) or response
      except ServiceException as exc:
        response = self._handle_exception(exc)
      except:
        logger.exception('Uncaught exception in %s', endpoint.name)
        response = self._handle_exception(ServiceException())

      return response

    # Generate code to to tell FastAPI which parameters this endpoint accepts.
    # TODO (@nrosenstein): support other parameter types (like query/header/cookie).
    args = ', '.join(a.name for a in endpoint.args)
    kwargs = ', '.join(f'{a.name}={a.name}' for a in endpoint.args)
    scope = {'_dispatcher': _dispatcher}
    exec(textwrap.dedent(f'''
      from starlette.requests import Request
      async def _handler(request: Request, {args}):
        return await _dispatcher(request=request, {kwargs})
    '''), scope)
    _handler = scope['_handler']
    _handler.__annotations__.update({a.name: a.type for a in endpoint.args})
    if endpoint.return_type:
      _handler.__annotations__['return'] = endpoint.return_type

    return _handler

  def _handle_exception(self, exc: ServiceException) -> Response:
    status_codes = {
      'UNAUTHORIZED': 403,
      'NOT_FOUND': 404,
      'CONFLICT': 409,
    }
    return JSONResponse(exc.safe_dict(), status_code=status_codes.get(exc.ERROR_CODE, 500))
