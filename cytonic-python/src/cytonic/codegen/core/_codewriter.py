
import contextlib
import typing as t


class CodeWriter:
  """
  A helper class to generate code, with functionality to fan into simultaenously writable sections of the
  file and temporarily increasing the indentation level.
  """

  def __init__(self, indent: str, level: int = 0) -> None:
    self._indent = indent
    self._level = level
    self._lines: list[str | 'CodeWriter'] = []

  def section(self) -> 'CodeWriter':
    section = CodeWriter(self._indent, self._level)
    self._lines.append(section)
    return section

  def flush(self, fp: t.TextIO) -> None:
    for line in self._lines:
      if isinstance(line, CodeWriter):
        line.flush(fp)
      else:
        fp.write(line)
        fp.write('\n')

  @contextlib.contextmanager
  def indented(self, add_level: int = 1) -> t.Iterator[None]:
    self._level += add_level
    try:
      yield
    finally:
      self._level -= add_level

  @property
  def prefix_length(self) -> int:
    return self._level * len(self._indent)

  def writeline(self, text: str) -> None:
    self._lines += (self._level * self._indent + text).splitlines()

  def writelines(self, lines: list[str]) -> None:
    for line in lines:
      self.writeline(line)

  def write(self, text: str) -> None:
    for line in text.splitlines():
      if not line:
        self._lines.append('')
      else:
        self.writeline(line)

  def blank(self, num: int = 1) -> None:
    self._lines += [''] * num
