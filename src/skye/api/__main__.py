
""" CLI to generate code from YAML API definitions. """

import argparse
from pathlib import Path
from ._model._project import Project


def get_argument_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser()
  parser.add_argument(
    'files',
    nargs='+',
    metavar='FILE',
    help='One or more YAML files to generate Python API bindings for.',
  )
  parser.add_argument(
    '--prefix',
    metavar='PATH',
    help='Generate files starting from the specified directory (defaults to cwd).'
  )
  parser.add_argument(
    '--async',
    action='store_true',
    help='Generate async API bindings.',
  )
  parser.add_argument(
    '--sync', '--blocking',
    action='store_true',
    help='Generate blocking API bindings.',
  )
  parser.add_argument(
    '--package',
    metavar='PACKAGE_NAME',
    help='Generate the code in a package (directory format) with the specified name.',
  )
  parser.add_argument(
    '--module',
    metavar='MODULE_NAME',
    help='Generate the code in a single module with the specified name.',
  )
  return parser


def main():
  args = get_argument_parser().parse_args()
  project = Project()
  for filename in map(Path, args.files):
    print(filename, filename.stem)
    project.add(filename.stem, filename)
  print(project._modules)

if __name__ == '__main__':
  main()
