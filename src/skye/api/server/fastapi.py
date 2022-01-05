
import textwrap
import typing as t
import databind.json
from fastapi import APIRouter
from starlette.requests import Request
from ..runtime import Context, ServerMixin, Endpoint, AuthenticationMethod

ServerMixinFactory = t.Callable[[Context], ServerMixin] | t.Type[ServerMixin]


async def extract_authorization(
  authentication_methods: t.Iterable[AuthenticationMethod],
  request: Request,
) -> t.Any | None:
  for method in authentication_methods:
    return await method.extract_credentials(request)


class SkyeAPIRouter(APIRouter):
  """ Router for service implementations defined with the Skye runtime API. """

  def __init__(self, server: ServerMixin, **kwargs: t.Any) -> None:
    super().__init__(**kwargs)
    self._server = server
    self._service_config = server.service_config
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
      context = Context(
        request=request,
        authorization=await extract_authorization(authorization_methods, request)
      )
      server = self._server(context)
      result = await getattr(server, endpoint.name)(**kwargs)
      return self._serialize_value(result, endpoint.return_type)

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
