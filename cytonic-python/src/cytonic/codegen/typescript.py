
import argparse
import dataclasses
import functools
import itertools
import textwrap
import typing as t
from pathlib import Path

import databind.json
from nr.util.generic import T

from cytonic.model import ErrorConfig, ModuleConfig, Project, TypeConfig, AuthenticationConfig
from .core._codewriter import CodeWriter
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

  def visit_type(self, rendered_type: str, type_locator: Project.TypeLocator | None) -> str:
    if type_locator:
      self.imports.add(TypeScriptImport('./' + type_locator.module_name, type_locator.type_name))
    elif rendered_type.startswith('Cytonic.'):
      rendered_type = rendered_type.rpartition('.')[-1]
      self.imports.add(TypeScriptImport('@cytonic/runtime', rendered_type))
    return rendered_type


@dataclasses.dataclass
class TypeScriptTypeToDescriptorConverter(DefaultTypeConverter):

  type_converter: TypeScriptTypeConverter

  TYPE_TEMPLATES = {
    'any': 'new AnyType()',
    'string': 'new StringType()',
    'integer': 'new IntegerType()',
    'double': 'new DoubleType()',
    'boolean': 'new BooleanType()',
    'datetime': 'new DatetimeType()',
    'decimal': 'new DecimalType()',
    'list': 'new ListType(?)',
    'set': 'new SetType(?)',
    'map': 'new MapType(?)',
    'optional': 'new OptionalType(?)',
  }

  def visit_type(self, rendered_type: str, type_locator: Project.TypeLocator | None) -> str:
    if type_locator:
      # Make sure that type descriptor for the custom type is imported.
      type_name = f'{rendered_type}_TYPE'
      self.type_converter.visit_type(type_name, Project.TypeLocator(type_locator.module_name, type_locator.module, type_name))
      return type_name
    if rendered_type.startswith('new'):
      # Make sure that the type descriptor is imported.
      index = rendered_type.index('(')
      self.type_converter.visit_type('Cytonic.' + rendered_type[4:index].strip(), None)
    return super().visit_type(rendered_type, type_locator)


