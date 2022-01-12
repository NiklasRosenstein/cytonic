
import abc
import contextlib
import dataclasses
import re
import sys
import typing as t
from pathlib import Path

from nr.util.generic import T


class CodeWriter:
  """
  Helper class to generate code, automatically indenting lines per the current indentation level.
  """

  def __init__(self, fp: t.TextIO, indent: str) -> None:
    self._fp = fp
    self._level = 0
    self._indent = indent

  @property
  def prefix_length(self) -> int:
    return self._level * len(self._indent)

  @contextlib.contextmanager
  def indented(self, add_level: int = 1) -> t.Iterable[None]:
    self._level += add_level
    try:
      yield
    finally:
      self._level -= add_level

  def writeline(self, text: str) -> None:
    text = text.rstrip()
    self._fp.write(self._indent * self._level)
    self._fp.write(text)
    if not text.endswith('\n'):
      self._fp.write('\n')

  def writelines(self, lines: list[str]) -> None:
    for line in lines:
      self.writeline(line)

  def write(self, text: str) -> None:
    for line in text.splitlines():
      if not line:
        self._fp.write('\n')
      else:
        self.writeline(line)

  def blank(self, num: int = 1) -> None:
    self._fp.write('\n' * num)


@dataclasses.dataclass
class FileOpener:

  stdout: bool = False
  open_stdout: t.Optional[t.Callable[[str], t.Any]] = None
  open_fs: t.Optional[t.Callable[[str, t.TextIO], t.Any]] = None

  @contextlib.contextmanager
  def open(self, filename: Path | str) -> t.Generator[t.TextIO, None, None]:
    if self.stdout:
      if self.open_stdout:
        self.open_stdout(filename)
      yield sys.stdout
    else:
      filename = Path(filename)
      filename.parent.mkdir(parents=True, exist_ok=True)
      with filename.open('w') as fp:
        if self.open_fs:
          self.open_fs(str(filename), fp)
        yield fp

  @staticmethod
  def with_indicator(stdout: bool, stdout_indicator: str, fs_indicator: str = 'Writing ') -> None:
    return FileOpener(
      stdout,
      lambda fn: print(f'\n{stdout_indicator} {fn}'),
      lambda fn, fp: print(f'{fs_indicator} {fn}'),
    )


class TypeConverter(t.Generic[T]):
  """
  A helper class to convert type strings as defined in the YAML specification to other forms of representation.
  The type parameter *T* is the data type which represents the type in its new form.
  """

  def convert_type_string(self, type_string: str) -> T:
    match = re.match(r'(\w+)(?:\[(.+)\])?', type_string)
    if not match:
      raise ValueError(f'what\'s dis? {type_string!r}')

    type_name, parameters_string = match.groups()
    parameters = None if parameters_string is None else [x.strip() for x in parameters_string.split(',')]

    return self.create_type(type_name, parameters)

  @abc.abstractmethod
  def create_type(self, type_name: str, parameters: list[str]) -> T:
    ...
