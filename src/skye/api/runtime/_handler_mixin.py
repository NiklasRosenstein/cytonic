
import typing as t

from starlette.requests import Request
from starlette.responses import Response
from ._authentication import Authorization
from ._service import Service

T = t.TypeVar('T')


class HandlerMixin:
  """ Mixin to be added for service implementations. """

  service_config: t.ClassVar[Service]

  def __init_subclass__(cls) -> None:
    cls.service_config = Service.from_class(cls, include_bases=True)

  async def before_request(self, request: Request, authorization: Authorization | None) -> Response | None:
    pass

  async def after_request(self, response: Response) -> Response | None:
    pass

  @property
  def context(self) -> Request:
    return self._context