@dataclasses.dataclass
class TypescriptGenerator:

  project: Project
  prefix: str | Path
  stdout: bool
  indent: str = '  '
  line_length: int = 120

  def __post_init__(self) -> None:
    self._type_converter = t.cast(TypeScriptTypeConverter, None)
    self._type_descriptor = t.cast(TypeScriptTypeToDescriptorConverter, None)

  def write(self) -> None:
    opener = FileOpener.with_indicator(self.stdout, '//')
    for module_name, module in self.project.modules.items():
      filename = Path(self.prefix) / (module_name + '.ts')
      self._module = module
      self._type_converter = TypeScriptTypeConverter(self.project)
      self._type_descriptor = TypeScriptTypeToDescriptorConverter(self.project, self._type_converter)
      self._writer = CodeWriter(self.indent)
      imports = self._writer.section()
      self._writer.blank()
      self._write_module(module_name, module)

      for group, type_names in itertools.groupby(sorted(self._type_converter.imports), lambda i: i.module):
        if group == f'./{module_name}': continue
        imports.writeline(f'import {{ {", ".join(x.type for x in type_names)} }} from "{group}";')

      with opener.open(filename) as fp:
        self._writer.flush(fp)

  def _get_field_type(self, type_string: str) -> str:
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

    for error_name, error_type in module.errors.items():
      self._write_error(error_name, error_type)
      self._writer.blank()

    self._write_service(module, True)
    self._writer.blank()
    self._write_service(module, False)
    self._writer.blank()
    self._write_service_definition(module)

  def _write_type(self, type_name: str, type_: TypeConfig) -> None:
    self._write_docs(type_.docs, 0)
    type_.validate()
    self._writer.writeline(f'export {"enum" if type_.values is not None else "interface"} {type_name} {{')
    with self._writer.indented():
      for field_name, field in (type_.fields or {}).items():
        self._writer.writeline(f'{field_name}: {self._get_field_type(field.type)};')
    self._writer.writeline('}')
    self._writer.blank()
    self._type_converter.visit_type('Cytonic.StructType', None)
    self._writer.writeline(f'export const {type_name}_TYPE = new StructType<{type_name}>({type_name!r}, {{')
    with self._writer.indented():
      for field_name, field in (type_.fields or {}).items():
        self._writer.writeline(f'{field_name}: {{ type: {self._type_descriptor.convert_type_string(field.type)} }},')
    self._writer.writeline('});')

  def _write_error(self, error_name: str, error: ErrorConfig) -> None:
    self._write_docs(error.docs, 0)
    base_class = self._type_converter.visit_type('Cytonic.ServiceException', None)
    self._writer.writeline(f'export interface {error_name}Error extends {base_class} {{')  # TODO
    with self._writer.indented():
      self._writer.writeline(f"error_name: '{self._module.name}:{error_name}'")
      if error.fields:
        self._writer.writeline('parameters: {')
        with self._writer.indented():
          for field_name, field in error.fields.items():
            self._writer.writeline(f'{field_name}: {self._get_field_type(field.type)},')
        self._writer.writeline('}')
    # TODO: Write logic to serialize/deserialize the error
    self._writer.writeline('}')

  def _write_service(self, module: ModuleConfig, async_: bool) -> None:
    type_name = f'{module.name}Service{"Async" if async_ else "Blocking"}'
    self._write_docs(module.docs, 0)
    self._writer.writeline(f'export interface {type_name} {{')
    with self._writer.indented():
      for endpoint_name, endpoint in module.endpoints.items():
        line = f'{endpoint_name}('
        if module.auth is not None or endpoint.auth is not None:
          credentials_type = self._type_converter.visit_type('Cytonic.Credentials', None)
          line += f'auth: {credentials_type}, '
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
    if async_:
      self._writer.blank()
      self._writer.writeline(f'export namespace {type_name} {{')
      with self._writer.indented():
        self._type_converter.visit_type('Cytonic.ClientConfig', None)
        self._writer.writeline(f'export function client(config: ClientConfig): {type_name} {{')
        with self._writer.indented():
          self._type_converter.visit_type('Cytonic.createAsyncClient', None)
          self._writer.writeline(f'return createAsyncClient<{type_name}>({module.name}Service_TYPE, config);')
        self._writer.writeline('}')
      self._writer.writeline('}')

  def _write_service_definition(self, module: ModuleConfig) -> None:
    self._type_converter.visit_type('Cytonic.Service', None)
    self._writer.writeline(f'const {module.name}Service_TYPE: Service = {{')
    with self._writer.indented():
      self._write_auth(module.auth)
      self._writer.writeline('endpoints: {')
      with self._writer.indented():
        for endpoint_name, endpoint in module.endpoints.items():
          endpoint.resolve_arg_kinds()
          self._writer.writeline(f'{endpoint_name}: {{')
          with self._writer.indented():
            self._writer.writeline(f'method: {endpoint.http.method!r},')
            self._writer.writeline(f'path: {endpoint.http.path!r},')
            self._write_auth(endpoint.auth)
            if endpoint.return_ is not None:
              self._writer.writeline(f'return: {self._type_descriptor.convert_type_string(endpoint.return_)},')
            if endpoint.args is not None:
              self._writer.writeline('args: {')
              with self._writer.indented():
                for arg_name, arg in endpoint.args.items():
                  self._writer.writeline(f'{arg_name}: {{')
                  with self._writer.indented():
                    assert arg.kind is not None, 'should have been set by EndpointConfig.resolve_arg_kinds()'
                    self._type_converter.visit_type('Cytonic.ParamKind', None)
                    self._writer.writeline(f'kind: ParamKind.{arg.kind.name},')
                    self._writer.writeline(f'type: {self._type_descriptor.convert_type_string(arg.type)},')
                  self._writer.writeline('},')
              self._writer.writeline('},')
              self._writer.writeline(f'args_ordering: {list(endpoint.args)!r},')
          self._writer.writeline('},')
      self._writer.writeline('},')
    self._writer.writeline('};')

  def _write_auth(self, auth: AuthenticationConfig | None) -> None:
    if auth is not None:
      auth_json = databind.json.dumps(auth, AuthenticationConfig)  # type: ignore
      self._writer.writeline(f'auth: {auth_json},')


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
