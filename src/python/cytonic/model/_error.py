
import dataclasses

from ._type import FieldConfig


@dataclasses.dataclass
class ErrorConfig:

  #: The error code of the base type.
  error_code: str

  #: The fields or parameters for the error.
  fields: dict[str, FieldConfig] | None = None

  docs: str | None = None
