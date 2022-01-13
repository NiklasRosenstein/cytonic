
import argparse
import dataclasses
import functools
import itertools
import textwrap
import typing as t
from pathlib import Path

from nr.util.generic import T

from cytonic.model import ErrorConfig, ModuleConfig, Project, TypeConfig
from ._codewriter import CodeWriter
from ._util import FileOpener, DefaultTypeConverter


@dataclasses.dataclass(frozen=True)
@functools.total_ordering
class TypeScriptImport:
  module: str
  type: str

  def __lt__(self, other: 'TypeScriptImport') -> bool:
    return f'{self.module}.{self.type}' < f'{other.module}.{other.type}'


@dataclasses.dataclass
class TypeScriptTypeConverter(DefaultTypeConverter):

  TYPE_TEMPLATES = {
    'any': 'any',
    'string': 'string',
    'integer': 'Cytonic.Integer',
    'double': 'Cytonic.Double',
    'boolean': 'boolean',
    'datetime': 'Date',
    'decimal': 'Cytonic.Decimal',
    'list': '?[]',
    'set': 'Set<?>',
    'map': 'Map<?, ?>',
    'optional': '? | undefined',
  }

  def __post_init__(self) -> None:
    super().__post_init__()
    self.imports = set[TypeScriptImport]()

  def visit_type(self, rendered_type: str, type_locator: Project.TypeLocator | None) -> None:
    if type_locator:
      self.imports.add(TypeScriptImport('./' + type_locator.module_name, type_locator.type_name))
    elif rendered_type.startswith('Cytonic.'):
      rendered_type = rendered_type.rpartition('.')[-1]
      self.imports.add(TypeScriptImport('@cytonic/runtime', rendered_type))
    return rendered_type


@dataclasses.dataclass
class TypescriptGenerator:

  project: Project
  prefix: str | Path
  stdout: bool
  indent: str = '  '
  line_length: int = 120

  def __post_init__(self) -> None:
    self._type_converter = t.cast(TypeScriptTypeConverter, None)

  def write(self) -> None:
    opener = FileOpener.with_indicator(self.stdout, '//')
    for module_name, module in self.project.modules.items():
      filename = Path(self.prefix) / (module_name + '.ts')
      self._type_converter = TypeScriptTypeConverter(self.project)
      self._writer = CodeWriter(self.indent)
      imports = self._writer.section()
      self._writer.blank()
      self._write_module(module_name, module)

      for group, type_names in itertools.groupby(sorted(self._type_converter.imports), lambda i: i.module):
        if group == f'./{module_name}': continue
        imports.writeline(f'import {{ {", ".join(x.type for x in type_names)} }} from "{group}";')

      with opener.open(filename) as fp:
        self._writer.flush(fp)

  def _get_field_type(self, type_string: str) -> None:
    return self._type_converter.convert_type_string(type_string)

  def _write_docs(self, docs: str | None, num_blanks: int = 0) -> None:
    if not docs:
      return
    self._writer.writelines([
      '/**',
      *(f' * {l}' for l in textwrap.wrap(docs, self.line_length - self._writer.prefix_length - 3)),
      ' */',
    ])
    self._writer.blank(num_blanks)

  def _write_module(self, module_name: str, module: ModuleConfig) -> None:
    for type_name, type_ in module.types.items():
      self._write_type(type_name, type_)
      self._writer.blank()

    for error_name, type_ in module.errors.items():
      self._write_error(error_name, type_)
      self._writer.blank()

    self._write_service(module, True)
    self._writer.blank()
    self._write_service(module, False)

  def _write_type(self, type_name: str, type_: TypeConfig) -> None:
    self._write_docs(type_.docs, 0)
    type_.validate()
    self._writer.writeline(f'export {"enum" if type_.values is not None else "interface"} {type_name} {{')
    with self._writer.indented():
      for field_name, field in type_.fields.items():
        self._writer.writeline(f'{field_name}: {self._get_field_type(field.type)};')
    self._writer.writeline('}')

  def _write_error(self, error_name: str, error: ErrorConfig) -> None:
    self._write_docs(error.docs, 0)
    base_class = self._type_converter.visit_type('Cytonic.ServiceException', None)
    self._writer.writeline(f'export class {error_name}Error extends {base_class} {{')  # TODO
    with self._writer.indented():
      if error.fields:
        lines = []
        for field_name, field in error.fields.items():
          lines.append(f'public {field_name}: {self._get_field_type(field.type)}')
        self._writer.writeline('public constructor(' + ', '.join(lines) + ') { super(); }')
    # TODO: Write logic to serialize/deserialize the error
    self._writer.writeline('}')

  def _write_service(self, module: ModuleConfig, async_: bool) -> None:
    self._write_docs(module.docs, 0)
    self._writer.writeline(f'export interface {module.name}Service{"Async" if async_ else "Blocking"} {{')
    with self._writer.indented():
      for endpoint_name, endpoint in module.endpoints.items():
        line = f'{endpoint_name}('
        if module.auth is not None or endpoint.auth is not None:
          credentials_type = self._type_converter.visit_type('Cytonic.Credentials', None)
          line += f'auth: {credentials_type}, '
          self._type_converter.visit_type('Cytonic.Credentials', None)
        for arg_name, arg in (endpoint.args or {}).items():
          line += f'{arg_name}: {self._get_field_type(arg.type)}, '
        if line.endswith(', '):
          line = line[:-2]
        line += '): '
        return_type = self._get_field_type(endpoint.return_) if endpoint.return_ else None
        if async_:
          return_type = f'Promise<{return_type}>' if return_type else 'Promise<void>'
        line += (return_type or 'null') + ';'
        self._writer.writeline(line)
    self._writer.writeline('}')


def get_argument_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser()
  parser.add_argument(
    'files',
    nargs='+',
    metavar='FILE',
    help='One or more YAML files to generate TypeScript API bindings for.',
  )
  parser.add_argument(
    '--prefix',
    metavar='PATH',
    help='The path to write the generated files to.',
    required=True,
  )
  parser.add_argument(
    '--stdout',
    action='store_true',
    help='Write the generated code to stdout insteda.',
  )
  return parser


def main():
  parser = get_argument_parser()
  args = parser.parse_args()

  project = Project.from_files(args.files)
  TypescriptGenerator(project, args.prefix, args.stdout).write()


if __name__ == "__main__":
  main()
