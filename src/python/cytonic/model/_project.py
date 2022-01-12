
import dataclasses
import typing as t
from pathlib import Path

from ._module import ModuleConfig, load_module


@dataclasses.dataclass
class TypeLocator:
  module_name: str
  module: ModuleConfig
  type_name: str


@dataclasses.dataclass
class Project:

  modules: dict[str, ModuleConfig] = dataclasses.field(default_factory=dict)

  TypeLocator: t.ClassVar = TypeLocator

  @classmethod
  def from_files(cls, files: list[str | Path]) -> 'Project':
    project = cls()
    for filename in map(Path, files):
      project.add(filename.stem, filename)
    return project

  def add(self, module_name: str, config: ModuleConfig | dict[str, t.Any] | str | Path) -> None:
    if not isinstance(config, ModuleConfig):
      config = load_module(config)
    if module_name in self.modules:
      raise ValueError(f'module {module_name!r} already in project')
    self.modules[module_name] = config

  def find_type(self, type_name: str) -> TypeLocator | None:
    for module_name, module in self.modules.items():
      if type_name in module.types:
        return TypeLocator(module_name, module, type_name)
    return None
