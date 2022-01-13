
import dataclasses
import typing as t

from nr.util.safearg import Arg


class ServiceException(Exception):
  """
  Base class for JSON encodable exceptions. If a subclass is a dataclass, its fields are always considered safe
  for consumption and serialization to clients. Otherwise, parameters passed to the #ServiceException constructor
  need to be explicitly marked #Safe or #Unsafe.
  """

  ERROR_CODE: t.ClassVar[str] = 'INTERNAL'
  ERROR_NAME: t.ClassVar[str] = 'Default:Internal'

  def __init__(self, message: Arg | None = None, **parameters: Arg) -> None:
    if message is not None and not isinstance(message, Arg):
      raise TypeError(f'message must be nr.util.safearg.Arg instance')
    if message is not None:
      parameters['message'] = message
    self.__parameters = parameters

  def safe_dict(self) -> dict[str, object]:
    parameters: dict[str, object] = {}
    result: dict[str, object] = {
      'error_code': self.ERROR_CODE,
      'error_name': self.ERROR_NAME,
      'parameters': parameters,
    }
    if dataclasses.is_dataclass(self):
      for field in dataclasses.fields(self):
        parameters[field.name] = getattr(self, field.name)
    for key, value in self.__parameters.items():
      if value.is_safe():
        parameters[key] = value.value
    return result


class UnauthorizedError(ServiceException):
  ERROR_CODE = 'UNAUTHORIZED'
  ERROR_NAME = 'Default:Unauthorized'


class NotFoundError(ServiceException):
  ERROR_CODE = 'NOT_FOUND'
  ERROR_NAME = 'Default:NotFound'


class ConflictError(ServiceException):
  ERROR_CODE = 'CONFLICT'
  ERROR_NAME = 'Default:Conflict'


class IllegalArgumentError(ServiceException):
  ERROR_CODE = 'ILLEGAL_ARGUMENT'
  ERROR_NAME = 'Default:IllegalArgument'
