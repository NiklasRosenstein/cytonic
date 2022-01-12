
import argparse
import dataclasses
import textwrap
from pathlib import Path

from cytonic.model import ErrorConfig, ModuleConfig, Project, TypeConfig
from ._util import CodeWriter, FileOpener


@dataclasses.dataclass
class TypescriptGenerator:

  project: Project
  prefix: str | Path
  stdout: bool
  indent: str = '  '
  line_length: int = 120

  def write(self) -> None:
    opener = FileOpener.with_indicator(self.stdout, '//')
    for module_name, module in self.project.modules.items():
      filename = Path(self.prefix) / (module_name + '.ts')
      with opener.open(filename) as fp:
        writer = CodeWriter(fp, self.indent)
        self._write_module(writer, module_name, module)

  def _write_docs(self, writer: CodeWriter, docs: str | None, num_blanks: int = 0) -> None:
    if not docs:
      return
    writer.writelines([
      '/**',
      *(f' * {l}' for l in textwrap.wrap(docs, self.line_length - writer.prefix_length - 3)),
      ' */',
    ])
    writer.blank(num_blanks)

  def _write_module(self, writer: CodeWriter, module_name: str, module: ModuleConfig) -> None:
    writer.writelines([
      'import Cytonic from "@cytonic/runtime";',
      ''
    ])

    for type_name, type_ in module.types.items():
      self._write_type(writer, type_name, type_)
      writer.blank()

    for error_name, type_ in module.errors.items():
      self._write_error(writer, error_name, type_)
      writer.blank()

    self._write_service(writer, module, True)
    writer.blank()
    self._write_service(writer, module, False)

  def _write_type(self, writer: CodeWriter, type_name: str, type_: TypeConfig) -> None:
    self._write_docs(writer, type_.docs, 0)
    type_.validate()
    writer.writeline(f'export {"enum" if type_.values is not None else "interface"} {type_name} {{')
    with writer.indented():
      for field_name, field in type_.fields.items():
        # TODO: Translate field type
        writer.writeline(f'{field_name}: {field.type};')
    writer.writeline('}')

  def _write_error(self, writer: CodeWriter, error_name: str, error: ErrorConfig) -> None:
    self._write_docs(writer, error.docs, 0)
    writer.writeline(f'export class {error_name}Error extends Cytonic.ServiceException {{')  # TODO
    with writer.indented():
      if error.fields:
        #writer.writeline('public constructor(')
        #with writer.indented():
        lines = []
        for field_name, field in error.fields.items():
          # TODO: Translate type
          lines.append(f'public {field_name}: {field.type}')
        #lines[-1] = lines[-1][:-1] + ')'
        writer.writeline('public constructor(' + ', '.join(lines) + ') { super(); }')
    # TODO: Write logic to serialize/deserialize the error
    writer.writeline('}')

  def _write_service(self, writer: CodeWriter, module: ModuleConfig, async_: bool) -> None:
    self._write_docs(writer, module.docs, 0)
    writer.writeline(f'export interface {module.name}Service{"Async" if async_ else "Blocking"} {{')
    with writer.indented():
      for endpoint_name, endpoint in module.endpoints.items():
        # TODO: Convert snake case to camelCase?
        line = f'{endpoint_name}('
        if module.auth is not None or endpoint.auth is not None:
          line += 'auth: Cytonic.Credentials, '
        for arg_name, arg in (endpoint.args or {}).items():
          # TODO: Translate type
          line += f'{arg_name}: {arg.type}, '
        if line.endswith(', '):
          line = line[:-2]
        line += '): '
        # TODO: Translate type
        return_type = endpoint.return_
        if async_ and return_type:
          return_type = f'Promise<{return_type}>'
        line += (return_type or 'null') + ';'
        writer.writeline(line)
    writer.writeline('}')


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
