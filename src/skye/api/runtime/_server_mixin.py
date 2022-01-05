
import dataclasses
import typing as t

from starlette.requests import Request
from ._service import Service

T = t.TypeVar('T')


@dataclasses.dataclass
class Context:
  request: Request
  authorization: t.Any | None

  def get_credentials(self, of_type: t.Type[T]) -> T:
    if isinstance(self.authorization, of_type):
      return self.authorization
    raise RuntimeError(f'{type(self.authorization).__name__} is not of type {of_type.__name__}')


class ServerMixin:
  """ Mixin to be added for service implementations. """

  service_config: t.ClassVar[Service]

  def __init__(self, context: Context) -> None:
    self._context = context

  def __init_subclass__(cls) -> None:
    cls.service_config = Service.from_class(cls, include_bases=True)

  @property
  def context(self) -> Request:
    return self._context
