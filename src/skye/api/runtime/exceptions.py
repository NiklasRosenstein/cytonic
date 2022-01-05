
import dataclasses
import typing as t

T = t.TypeVar('T')


class Safe(t.Generic[T]):
  """ Wrapper for values to indicate that they are "safe" to display to users. """

  def __init__(self, value: T) -> None:
    self._value = value

  def __repr__(self) -> str:
    return f'Safe({self._value!r})'

  def __str__(self) -> str:
    return str(self._value)

  @property
  def value(self) -> T:
    return self._value


class ServiceException(Exception):
  ERROR_CODE: t.ClassVar[str] = 'INTERNAL'
  ERROR_NAME: t.ClassVar[str] = 'Default:Internal'

  def __init__(self, **parameters: object | Safe) -> None:
    self.__parameters = parameters

  def safe_dict(self) -> dict[str, object]:
    result: dict[str, object] = {
      'error_code': self.ERROR_CODE,
      'error_name': self.ERROR_NAME,
      'parameters': {},
    }
    if dataclasses.is_dataclass(self):
      for field in dataclasses.fields(self):
        result['parameters'][field.name] = getattr(self, field.name)
    for key, value in self.__parameters.items():
      if isinstance(key, Safe):
        result['parameters'][key] = value.value
      elif key in self.SAFE_PARAMETERS:
        result['parameters'][key] = value
    return result


class UnauthorizedError(Exception):
  ERROR_CODE = 'UNAUTHORIZED'
  ERROR_NAME = 'Default:Unauthorized'


class NotFoundError(Exception):
  ERROR_CODE = 'NOT_FOUND'
  ERROR_NAME = 'Default:NotFound'


class ConflictError(Exception):
  ERROR_CODE = 'CONFLICT'
  ERROR_NAME = 'Default:Conflict'
